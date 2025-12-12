# This is a really basic serial monitor. It will establish a connection,
# then prompt for a command and print the response.

import sys
import serial as s
import serial.tools.list_ports as stl

## Serial connection
ser = s.Serial()
ser.port = next(stl.grep('COM*')).name  # Try to automatically find the port - replace with eg 'COM15' if it doesn't work
ser.baudrate = 115200
ser.timeout = 1
ser.dtr = False # Don't reset bioreactor
ser.rts = False

try:
    ser.open()
except:
    print("error, couldn't open port - check connection and that port isn't being used in another process")
    sys.exit()

if ser.isOpen():
    while True:
        ser.write(input("Enter command: ").encode("utf-8"))
        print(ser.read_until("\r").decode("utf-8"))
