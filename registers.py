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
#JK-JK_PB1A16S10P Registers 



  # Data Type	Size (Bytes)	Unsigned Format	        Signed Format
    # UINT32	4 bytes	        'I' (unsigned int)	    'i' (signed int)
    # UINT16	2 bytes	        'H' (unsigned short)	'h' (signed short)
    # UINT8	    1 byte	        'B' (unsigned char)	    'b' (signed char)

    # Define JKregisters with their position, name, type, coefficient, unit
JKDeviceInfoRegisters = [
    (0x0000, 'DeviceID', '16s', 1, 'string'),  # 16-byte string
    (0x0010, 'HW Version', '8s', 1, 'string'),   # 8-byte string
    (0x0018, 'SW Version', '8s', 1, 'string'),   # 8-byte string
    (0x0020, 'Runtime', '<H', 1, 'S'),       # Unsigned 16-bit integer
    (0x0024, 'On time', '<H', 1, 'S'),       # Unsigned 16-bit integer
]
JKCellInfoRegisters = [#0x1200
   (0x0000, 'CellV0','H', 0.001,'V'),
   (0x0002, 'CellV1','H', 0.001,'V'),
   (0x0004, 'CellV2','H', 0.001,'V'),
   (0x0006, 'CellV3','H', 0.001,'V'),
   (0x0008, 'CellV4','H', 0.001,'V'),
   (0x0008, 'CellV5','H', 0.001,'V'),
   (0x000A, 'CellV6','H', 0.001,'V'),
   (0x000C, 'CellV7','H', 0.001,'V'),
   (0x000E, 'CellV8','H', 0.001,'V'),
   (0x0010, 'CellV9','H', 0.001,'V'),
   (0x0012,'CellV10','H', 0.001,'V'),
   (0x0014,'CellV11','H', 0.001,'V'),
   (0x0016,'CellV12','H', 0.001,'V'),
   (0x0018,'CellV13','H', 0.001,'V'),
   (0x001A,'CellV14','H', 0.001,'V'),
   (0x001C,'CellV15','H', 0.001,'V'),
   #(0x001E,'CellV16','H', 0.001,'V'),
   #(0x0020,'CellV17','H', 0.001,'V'),
   #(0x0022,'CellV18','H', 0.001,'V'),
   #(0x0024,'CellV19','H', 0.001,'V'),
   #(0x0026,'CellV20','H', 0.001,'V'),
   #(0x0028,'CellV21','H', 0.001,'V'),
   #(0x002C,'CellV22','H', 0.001,'V'),
   #(0x002E,'CellV23','H', 0.001,'V'),
   #(0x0030,'CellV24','H', 0.001,'V'),
   #(0x0032,'CellV25','H', 0.001,'V'),
   #(0x0034,'CellV26','H', 0.001,'V'),
   #(0x0036,'CellV27','H', 0.001,'V'),
   #(0x0038,'CellV28','H', 0.001,'V'),
   #(0x003A,'CellV29','H', 0.001,'V'),
   #(0x003C,'CellV30','H', 0.001,'V'),
   #(0x003E,'CellV31','H', 0.001,'V'),
   (0x0040, 'NrOfCells', 'I', 1,''),
   (0x0044, 'CellVolAve', 'H', 0.001,'V'),
   (0x0046, 'CellVdifMax', 'H', 0.001,'V'),
   (0x0048, 'MaxVolCellNbr', 'B', 1,'-'),
   (0x0049, 'MinVolCellNbr', 'B', 1,'-'),
   (0x004A, 'CellR0','H', 0.001,'?'),
   (0x004C, 'CellR1','H', 0.001,'?'),
   (0x004E, 'CellR2','H', 0.001,'?'),
   (0x0050, 'CellR3','H', 0.001,'?'),
   (0x0052, 'CellR4','H', 0.001,'?'),
   (0x0054, 'CellR5','H', 0.001,'?'),
   (0x0056, 'CellR6','H', 0.001,'?'),
   (0x0058, 'CellR7','H', 0.001,'?'),
   (0x005A, 'CellR8','H', 0.001,'?'),
   (0x005C, 'CellR9','H', 0.001,'?'),
   (0x005E,'CellR10','H', 0.001,'?'),
   (0x0060,'CellR11','H', 0.001,'?'),
   (0x0062,'CellR12','H', 0.001,'?'),
   (0x0064,'CellR13','H', 0.001,'?'),
   (0x0066,'CellR14','H', 0.001,'?'),
   (0x0068,'CellR15','H', 0.001,'?'),
   #(0x006A,'CellR16','H', 0.001,'?'),
   #(0x006C,'CellR17','H', 0.001,'?'),
   #(0x006E,'CellR18','H', 0.001,'?'),
   #(0x0070,'CellR19','H', 0.001,'?'),
   #(0x0072,'CellR20','H', 0.001,'?'),
   #(0x0074,'CellR21','H', 0.001,'?'),
   #(0x0076,'CellR22','H', 0.001,'?'),
   #(0x0078,'CellR23','H', 0.001,'?'),
   #(0x007A,'CellR24','H', 0.001,'?'),
   #(0x007C,'CellR25','H', 0.001,'?'),
   #(0x007E,'CellR26','H', 0.001,'?'),
   #(0x0080,'CellR27','H', 0.001,'?'),
   #(0x0082,'CellR28','H', 0.001,'?'),
   #(0x0084,'CellR29','H', 0.001,'?'),
   #(0x0086,'CellR30','H', 0.001,'?'),
   #(0x0088,'CellR31','H', 0.001,'?'),
   (0x008A,'TempMOS','h', 0.1,'C'),
   #(0x008C,'CellWireResSts','I', 1,'Bits'),
   (0x0090,'BatV','I', 0.001,'V'),
   (0x0094,'BatP','I', 0.001,'W'),
   (0x0098,'BatI','i', 0.001,'A'),
   (0x009C,'Temp1','h', 0.1,'C'),
   (0x009E,'Temp2','h', 0.1,'C'),

   (0x00A0,'Alarm','I',1,'Bits'),
   (0x00A4,'BalanceI','H', 0.001,'A'),
   (0x00A6,'BalanceSts','B',1,'2: discharge; 1: charge; 0: off'),
   (0x00A7,'SOC','B',1,'%'),
   (0x00A8,'CapRemain','i',0.001,'Ah'),
   (0x00AC,'FullChgCap','I',0.001,'Ah'),
   (0x00B0,'CycleCount','I',1,'-'),
   (0x00B4,'CycleCap','I',0.001,'Ah'),
   (0x00B8,'SOH','B',1,'%'),
   (0x00B9,'Precharge','B',1,'-'),
   (0x00BA,'UserAlarm1','H',1,'-'),
   (0x00BC,'RunTime','I',0.00027778,'H'),
   (0x00C0,'Charge','B',1,'-'),
   (0x00C1,'Discharge','B',1,'-'),
   (0x00C2,'UserAlarm2','H',1,'-'),
   (0x00DC, 'BatVCorrect', 'f', 1.0,'-'),
   (0x00E4,'BatV','H',0.01,'V'),
   ]

alarm_flags = [
   "AlarmWireRes",               # bit 0
   "AlarmMosOTP",                # bit 1
   "AlarmCellQuantity",          # bit 2
   "AlarmCurSensorErr",          # bit 3
   "AlarmCellOVP",               # bit 4
   "AlarmBatOVP",                # bit 5
   "AlarmChOCP",                 # bit 6
   "AlarmChSCP",                 # bit 7
   "AlarmChOTP",                 # bit 8
   "AlarmChUTP",                 # bit 9
   "AlarmCPUAuxCommuErr",       # bit 10
   "AlarmCellUVP",               # bit 11
   "AlarmBatUVP",                # bit 12
   "AlarmDchOCP",                # bit 13
   "AlarmDchSCP",                # bit 14
   "AlarmDchOTP",                # bit 15
   "AlarmChargeMOS",             # bit 16
   "AlarmDischargeMOS",          # bit 17
   "GPSDisconnected",            # bit 18
   "Modify PWD. in time",        # bit 19
   "Discharge On Failed",        # bit 20
   "Battery Over Temp Alarm",    # bit 21
   "Temperature sensor anomaly", # bit 22
   "PLCModule anomaly"           # bit 23
   ]
