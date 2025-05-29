'''
Read Data from JK_PB1A16S10P and many other newer JK BMS over BLE and publish on a MQTT Server 

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>

NO COMMERCIAL USE !!

Copyright 2025 Z.TOe toedci@gmail.com
------------------------------------------------------------------------------------------------------------------------
If you do any modification to this python script please SHARE with me, thank you!!!!
------------------------------------------------------------------------------------------------------------------------
'''
import sys
import threading
import asyncio
from bleak import BleakClient, BleakScanner,BleakError
from bleak.exc import BleakDBusError
from threading import Lock
from cursor import *
from registers import *
import time
import json
import paho.mqtt.client as paho
from datetime import datetime
import warnings
import struct
import os
import platform
import concurrent.futures
import itertools
import pickle

# Version
VERSION = "2.2.1"

MQTTIP ="192.168.1.11"
MQTTPORT = 1883
topic_prefix = "JK"
mqttClient = paho.Client


RETRY_ATTEMPTS = 15
RETRY_DELAY = 1  # seconds
TIMEOUT_RESPONSE = 10
SHORT_FRAME_LIMIT = 20
SLEEP = 300
WATCHDOG_TIMEOUT = SLEEP*3 # Maximum time allowed for scanning & connecting & sleeping (seconds)
WRITE_TIMEOUT = 5  # Timeout in seconds

MQTT = True
OUTPUT = True
jsonStr = ""
QUIET = True #Only print important information



# BLE things
DEVICE_NAMES = ["290120255005-01","JK_PB1A16S10P-02", "JK_PB1A16S10P-03"] #It is very important to get the names correct
DEVICE_NAMES_LAST = [] #Keep track of which devices have been processed in the current run
#SERVICE_UUID = "ffe0"
SERVICE_UUID = "0000FFE0-0000-1000-8000-00805f9b34fb"
#CHAR_UUID = "ffe1"
CHAR_UUID = "0000FFE1-0000-1000-8000-00805f9b34fb"
MIN_FRAME_SIZE = 300
MAX_FRAME_SIZE = 320
CMD_HEADER = bytes([0xAA, 0x55, 0x90, 0xEB])
CMD_TYPE_DEVICE_INFO = 0x97  # 0x03: Device Information
CMD_TYPE_CELL_INFO = 0x96  # 0x02: Cell Information
CMD_TYPE_SETTINGS = 0x95  # 0x01: Settings


stop_searching = False
# ble_buffer = bytearray(MAX_FRAME_SIZE)
# ble_buffer_index = 0
capturing = False
waiting_for_device_info = False
waiting_for_cell_info = False
thread_lock = Lock()
short_frame_count = 0
last_response = bytearray()  # Store the last valid response
cursor_chars = "\/|-"
indx = 0

# Messages
GET_DEVICE_INFO = bytearray([0xaa, 0x55, 0x90, 0xeb, 0x97, 0x00, 0xdf, 0x52, 0x88, 0x67, 0x9d, 0x0a, 0x09, 0x6b, 0x9a, 0xf6, 0x70, 0x9a, 0x17, 0xfd])
GET_CELL_INFO =   bytearray([0xaa, 0x55, 0x90, 0xeb, 0x96, 0x00, 0x79, 0x62, 0x96, 0xed, 0xe3, 0xd0, 0x82, 0xa1, 0x9b, 0x5b, 0x3c, 0x9c, 0x4b, 0x5d])

last_activity_time = time.time()
notification_queue = None  # Global queue for notifications


def log(color=f"{RESET}",owner="0",process="", message="",**kwargs):
    #------------------------------------------------------------------------------------------
    if not QUIET: print(f"{color}[{owner}]{RESET}{process}: {message}",**kwargs)
#------------------------------------------------------------------------------------------

def calculate_crc(data):
    #------------------------------------------------------------------------------------------
    return sum(data) & 0xFF
#------------------------------------------------------------------------------------------

def connectMqtt():
    # ---------------------------------------------------------------------------------------
    global MQTT, mqttClient

    if MQTT:
        # Initialise MQTT if configured
        clientid = "my" + topic_prefix

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # Use API versioning correctly
            mqttClient = paho.Client(client_id=clientid)#, callback_api_version=paho.CallbackAPIVersion.VERSION1)

        # if config.mqtt.username != "":
        #     mqttClient.tls_set()  # <--- even without arguments
        #     mqttClient.username_pw_set(username="", password="")

        # intopic = config.mqtt.topic_prefix+"/set_register"  # todo deye5k ins config this is what coming in
        # mqttClient.on_message = on_mqtt_message
        try:
            mqttClient.connect(MQTTIP, MQTTPORT)
        except:
            log("","PI4","MQTT","can't connect to server!!")
            return -1
        #mqttClient.subscribe(intopic)
        mqttClient.loop_start()  # start the loopmqttClient.loop_start() #start the loop
        log("","PI4","MQTT",f"connected to server {MQTTIP}")
        return mqttClient
# --connectMqtt-------------------------------------------------------------------------------------------------------

def parse_JK_celldata(raw_data, devicename):
    #---------------------------------------------------------------------------------------------
    global jsonStr, DEVICE_NAMES_LAST, last_activity_time
    parsed_data = {}

    # Add date and time as the first two items
    parsed_data["date"] = datetime.now().strftime("%Y-%m-%d")
    parsed_data["time"] = datetime.now().strftime("%H:%M:%S")

    #alarm_data = {}  # Dictionary to store alarm flags separately

    for pos, name, fmt, coeff, unit in JKCellInfoRegisters:
        size = struct.calcsize(fmt)
        if pos + size <= len(raw_data):
            value = struct.unpack_from(fmt, raw_data, pos)[0] * coeff
            if pos == 0x0040:  
                value = bin(value).count('1')  # Count number of bits set
            if pos == 0x008C:  
                value = f"{value:032b}"  # Convert to a 32-bit binary string

            if pos == 0x00A0:
                # Store alarm flags under "Alarm" sub-item
                for i, alarm_name in enumerate(alarm_flags):
                    #alarm_data[alarm_name] = 1 if (value & (1 << i)) else 0
                    parsed_data[alarm_name] = 1 if (value & (1 << i)) else 0
            else:
                parsed_data[name] = round(value, 3) if isinstance(value, float) else value

    # Add alarm flags as a sub-dictionary
    # if alarm_data:
    #     parsed_data["Alarm"] = alarm_data
    last_activity_time = time.time() #Update that something has happened
    jsonStr = json.dumps(parsed_data, ensure_ascii=False, indent=4)
    if OUTPUT: print(jsonStr)
    if devicename not in DEVICE_NAMES_LAST: #If the processed device isnt processed then add it to the processed list.
        DEVICE_NAMES_LAST.append(devicename)
    if sorted(DEVICE_NAMES_LAST) == sorted(DEVICE_NAMES): #If all devices are processed then clear out the list so that it can restart
        DEVICE_NAMES_LAST = []
    if MQTT:
        try:
            mqttClient.publish((topic_prefix + "/" + devicename), jsonStr)
        except:
            log("",devicename,"PARSER","MQTT can't publish!!")
            return -1

    return parsed_data
#-------------------------------------------------------------------------------------------------

def parse_cell_info(device_name,data):
    #---------------------------------------------------------------------------------------------
    """Parsing Cell Info Frame (0x02) based on JK-BMS specification"""
    log("",device_name, "PARSER", "Cell Info Frame...")

    try:
        # Extract the frame counter (Position 5)
        frame_counter = data[5]
        log("",device_name,"PARSER", f"Frame Counter: {frame_counter}")
        
        # Extract enabled cells bitmask (Positions 70-73)BIT[n] ist 1 und zeigt damit an, dass die Batterie vorhanden ist.
        enabled_cells = int.from_bytes(data[70:74], byteorder='little')
        enabled_cells = bin(enabled_cells).count('1')
        log("",device_name,"PARSER", f"Enabled CellNr: {enabled_cells}")

        parsed_result = parse_JK_celldata(data[6:],device_name)
        # for key, value in parsed_result.items():
        #     if OUTPUT:
        #         print(f"[{LBLUE}{device_name}{RESET}] {key.ljust(15)}: {value}")
        return parsed_result

    except Exception as e:
        log("",device_name,"PARSER", f"Error parsing Cell Info Frame: {e}")
        return None
#-------------------------------------------------------------------------------------------------

def parse_device_info(device_name, data):
    # ---------------------------------------------------------------------------------------
    data_bytes= data[6:]
    device_info = {}

    for offset, name, fmt, length, unit in JKDeviceInfoRegisters:
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, data_bytes, offset)[0]
        
        if fmt.endswith('s'):
            value = value.rstrip(b'\x00').decode('utf-8', errors='ignore')
            value = ''.join(c for c in value if c.isprintable())  # Remove any control characters

        device_info[name] = value

    log("",device_name, "PARSER","Device Info")
    jsonStr = json.dumps(device_info, ensure_ascii=False, indent=4)
    # Convert the JSON string back into a dictionary
    device_info_dict = json.loads(jsonStr)

    # New item to add at the beginning
    new_item = {"Device": device_name}

    # Add the new item at the beginning of the dictionary
    device_info_dict = {**new_item, **device_info_dict}

    if OUTPUT: print(jsonStr)
    
    return device_info
# ---------------------------------------------------------------------------------------
def save_Serializable_globals():
    global DEVICE_NAMES_LAST
    with open('serializable_globals.pkl', 'wb') as f:
        pickle.dump(DEVICE_NAMES_LAST, f) #Save the current processed list past a script restart
# ---------------------------------------------------------------------------------------
def restart_script():
# ---------------------------------------------------------------------------------------
    """Forcefully restart the script if it hangs."""
    log("","MAIN","WATCHDOG", "No activity detected! Restarting script...")
    save_Serializable_globals()
    if "autostart" in sys.argv:
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        os.execv(sys.executable, ['python'] + sys.argv + ['autostart'])
# ---------------------------------------------------------------------------------------

def watchdog_task():
# ---------------------------------------------------------------------------------------
    """Background thread that restarts the script if no activity is detected."""
    global last_activity_time
    while True:
        time.sleep(WATCHDOG_TIMEOUT)
        if time.time() - last_activity_time > WATCHDOG_TIMEOUT:
            restart_script()
# ---------------------------------------------------------------------------------------

async def ble_data_process(client, data, device_name):
    #---------------------------------------------------------------------------------------------
    global indx,capturing,  stop_searching, waiting_for_device_info, waiting_for_cell_info, \
        ble_buffer, ble_buffer_index, last_activity_time
    
    try:
        with thread_lock:
            if not capturing:
                if data[:4] == b'\x55\xAA\xEB\x90':
                    capturing = True
                    ble_buffer = bytearray()
                    log(GREEN, device_name ,"CALLBACK", f"Start detected! {data[:4].hex().upper()} Msg type: {data[4]:02X}")       
                    log("",device_name, "CALLBACK","frame received" , end=" ")
                    last_activity_time = time.time() #Update that something has happened
                else:
                    #log(device_name, f"CALLBACK: Wrong header detected! {data[:4].hex().upper()}")
                    #if OUTPUT: print(end="*",flush=True)
                    sys.stdout.write(f"\r{cursor_chars[indx]}\r")  # Overwrite the same line
                    sys.stdout.flush()
                    indx = (indx + 1) % len(cursor_chars)  #
                    return
                
            try:
                #log(device_name,f"CALLBACK: extend data")
                ble_buffer.extend(data)
            except Exception as e:
                log("",device_name,"CALLBACK", f"Error while processing data: {e}")
                ble_buffer_index = 0
                capturing = False
                return
                
            ble_buffer_index = len(ble_buffer)
            if OUTPUT: print(ble_buffer_index, end="*",flush=True) 

            if ble_buffer_index > MAX_FRAME_SIZE:
                log(RED,device_name,"CALLBACK", f"data size:{ble_buffer_index}")
                ble_buffer_index = 0
                capturing = False
                return


            if MIN_FRAME_SIZE <= len(ble_buffer) <= MAX_FRAME_SIZE:
                # CRC Validation
                crc_calculated = calculate_crc(ble_buffer[:-1])
                crc_received = ble_buffer[-1]
                
                if crc_calculated != crc_received:
                    log("\n",device_name,"CALLBACK", f"{len(ble_buffer)} bytes, CRC Invalid: {crc_calculated:02X} != {crc_received:02X}")
                    ble_buffer_index = 0
                    capturing = False
                    return 0
                else:
                    log("\n",device_name,"CALLBACK", f"{ble_buffer_index} bytes, CRC Valid: {crc_calculated:02X} == {crc_received:02X}")

                message_type = ble_buffer[4]
                log("",device_name,"CALLBACK", f"Call PARSER {message_type:02X} devinfo:{waiting_for_device_info},cellinfo:{waiting_for_cell_info}")
                
                if message_type == 0x3 and waiting_for_device_info:
                    parse_device_info(device_name, ble_buffer)
                    waiting_for_device_info = False
                    log("",device_name,"CALLBACK", "Device Info processed.")
                    
                elif message_type == 0x2 and waiting_for_cell_info:
                    parse_cell_info(device_name, ble_buffer)
                    waiting_for_cell_info = False
                    log("",device_name, "CALLBACK","Cell Info processed. Processing complete.")
                    
                    # Stop notifications when all processing is complete
                    try:
                        await asyncio.wait_for(client.stop_notify(CHAR_UUID), timeout=5)
                    except asyncio.TimeoutError:
                        log("",device_name, "CALLBACK","Timed out waiting to stop notifications.")
                    log("",device_name, "CALLBACK","Stopped notifications.")
                    stop_searching = True  

                else:
                    log("",device_name,"CALLBACK", f"NO PARSER {message_type:02X} / wait devinfo:{waiting_for_device_info}, cellinfo:{waiting_for_cell_info}")
                # Reset buffer
                ble_buffer_index = 0
                capturing = False
    
    except Exception as e:
        log("",device_name,"CALLBACK", f"{e}")
#---------------------------------------------------------------------------------------------


async def data_queue_task(client, data, device_name):
    #---------------------------------------------------------------------------------------------
    # Safely add data to the queue
    global notification_queue
    """Safely add BLE notification data to the queue."""
    #log("",device_name, f"[data_queue_task] Processing: {client}, {data},{device_name}")
    await notification_queue.put((client, data, device_name))
 #---------------------------------------------------------------------------------------------

# async def subscribe_notifications(client, device_name):
#      #---------------------------------------------------------------------------------------------
#     await client.start_notify(CHAR_UUID, lambda sender, data: asyncio.create_task(data_queue_task(client, data, device_name)))
#---------------------------------------------------------------------------------------------

async def processBLE(device):
    # ---------------------------------------------------------------------------------------
    """Handles BLE connection and data processing for a device."""
    global stop_searching, waiting_for_device_info, waiting_for_cell_info, notification_queue
    address = device.address
    device_name = device.name
    stop_searching = False
    attempt = 0

    while attempt < RETRY_ATTEMPTS and not stop_searching:
        try:
            async with BleakClient(address) as client:
                if OUTPUT and client.is_connected: 
                    log("\n",device_name, f"BLE","Connected")
                    
                
                if client.is_connected:
                    # Create a task to handle notifications and queue them
                    await client.start_notify(CHAR_UUID, lambda sender, data: asyncio.create_task(data_queue_task(client, data, device_name)))
                    # Directly assign the function instead of lambda (avoiding async task creation here)
                    #was running so under V1.9
                    #await subscribe_notifications(client, device_name)

                    log("",device_name, f"BLE","Subscribed to notifications")
                else: 
                   log(RED,device_name, f"BLE","NOT Connected 0") 
                   break
                
                if client.is_connected:
                    log(YELLOW,device_name, f"BLE"," Sending Device Info request...wait for response")
                    waiting_for_device_info = True
                    await client.write_gatt_char(CHAR_UUID, GET_DEVICE_INFO)  
                    
                    timeout_counter = 0
                    while waiting_for_device_info and timeout_counter < TIMEOUT_RESPONSE:
                        await asyncio.sleep(1)
                        timeout_counter += 1
                    
                    if waiting_for_device_info and timeout_counter >= TIMEOUT_RESPONSE:
                        log(RED,device_name, f"BLE","Timeout waiting for Device Info response.")
                        try:
                            await asyncio.wait_for(client.stop_notify(CHAR_UUID), timeout=5)
                        except asyncio.TimeoutError:
                            log(RED,device_name, f"BLE","Timed out waiting to stop notifications.")
                        waiting_for_device_info = False
                        break
                
                if client.is_connected:
                    log(YELLOW,device_name, "BLE","Sending Cell Info request...wait for response")
                    waiting_for_cell_info = True
                    await client.write_gatt_char(CHAR_UUID, GET_CELL_INFO)
                    
                    timeout_counter = 0
                    while waiting_for_cell_info and timeout_counter < TIMEOUT_RESPONSE:
                        await asyncio.sleep(1)
                        timeout_counter += 1
                    
                    if waiting_for_cell_info and timeout_counter >= TIMEOUT_RESPONSE:
                        log(RED,device_name, f"BLE","Timeout waiting for Cell Info response.")
                        try:
                            await asyncio.wait_for(client.stop_notify(CHAR_UUID), timeout=5)
                        except asyncio.TimeoutError:
                            log(RED,device_name, f"BLE","Timed out waiting to stop notifications.")
                        waiting_for_cell_info = False
                        break
                
                log("\n"+LYELLOW,device_name, "BLE","Successfully processed the device")
                return
        except Exception:
            if not stop_searching:
                if OUTPUT: print(f"--{attempt + 1}", end="", flush=True)
            if attempt < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY)
            attempt += 1
    
    if not stop_searching and not capturing:
        log("\n"+RED,device_name, "BLE",f"Failed to connect after {RETRY_ATTEMPTS} attempts.")
#---------------------------------------------------------------------------------------------

async def scan_and_process_devices():
    #---------------------------------------------------------------------------------------------
    """Scans for BLE devices and processes them sequentially."""
    global waiting_for_cell_info, waiting_for_device_info, DEVICE_NAMES_LAST, last_activity_time

    scanner = BleakScanner() #Made the scanner a separate object in case it's needed further down in the future.
    try:
        devices = await scanner.discover()
    except BleakDBusError as e:
        if "InProgress" in str(e):
            #log(RED,device_name, "BLE","ERROR scan already in progress. Retrying in 5s...")
            log(RED,"Some device", "BLE","ERROR scan already in progress. Retrying in 5s...") #device_name isnt defined in this scope, so I changed it

            await restart_script() #Restarting the script and thus restarting the BLE module seems to work best for resolving this.
            return False
        else:
            log(RED,"Some device", "BLE","ERROR!") #device_name isnt defined in this scope, so I changed it
            return False
    except BleakError:
        await restart_script() #Restarting the script and thus restarting the BLE module seems to work best for resolving this.
        return False
    try:
        
        found_devices = {d.name: d for d in devices if d.name in DEVICE_NAMES}
        for device_name in DEVICE_NAMES:
            if device_name not in DEVICE_NAMES_LAST: #If its a device that hasnt been processed in the past, then proceed
                device = found_devices.get(device_name)
                if device:
                    log(GREEN,device.name,"BLE","found!\nConnecting ", end="")
                    last_activity_time = time.time()
                    await processBLE(device)
                else:
                    log(RED,device_name,"BLE","Not found.")
    except Exception as e:
        print(e)
        await asyncio.sleep(5)
        return False

    return True
#---------------------------------------------------------------------------------------------
async def notify_process_task():
    #---------------------------------------------------------------------------------------------
    global notification_queue
    log("","MAIN","NOTIFY PROCESSOR",f"Started processing... Loop ID: {id(asyncio.get_running_loop())}")

    while True:
        # Print queue size for debugging
        #print(f"Queue size: {notification_queue.qsize()}")
        
        if not notification_queue.empty():  # Only process if there is data
            client, data, device_name = await notification_queue.get()
            #print(f"[{device_name}] Processing data...")
            await ble_data_process(client, data, device_name)
            notification_queue.task_done()  # Mark the task as done
        else:
            await asyncio.sleep(0.1)  # Sleep for a short time if the queue is empty
#---------------------------------------------------------------------------------------------


async def main():
# ---------------------------------------------------------------------------------------
    global waiting_for_device_info,waiting_for_cell_info,loop,last_activity_time
    global notification_queue, DEVICE_NAMES_LAST

    if "autostart" in sys.argv: #Check if the script has bee automatically restarted and reloads the list of processed devices. This is important to not get stuck on the same devices.
        if os.path.exists('serializable_globals.pkl'):
            with open('serializable_globals.pkl', 'rb') as f:
                DEVICE_NAMES_LAST = pickle.load(f)
    waiting_for_device_info = False
    waiting_for_cell_info = False

    loop = asyncio.get_running_loop()
    notification_queue = asyncio.Queue()  # ✅ Initialize queue first!

    log("","MAIN ","LOOP_ID",f"{id(asyncio.get_running_loop())}")

    # Now start the notification processor
    task = asyncio.create_task(notify_process_task())
    await asyncio.sleep(1)  # Allow notify_process_task to start

    #log("","MAIN",f"Queue size before put: {notification_queue.qsize()}")
    #test queue
    await notification_queue.put(("client0", "data0", "device_name0"))
    #log("","MAIN",f"Queue size after put: {notification_queue.qsize()}")

    if platform.system() == "Linux":
        s=os.system("sudo systemctl restart bluetooth")
    elif platform.system() == "Windows":
        s=os.system("net stop Bluetooth && net start Bluetooth") 
    log(LBLUE,"MAIN","", f"restart bluetooth {s}")
    await asyncio.sleep(5)

    while True:
        last_activity_time = time.time()
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M:%S")
        log(LBLUE,"MAIN","", f"Scanning for devices...{today} {now}")
        
        try:
            # Enforce a watchdog timeout on the scanning & processing loop
            if not waiting_for_cell_info and not waiting_for_device_info:
                result = await asyncio.wait_for(scan_and_process_devices(), timeout=WATCHDOG_TIMEOUT)
            else: 
                log(RED,"MAIN","", "timeout: waiting frames")
            
        except asyncio.TimeoutError:
            log("\n"+RED,"MAIN", "WATCHDOG","Timeout exceeded! Restarting BLE scan...")           
            #break
        
        log(LBLUE,"BLE","", "All devices processed !")
        
        s = int(SLEEP/2)
        if not QUIET: print(end=""+"sleep for "+str(SLEEP)+"sec ")
        for x in range(s):
            #todo mqtt break
            #if is_onmessage: break
            if x % 2 == 0:
                if not QUIET: print(end="--"+str(x*2), flush=True)
            time.sleep(2)
        log("\n"+LBLUE,"BLE","", "Restarting scan..."+today+" "+ now)
        waiting_for_cell_info = False
        waiting_for_device_info = False
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    #os.system("cls" if os.name == "nt" else "clear")
    if OUTPUT: print(f"JK Data Parser v{VERSION}")
    
    if MQTT:
        while not connectMqtt():
            time.sleep(SLEEP)
    else:
        log("","MAIN","MQTT","NO,  >>>> is mqtt = 0  !!!!!!!!")

        # Start watchdog thread
    watchdog_thread = threading.Thread(target=watchdog_task, daemon=True)
    watchdog_thread.start()

    asyncio.run(main())
