import sys
import time
import serial as s
import serial.tools.list_ports as stl


def sendcmd(cmd):
    global ser, ogi_flags
    if "verbose" in ogi_flags:
        print("sending the command: " + cmd)

    try:
        while ser.in_waiting:  # there is data in the buffer - print until clear
            print(ser.read(64).decode("utf-8"))

        # ready to send
        ser.write(cmd.encode("utf-8"))

        # wait for response
        while True:
            if ser.in_waiting:
                # read back response
                mystr = ser.read_until("\r").decode("utf-8")

                # check that return message starts with our command
                if not mystr.startswith(cmd):
                    print(f"error, return message {mystr} does not match command {cmd}")
                    if "exit_on_fail" in ogi_flags:
                        sys.exit()
                    return

                # check for error
                if mystr.find("ERR") != -1:
                    print(mystr.rstrip().partition("ERR"))
                    if "exit_on_fail" in ogi_flags:
                        sys.exit()
                    return

                # success - return payload
                return mystr.rstrip().partition(cmd)[2]
    except:
        print("error, serial connection lost")
        if ("automatic_reconnect" in ogi_flags) and (
            "exit_on_fail_disconnect" not in ogi_flags
        ):
            print("attempting to reconnect...")
            connect_OGI3(keep_flags=True, attempts=10000)
            return
        if "exit_on_fail" in ogi_flags:
            sys.exit()
        return


## Serial connection
def connect_OGI3(
    keep_flags=False,
    exit_on_fail=False,
    verbose=False,
    exit_on_fail_disconnect=False,
    attempts=5,
    automatic_reconnect=False,
):
    global ser, ogi_flags
    if keep_flags == False:
        ogi_flags = set()
    if exit_on_fail:
        ogi_flags.add("exit_on_fail")
    if verbose:
        ogi_flags.add("verbose")
    if automatic_reconnect:
        ogi_flags.add("automatic_reconnect")

    while attempts > 0:
        try:
            ser = s.Serial()
            ser.port = next(
                stl.grep("COM*")
            ).name  # Try to automatically find the port - replace with eg 'COM15' if it doesn't work
            ser.baudrate = 115200
            ser.timeout = 1

            # Disable DTR to prevent Arduino auto-reset
            ser.dtr = False
            ser.rts = False

            # Wait a moment for settings to take effect
            time.sleep(0.5)
            ser.open()
            attempts = 0

        except:
            print(
                "error, couldn't open port - check connection and that port isn't being used in another process"
            )
            if exit_on_fail_disconnect:
                sys.exit()
            attempts -= 1
            time.sleep(1)

    if ser.isOpen():
        print("Serial connection established\n")
        # wait for reactor to start
        time.sleep(0.5)
    else:
        print("error, serial port not open")
        if exit_on_fail_disconnect:
            sys.exit()
        else:
            return
