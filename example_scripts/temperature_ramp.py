# Start a batch culture @ 30 C until OD = 0.5, then increase temperature 1 C per hr to 37 C.
# Plot OD & temperature.
# Flask A only.

import time
import pandas as pd
import matplotlib.pyplot as plt
from ogi import sendcmd, connect_OGI3

FILENAME = 'temperature_ramp.csv'   # Save data here

INITIAL_TEMPERATURE = 30
TARGET_OD = 0.5    # Start ramping temperature at this OD
FINAL_TEMPERATURE = 37
TEMPERATURE_STEP = 1
TEMPERATURE_DURATION = 3600 # Time in seconds to spend at temperature
current_temperature = INITIAL_TEMPERATURE

connect_OGI3(verbose=True)

# example settings for batch culture
sendcmd('choose OD cal 4')
sendcmd('set exp length 48')
sendcmd('set sample interval 5')
sendcmd('set motor rpm A 4000')
sendcmd('set ambient temp 23')
sendcmd(f'set temp control target A {current_temperature}')
sendcmd('set temp control A 1')
sendcmd('start batch culture')


# Pandas data frame
c = ['time','OD A','Temp A','Target Temp A']
df = pd.DataFrame(columns=c, dtype=float)

# This function takes measurements and updates the plot
def update_plot():
    global df
    if (payload := sendcmd('get OD A')):    # read OD
        # split payload into time and value:
        data = [float(s) for s in payload.split(',')]

        # join to existing dataframe (note that `verify_integrity` prevents adding duplicates)
        tmp = pd.DataFrame([data], columns=['time', 'OD A'])
        df = pd.concat([df, tmp], ignore_index=True, verify_integrity=True)

    if (payload := sendcmd('get temperature A')):    # read temperature
        data = [float(s) for s in payload.split(',')]
        data.append(current_temperature)    # Save current target too

        tmp = pd.DataFrame([data], columns=['time', 'Temp A', 'Target Temp A'])
        df = pd.concat([df, tmp], ignore_index=True, verify_integrity=True)

    # Save data to file
    df.to_csv(FILENAME)

    # Plot data
    fig, ax = plt.subplots(num=0, clear=True)
    ax2 = ax.twinx()
    ax.scatter(df['time'], df['OD A'], 'x-', s=2, c='tab:blue')
    ax2.scatter(df['time'], df['Temp A'], s=2, c='tab:orange')
    ax2.step(df['time'], df['Target Temp A'], where='post', color='tab:green')

    ax.set_xlabel('Time (hrs)')
    ax.set_ylabel('OD')
    ax.set_ylabel(r'Temperature ($\degree$C)')

    fig.legend(['OD A','Temperature A', 'Target temperature'])

    plt.pause(10)    # Runs the GUI loop for 10 s - keeps the plot interactive


# Main flow:
# First measurement
update_plot()

# Take regular measurements until threshold OD
while (df['OD A'][df['OD A'].notna()].iloc[-1] < TARGET_OD):
    update_plot()

# Ramp up temperature
while (current_temperature < FINAL_TEMPERATURE):
    current_temperature = current_temperature + 1
    sendcmd(f'set temp control target A {current_temperature}')    # Increase target temperature

    t = time.time()
    while (time.time() < t + TEMPERATURE_DURATION):     # Take measurements for this long
        update_plot()

# Continue taking measurements
while(True):
    update_plot()
