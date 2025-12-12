import sys
import time
import serial as s
import serial.tools.list_ports as stl
import pandas as pd
import matplotlib.pyplot as plt


def sendcmd(cmd):
    while(ser.in_waiting):  # there is data in the buffer - print until clear
        print(ser.read(64).decode('utf-8'))

    # ready to send
    ser.write(cmd.encode('utf-8'))

    # wait for response
    while True:
        if ser.in_waiting:
            # read back response
            mystr = ser.read_until('\r').decode('utf-8')

            # check that return message starts with our command
            if (not mystr.startswith(cmd)):
                print(f"error, return message {mystr} does not match command {cmd}")
                return

            # check for error
            if (mystr.find("ERR") != -1):
                print(mystr.rstrip().partition("ERR"))
                return

            # success - return payload
            return mystr.rstrip().partition(cmd)[2]

## Pandas data frame
c = ['time','OD A','OD B','OD C','OD D']
df = pd.DataFrame(columns=c, dtype=float)

## Serial connection
ser = s.Serial()
ser.port = next(stl.grep('COM*')).name  # Try to automatically find the port - replace with eg 'COM15' if it doesn't work
ser.baudrate = 115200
ser.timeout = 1
ser.dtr = False
ser.dtr = False

try:
    ser.open()
except:
    print("error, couldn't open port - check connection and that port isn't being used in another process")
    sys.exit()

if ser.isOpen():
    print('Serial connection established\n')

    # wait for reactor to start
    time.sleep(0.5)

    # write command
    sendcmd('choose OD cal 0')
    sendcmd('set exp length 24')
    sendcmd('set sample rate 5')
    sendcmd('set motor A rpm 3000')
    sendcmd('set ambient temp 23')
    sendcmd('set temp control target A 37')
    sendcmd('set temp control A 1')
    sendcmd('start batch culture')

    # print OD A
    while(True):
        for r in ['A', 'B', 'C', 'D']:
            if (payload := sendcmd(f'get OD {r}')):    # read OD
                data = [[float(s) for s in payload.split(',')]]
                tmp = pd.DataFrame(data, columns=['time', f'OD {r}'])
                df = pd.concat([df, tmp], ignore_index=True, verify_integrity=True)

        # Plot data
        plt.cla()
        plt.plot(df['time'], df['OD A'], 'x-')
        plt.plot(df['time'], df['OD B'], 'x-')
        plt.plot(df['time'], df['OD C'], 'x-')
        plt.plot(df['time'], df['OD D'], 'x-')

        plt.xlabel('Time (hrs)')
        plt.ylabel('OD')

        plt.legend(['A','B','C','D'])

        t = time.time()
        while (time.time() - t < 5 * 60):
            plt.pause(1)    # Need this to keep plot interactive

    ser.close()
