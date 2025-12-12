import sys
import time
import serial as s
import serial.tools.list_ports as stl
import pandas as pd
import matplotlib.pyplot as plt
from ogi import sendcmd, connect_OGI3

connect_OGI3()

## Pandas data frame
c = ['time','OD A','OD B','OD C','OD D']
df = pd.DataFrame(columns=c, dtype=float)

# example settings for batch culture
sendcmd('choose OD cal 0')
sendcmd('set exp length 24')
sendcmd('set sample rate 5')
sendcmd('set motor A rpm 3000')
sendcmd('set ambient temp 23')
sendcmd('set temp control target A 37')
sendcmd('set temp control A 1')
sendcmd('start batch culture')

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
