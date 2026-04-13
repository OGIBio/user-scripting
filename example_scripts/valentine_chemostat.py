# Controls the OD in a heart shape.
# Flask A is the bottom side sloping down and up
# Flask B forms the two bumps
#
#
# OD_2 ______ __    __
#            /  \  /  \
# OD_1 ____ /    \/    \
#           \          /
#            \        /
#             \      /
#              \    /
#               \  /
# OD_0 _________ \/
# |---------|     |----|
#   T_DELAY      T_0   +DT
#


import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from ogi import sendcmd, connect_OGI3


# struct of parameters
@dataclass(frozen=True)
class Params:
    OD_0: float = 0.2
    OD_1: float = 1.0
    OD_2: float = 1.4
    DT_HRS: float = 6
    T_DELAY_HRS: float = 1
    SAMPLE_INTERVAL_MINS: float = 5
    FLASK_VOL_ML: float = 15

    @property
    def T_0_HRS(self) -> float:
        return self.T_DELAY_HRS + self.DT_HRS

    @property
    def SAMPLE_INTERVAL_SEC(self) -> float:
        return self.SAMPLE_INTERVAL_MINS * 60


# Update the plot
def update_plot(df, interval):
    fig, ax = plt.subplots(num=0, clear=True)

    ax.set_xlabel("Time (hrs)")
    ax.set_ylabel("OD")

    for f in ["A", "B"]:
        # Plot data
        t = df["Time (hrs)"][df["Reactor"] == f]
        od = df["OD"][df["Reactor"] == f]
        ax.scatter(t, od, label=f"OD {f}")

    ax.legend()

    # Run the GUI loop - keeps the plot interactive
    # This is also how we time retrieving data from the OGI3
    plt.pause(interval)


# Get new ODs and update dataframe
def update_ODs(df: pd.DataFrame) -> pd.DataFrame:
    for f in ["A", "B"]:
        if payload := sendcmd(f"get OD {f}"):  # read OD
            # split payload into time and value:
            data = [float(s) for s in payload.split(",")]

            # join to existing dataframe
            tmp = pd.DataFrame([data], columns=["Time (hrs)", "OD"])
            tmp["Reactor"] = f
            df = pd.concat([df, tmp], ignore_index=True)

    return df


# Send new flow rates to OGI3
def update_flowrates(fA, fB):
    sendcmd(f"set chemostat flowrate A {fA}")
    sendcmd(f"set chemostat flowrate B {fB}")


# Equation for the trace of OD A
def target_A(t, p: Params):
    if p.T_0_HRS - p.DT_HRS < t < p.T_0_HRS:
        return p.OD_0 + (p.OD_0 - p.OD_1) / p.DT_HRS * (t - p.T_0_HRS)
    if p.T_0_HRS < t < p.T_0_HRS + p.DT_HRS:
        return p.OD_0 + (p.OD_1 - p.OD_0) / p.DT_HRS * (t - p.T_0_HRS)

    return p.OD_1


# Equation for the trace of OD B
def target_B(t, p: Params):
    C = 4 * (p.OD_2 - p.OD_1) / p.DT_HRS**2

    if p.T_0_HRS - p.DT_HRS < t < p.T_0_HRS:
        return -C * (t - p.T_0_HRS) * (t - (p.T_0_HRS - p.DT_HRS)) + p.OD_1
    if p.T_0_HRS < t < p.T_0_HRS + p.DT_HRS:
        return -C * (t - p.T_0_HRS) * (t - (p.T_0_HRS + p.DT_HRS)) + p.OD_1

    return p.OD_1


# Store target equations in a dict for easier looping
TARGET_OD = {"A": target_A, "B": target_B}


# Calculates a new flow rate based on current and target OD
def newflowrate(
    current_flowrate, flask_vol_ml, deltaT, current_OD, previous_OD, target_OD
):
    """
    This equation might have a nicer form but the idea is it gets an underlying
    exponential growth rate from the change in OD and the current flowrate, then
    figures out what new flowrate would be needed to reach target_OD in deltaT time
    """

    if (target_OD < 0.01):  # might have calculated a bad target if this happens
        return current_flowrate

    # bad ODs - can't take the log
    if current_OD <= 0 or previous_OD <= 0 or target_OD <= 0:
        return 0.0

    newf = current_flowrate + flask_vol_ml / deltaT * (
        2 * np.log(current_OD) - np.log(previous_OD) - np.log(target_OD)
    )

    # if target is much larger than current OD, it will calculate a negative flow rate
    if newf < 0:
        return 0.0

    # limit max flow rate
    if newf > 35.0:
        return 35.0

    return newf


# Calculate flowrates
def calculate_flowrates(t, df, flowrates, p: Params):
    newflows = []

    for i, f in enumerate(["A", "B"]):
        od = df["OD"][df["Reactor"] == f]

        if len(od) < 2:
            newflows.append(flowrates[i])
            continue

        current, previous = od.iloc[-1], od.iloc[-2]

        target = TARGET_OD[f](t, p)  # calculate target

        newf = newflowrate(
            flowrates[i],
            p.FLASK_VOL_ML,
            p.SAMPLE_INTERVAL_MINS / 60,
            current,
            previous,
            target,
        )

        newflows.append(newf)

    return newflows


def main():
    params = Params()

    # Pandas data frame to store ODs and flowrates
    # Updated flowrates are logged in the same row as the OD measurement which triggered the update
    c = ["Time (hrs)", "Reactor", "OD", "Flowrate"]
    df = pd.DataFrame(columns=c, dtype=float)

    connect_OGI3(verbose=True)

    # settings for chemostat
    sendcmd("choose OD cal 0")
    sendcmd("set exp length 48")
    sendcmd(f"set sample interval {params.SAMPLE_INTERVAL_MINS}")
    sendcmd("set motors rpm 4000")
    sendcmd("set ambient temp 23")
    sendcmd("set temp control targets 30")
    sendcmd("set temp controls 1")
    sendcmd("set temp control C 0")  # not using flask C
    sendcmd("set temp control D 0")  # not using flask D
    sendcmd(f"set chemostat flowrates 0")
    sendcmd("start chemostat")

    # Take two measurements so we have previous ODs to work with
    df = update_ODs(df)
    update_plot(df, params.SAMPLE_INTERVAL_SEC)
    df = update_ODs(df)
    update_plot(df, params.SAMPLE_INTERVAL_SEC)

    # We need to wait for each flask to reach its initial OD before starting
    still_growingA = True
    still_growingB = True

    # Flag to start the time when all flasks have reached their targets
    T_INIT = None

    # initial flow rates
    flowrates = [0, 0]

    try:
        while True:
            # need this loop to happen once every SAMPLE_INTERVAL_SEC
            t_loop = time.time()

            df = update_ODs(df)

            if df["OD"][df["Reactor"] == "A"].iloc[-1] > params.OD_0 and still_growingA:
                still_growingA = False
            if df["OD"][df["Reactor"] == "B"].iloc[-1] > params.OD_1 and still_growingB:
                still_growingB = False

            # All flasks have reached initial OD, start the time
            if T_INIT is None and not (still_growingA or still_growingB):
                T_INIT = time.time()

            # If not started, t = 0 will make all target ODs the initial ODs
            if T_INIT is None:
                t = 0
            else:
                t = (time.time() - T_INIT) / 3600  # in hrs

            flowA, flowB = calculate_flowrates(t, df, flowrates, params)

            # helper function to get index of last OD
            ind = lambda f: df[df["Reactor"] == f].index[-1]

            # save flowrates to dataframe
            df.loc[ind("A"), "Flowrate"] = flowA
            df.loc[ind("B"), "Flowrate"] = flowB

            # store most recent flowrates in array for next iteration
            flowrates = [flowA, flowB]

            # send new flowrates to device
            update_flowrates(flowA, flowB)

            # Save data to file
            FILENAME = "valentine.csv"
            df.to_csv(FILENAME, index=False)

            t_remaining = max(0, t_loop + params.SAMPLE_INTERVAL_SEC - time.time())
            update_plot(df, t_remaining)

    except Exception as e:
        # something went wrong - switch off pumps before exiting
        sendcmd("set chemostat flowrates 0")
        print(f"Exception {e}")


if __name__ == "__main__":
    main()
