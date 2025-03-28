# JK_BLE_READER
Read Data from JK_PB1A16S10P and many other newer JK BMS over BLE and publish on a MQTT Server
This script reads 3 JK in one round, just put more DEVICE_NAMES for more.

This script tested on a Pi4 wiith bluetooth.

- Set your MQTT IP/Port in script or NO mqtt under "MQTT"
- Set your Blutooth device names under "DEVICE_NAMES"
- Set SLEEP in seconds for polling intervall

MQTT Topic is "JK/devName"
If you tested on an other JK BMS than JK_PB1A16S10P, please let me know
