import sys
import time
import serial as s
import serial.tools.list_ports as stl
import pandas as pd
import matplotlib.pyplot as plt
from ogi import sendcmd, connect_OGI3

## Pandas data frame
c = ['time','OD A','target']
df = pd.DataFrame(columns=c, dtype=float)

# target ODs
targetlow = 0.3
targethigh = 0.8
target = targethigh

# write command
sendcmd('choose OD cal 0')
sendcmd('set temp control target A 30')
sendcmd('set temp control A 1')
sendcmd('set turbidostat controls 0')
sendcmd('set turbidostat control A 1')
sendcmd(f'set turbidostat target A {target}')
sendcmd('start turbidostat')

while(True):
    if (payload := sendcmd('get OD A')):    # read OD A
        data = [float(s) for s in payload.split(',')]
        data.append(target)
        tmp = pd.DataFrame([data], columns=['time', 'OD A', 'target'])
        df = pd.concat([df, tmp], ignore_index=True, verify_integrity=True)

    # Plot data & target
    plt.cla()
    plt.plot(df['time'], df['OD A'], 'x-')
    plt.step(df['time'], df['target'], where='post')

    plt.xlabel('Time (hrs)')
    plt.ylabel('OD')

    plt.legend(['A','target'])

    # Adjust target A
    if (df['OD A'].iloc[-1] > targethigh):
        sendcmd(f'set turbidostat target A {targetlow}')
        target = targetlow
    if (df['OD A'].iloc[-1] < targetlow):
        sendcmd(f'set turbidostat target A {targethigh}')
        target = targethigh

    t = time.time()
    while (time.time() - t < 10):
        plt.pause(1)    # Need this to keep plot interactive
