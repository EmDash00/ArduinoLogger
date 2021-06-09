#!/usr/bin/env python

import subprocess
from shutil import which

from argparse import ArgumentParser
from datetime import datetime
from deserialize import deserialize

from pathlib import Path
import json
import subprocess
import yaml

import serial

from typing import Optional

class Config:
    port: Optional[str]
    baud: Optional[int]
    name: Optional[str]
    timestamp: Optional[bool]
    timeout: Optional[float]
    echo: Optional[bool]
    no_handshake: Optional[bool]

    def __init__(self):
        self.port = None
        self.baud = 9600
        self.name = "out"
        self.timestamp = True
        self.timeout = 0.1
        self.echo = False
        self.no_handshake = False
    
    def fix(self):
        if self.port == "":
            self.port = None

        if self.baud is None:
            self.baud = 9600
        
        if self.name is None or self.name == "":
            self.name = "out"
        
        if self.timestamp is None:
            self.timestamp = False

        if self.timeout is None:
            self.timeout = 0.1
        
        if self.echo is None:
            self.echo = False
        
        if self.no_handshake is None:
            self.no_handshake = False
        
        return self



def main(port: str, baudrate: int, timeout: float, out: str, echo: bool, handshake: bool):

    with serial.Serial(port, baudrate, timeout=timeout) as dev:
        
        print ("Press enter to begin.")
        input()

        if handshake:
            signal = int.to_bytes(0xFF, length=1, byteorder='big')
    
            print("Waiting for handshake initiation...")

            while dev.read() != signal:
                pass

            dev.write(signal)

            print("Handshake completed!")

            dev.readline()

        with open(out, 'w') as f:
            while True:
                data = dev.readline()
            
                # Arduino uses ASCII encoding
                msg = data[:-2].decode('ascii')

                # Lines marked with ECHO: are treated as debug output.
                if not msg.startswith("ECHO:"):
                    if len(data) > 0:  # Valid transission 
                        # Stop saving 
                        if msg == "DONE":
                            break
                        else:
                            f.write(msg)
                            f.write('\n')
                    
                        if echo:
                            print(msg)
                else:
                    # 012345  ...       -1
                    # ECHO:Hello, World!\n
                    #      ^-----------^ is selected
                    print(msg[5:].lstrip())
        

def get_devices():
    res = subprocess.run(['arduino-cli', 'board', 'list'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    return [line.split(' ')[0] for line in res.split('\n')[1:-2] if not line.strip().endswith("Unknown")]

if __name__ == "__main__":
    parser = ArgumentParser()
   
    parser.add_argument(
        "--port",
        '-p', 
        help="Port to listen for communications on",
        type=str,
        default=""
    )
    
    parser.add_argument(
        "--baud", 
        help="Baud rate of the communications. By default 9600", 
        default=-1, 
        type=int
    )

    parser.add_argument(
        "--name",
        help="Name of output file",
        default="",
        type=str
    )

    parser.add_argument(
        "--timestamp",
        help="Timestamp output file",
        action="store_true"
    )
    
    parser.add_argument(
        "--timeout", 
        help="Communications timeout in seconds. By default 0.1s", 
        default=-1, 
        type=float
    )

    parser.add_argument(
        "--echo",
        help="Echo logging data",
        action="store_true"
    )


    parser.add_argument(
        "--no-handshake",
        help="Don't handshake with the Arduino to ensure its there.",
        action="store_true"
    )

    parser.add_argument(
        "--config",
        help=".json or .yaml config file with logger configuration",
        type=Path,
        default=""
    )

    args = parser.parse_args()

    if args.config != Path(""):
        if args.config.is_file():
            if args.config.suffix == ".json":
                with open(args.config, 'r') as f:
                    loaded_args = deserialize(Config, json.load(f)).fix()
            elif args.config.suffix == ".yml":
                with open(args.config, 'r') as f:
                    loaded_args = deserialize(Config, yaml.safe_load(f)).fix()
            else:
                print("error: Only JSON and YAML is supported.")
                parser.exit()
        else:
            print("error: config is not a file.")
            parser.exit() 
    else:
        loaded_args = Config()

    if args.port == "":
            if loaded_args.port is not None:
                if which('arduino-cli') is not None:
                    valid_devices = get_devices()
                    if loaded_args.port in valid_devices:
                        port = loaded_args.port
                    else:
                        print("error: specified port does not name a valid device.")
                        parser.exit()
                else:
                    valid_devices = loaded_args.port
            else:
                if which('arduino-cli') is not None:
                    valid_devices = get_devices()

                    if len(valid_devices) == 1:
                        port = valid_devices[0]
                    else:
                        print("There are multiple valid devices. Please specify in the config or through the command-line.")
                else:
                    parser.print_help()
                    print("error: arduino-cli not found. You must specify a PORT in the command-line or CONFIG.")
                    parser.exit()
    else:
        if which('arduino-cli') is not None:
            valid_devices = get_devices()
            if args.port in valid_devices:
                port = args.port
                parser.exit()
            else:
                print("error: specified port does not name a valid device.")
        else:
            port = args.port
     
    if args.baud < 0:
        baud = loaded_args.baud
    else:
        baud = args.baud

    if not args.echo:
        echo = loaded_args.echo
    else:
        echo = args.echo

    if args.timeout < 0:
        timeout = loaded_args.timeout
    else:
        timeout = args.timeout

    if not args.no_handshake:
        handshake = not loaded_args.no_handshake
    else:
        handshake = not args.no_handshake

    if not args.timestamp:
        timestamp = loaded_args.timestamp
    else:
        timestamp = args.timestamp
    
    time = " {:%Y-%m-%d %H.%M.%S}".format(datetime.now()) if timestamp else ""

    if args.name == "":
        name = loaded_args.name[:-4] if loaded_args.name.endswith('.csv') else loaded_args.name
        out = "{}{}{}".format(name, time, ".csv")
    else:
        name = args.name[:-4] if loaded_args.name.endswith('.csv') else args.name
        out = "{}{}{}".format(name, time, ".csv")

    #print(port, baud, out, echo, timeout, handshake)
    
    main(port, baud, timeout, out, echo, handshake)