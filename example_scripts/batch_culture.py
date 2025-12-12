# This example shows how to set basic settings and start a batch culture experiment.
# It will then plot the ODs.

import pandas as pd
import matplotlib.pyplot as plt
from ogi import sendcmd, connect_OGI3

connect_OGI3(verbose=True)

# example settings for batch culture
sendcmd('choose OD cal 0')
sendcmd('set exp length 24')
sendcmd('set sample interval 5')
sendcmd('set motor rpm A 3000')
sendcmd('set ambient temp 23')
sendcmd('set temp control target A 37')
sendcmd('set temp control A 1')
sendcmd('start batch culture')

## Pandas data frame
c = ['time','OD A','OD B','OD C','OD D']
df = pd.DataFrame(columns=c, dtype=float)

while(True):
    for r in ['A', 'B', 'C', 'D']:
        if (payload := sendcmd(f'get OD {r}')):    # read OD
            # split payload into time and value:
            data = [[float(s) for s in payload.split(',')]]

            # join to existing dataframe (note that `verify_integrity` prevents adding duplicates)
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

    plt.pause(10)    # Need this to keep plot interactive
