from argparse import ArgumentParser
from typing import Optional
from datetime import datetime
import serial

def main(port: str, baudrate: int, timeout: float, out: str, echo: bool, handshake: bool):

    with serial.Serial(port, baudrate, timeout=timeout) as dev:
        if handshake:
            signal = int.to_bytes(0xFF, length=1, byteorder='big')
    
            print("Waiting for handshake initiation...")

            while dev.read() != signal:
                pass

            dev.write(signal)

            print("Handshake completed!")

        with open(out, 'w') as f:
            while True:
                data = dev.readline()

                if len(data) > 0:
                    msg = data[:-2].decode('ascii')
                    if msg == "DONE":
                        break
                    else:
                        f.write(msg)
                        f.write('\n')

                if echo:
                    print(msg)
        
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "port", 
        help="Port to listen for communications on",
        type=str,
    )
    
    parser.add_argument(
        "--baud", 
        help="Baud rate of the communications. By default 9600", 
        default=9600, 
        type=int
    )

    parser.add_argument(
        "--name",
        help="Name of output file",
        default="out {:%Y-%m-%d %H.%M.%S}.csv".format(datetime.now()),
        #default="out.csv",
        type=str
    )
    
    parser.add_argument(
        "--timeout", 
        help="Communications timeout in seconds. By default 0.1s", 
        default=0.1, 
        type=float
    )

    parser.add_argument(
        "--echo",
        help="Echo serial data",
        action="store_true"
    )


    parser.add_argument(
        "--no-handshake",
        help="Don't handshake with the Arduino to ensure its there.",
        action="store_false"
    )

    args = parser.parse_args()

    if not args.name.endswith(".csv"):
        out = "{}\ .csv".format(args.name)
    else:
        out = args.name

    main(args.port, args.baud, args.timeout, out, args.echo, args.no_handshake)
