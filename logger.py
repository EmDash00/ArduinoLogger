#!/usr/bin/env python

import subprocess
from shutil import which

import re
from argparse import ArgumentParser
from datetime import datetime
from deserialize import deserialize  # type: ignore

from pathlib import Path
import json
import yaml

import serial  # type: ignore
from serial import SerialException

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
        self.name = "out.csv"
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


def main(
    port: str,
    baudrate: int,
    timeout: float,
    out: str,
    echo: bool,
    handshake: bool
):

    try:
        with serial.Serial(port, baudrate, timeout=timeout) as dev:

            print("Press enter to begin.")
            input()

            if handshake:
                signal = int.to_bytes(0xFF, length=1, byteorder='big')

                print("Waiting for handshake initiation...")

                i = 0
                msg = dev.read()

                while msg != signal:
                    if not len(msg):
                        i += 1
                        print("timed out. attempt {}/3".format(i))

                        if i == 3:
                            print(
                                "error: unabled to complete handshake. "
                                "Did you name a valid port?"
                            )
                            exit(1)

                    msg = dev.read()

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

    except SerialException:
        print("specified port does not name a valid device.")


def get_devices():
    res = subprocess.run(
        ['arduino-cli', 'board', 'list'],
        stdout=subprocess.PIPE
    ).stdout.decode('utf-8')

    return [
        line.split(' ')[0] for line in res.split('\n')[1:-2]
        if not line.strip().endswith("Unknown")
    ]


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
        "-b",
        help="Baud rate of the communications. By default 9600",
        default=-1,
        type=int
    )

    parser.add_argument(
        "--name",
        "-n",
        help="Name of output file",
        default="",
        type=str
    )

    parser.add_argument(
        "--timestamp",
        help="Whether or not to apppend a timestamp to the output file. By "
             "default, true",
        action="store_true"
    )

    parser.add_argument(
        "--timeout",
        "-t",
        help="Communications timeout in seconds. By default 0.1s",
        default=-1,
        type=float
    )

    parser.add_argument(
        "--echo",
        "-e",
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
        "-c",
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
                    print(
                        "error: specified port does not name a valid device."
                    )

                    parser.exit()
            else:
                valid_devices = loaded_args.port
        else:
            if which('arduino-cli') is not None:
                valid_devices = get_devices()

                if len(valid_devices) == 1:
                    port = valid_devices[0]
                elif len(valid_devices) > 1:
                    print(
                        "error: there are multiple valid devices. "
                        "Please specify a PORT in the config or through a "
                        "command-line option. You can list valid devices with"
                        "`arduino-cli board list'"
                    )

                    parser.exit()

                elif len(valid_devices) == 0:
                    print(
                        "error: there are no valid devices"
                    )

                    parser.exit()
            else:
                parser.print_help()
                print(
                    "error: `arduino-cli' not found, cannot determine port"
                    "automatically. "
                    "You must specify a PORT in a provided CONFIG or through "
                    "a command-line option"
                )

                parser.exit()
    else:
        if which('arduino-cli') is not None:
            valid_devices = get_devices()
            if args.port in valid_devices:
                port = args.port
            else:
                port = args.port
                print("error: specified port does not name a valid device.")
                parser.exit()
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

    p = re.compile(r"(\w+\.*)\.?(\w+)?")

    if args.name == "":
        res = p.match(loaded_args.name)
    else:
        res = p.match(args.name)

    if res.group(2) is not None:  # type: ignore
        name = res.group(1)[:-1]  # type: ignore
        suffix = ".{}".format(res.group(2))  # type: ignore
    else:
        name = res.group(1)  # type: ignore
        suffix = ""

    out = "{}{}{}".format(
        name,   # type: ignore
        time,
        suffix
    )

    main(port, baud, timeout, out, echo, handshake)
