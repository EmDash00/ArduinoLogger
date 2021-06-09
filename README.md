# Arduino Data Logger

Simple data Logs serial data from Arduino to a file without losing the ability to use Serial debugging.

## Usage

```
usage: logger.py [-h] [--port PORT] [--baud BAUD] [--name NAME] [--timestamp]
                 [--timeout TIMEOUT] [--echo] [--no-handshake]
                 [--config CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Port to listen for communications on
  --baud BAUD, -b BAUD  Baud rate of the communications. By default 9600
  --name NAME, -n NAME  Name of output file
  --timestamp           Whether or not to apppend a timestamp to the output
                        file. By default, true
  --timeout TIMEOUT, -t TIMEOUT
                        Communications timeout in seconds. By default 0.1s
  --echo, -e            Echo logging data
  --no-handshake        Don't handshake with the Arduino to ensure its there.
  --config CONFIG, -c CONFIG
                        .json or .yaml config file with logger configuration
```

#### Example Usage

```
./logger -p "COM3" --baud=115200
```

The above command will listen on `COM3` and print output to a file called `out [TIME].csv`.

#### Using Config Files

It is also possible to use a configuration specified in a YAML or JSON files. This makes it less tedious to remember the configuration for the logger.

```
./logger --config="config.yml"
```

The above command will use the config specified in `config.yml`. Missing or `null` values in the config are treated as default values by the program. Extra values provided are ignored.

## Installation

Requirements: Python 3.6+

```
git clone https://github.com/EmDash00/ArduinoLogger.git
pip install -r requirements.txt
```

Run with

```
./logger.py
```

#### Optional Dependency: arduino-cli

If `arduino-cli` is installed and is on `PATH` the program gains both the ability to automatically determine the port if only one device is connected. This makes the below command possible.

```
./logger.py
```

It also becomes possible to validate whether the specified `PORT` is a valid device. For example:

```
./logger.py
error: there are no valid devices
```

## Theory of Operation

When the Arduino Data Logger starts, it initiates a "handshake" with device on the specified serial port  (unless specified otherwise using `--no-handshake`). Functionally, this means it will wait for a byte containing `0xFF` to be transmitted. On receiving the byte, the logger will return the "handshake" by sending back the same `0xFF` byte. 

Then, Arduino Data Logger simply reads lines printed to the serial port and logs it to a file. What you print is what you get. The exception to this rule is messages staring with `ECHO:`. These messages not logged to the file and instead only printed to the screen.

When the logger receives a line containing `DONE`, it stops listening and the program terminates.