# This script shows how to plot the ODs of an already running experiment.
# To use, start your experiment before running this script.

import pandas as pd
import matplotlib.pyplot as plt
from ogi import sendcmd, connect_OGI3

connect_OGI3()

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
