#!/usr/bin/python3

#  version 2022-08-12b
# Basic approach for reporting:
#  1. Write a logfile with the raw values (RecordValues)
#  2. Decode the values after the run. (Decode)
from datetime import datetime
import time
import serial  # pip3 install pyserial
import os
from pathlib import Path

# constants
sleep_time = 0.25  # seconds
# see udev rules for device construction
nano_dev = '/dev/NANO'  # NANO  connected via rPi USB;
nano2_dev = '/dev/NANO2'  # NANO2 connected via rPi USB;
data_dir = '/var/www/html/data'
current_symlink = data_dir+'/current'
file_timestamp = datetime.now().strftime('%Y-%m-%dT%H%M')
raw_log_file_path = data_dir + '/raw-' + file_timestamp + '.csv'
live_readings = data_dir+'/live_readings'
position_file = "/mnt/ramdisk/POSITION"  # written by PickleGPS.py
gps_header = 'latitude,longitude,altitudeFt,mph,utc'

# globals
NANO = NANO2 = 0
RAW_LOG_FILE = 0

##### FUNCTIONS #############################################
# initialize serial (UART) connection to arduino


def init_nano():
    global NANO
    isOpen = False
    while not isOpen:
        try:
            # baud must match what's in the Arduino sketch
            NANO = serial.Serial(nano_dev, 57600, timeout=1)
            NANO.close()
            NANO.open()
            isOpen = NANO.isOpen()
        except:
            print("exception in init_nano")
            time.sleep(0.33)
    if isOpen:
        print('Nano open: ' + NANO.portstr)
    else:
        print('Nano not open? How can be?')


def get_nano_header():
    global NANO
    nano_header = '1000,1,1,1,1,1,1,1,1,1,1,1,1,1,1000'
                    # 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
    try:
        # clearing out the startup messages, yo
        junk = NANO.read(1000)
        junk = NANO.read(1000)
        NANO.write(str('h').encode())
        nano_header = NANO.readline().decode('ascii').rstrip()
    except Exception as e:
        print("exception in get_nano_header: " + str(e))
    return nano_header


def get_raw_nano_data():
    global NANO
    raw_nano_data = '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1'
                   # 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
    try:
        NANO.write(str('d').encode())
        raw_nano_data = NANO.readline().decode('ascii').rstrip()
    except Exception as e:
        print("exception in get_raw_nano_data: " + str(e))
    return raw_nano_data


def init_nano2():
    global NANO2
    isOpen = False
    while not isOpen:
        try:
            # baud must match what's in the Arduino sketch
            NANO2 = serial.Serial(nano2_dev, 57600, timeout=1)
            NANO2.close()
            NANO2.open()
            isOpen = NANO2.isOpen()
        except:
            print("exception in init_nano2")
            time.sleep(0.33)
    if isOpen:
        print('Nano2 open: ' + NANO2.portstr)
    else:
        print('Nano2 not open? How can be?')


def get_nano2_header():
    global NANO2
    nano2_header = '2000,2,2,2,2,2,2,2000'
                     # 1 2 3 4 5 6 7 8
    try:
        # clearing out the startup messages, yo
        junk = NANO2.read(1000)
        junk = NANO2.read(1000)
        NANO2.write(str('h').encode())
        nano2_header = NANO2.readline().decode('ascii').rstrip()
    except Exception as e:
        print("exception in get_nano2_header: " + str(e))
    return nano2_header


def get_raw_nano2_data():
    global NANO2
    raw_nano2_data = '2,2,2,2,2,2,2,2'
                    # 1 2 3 4 5 6 7 8
    try:
        NANO2.write(str('d').encode())
        raw_nano2_data = NANO2.readline().decode('ascii').rstrip()
    except Exception as e:
        print("exception in get_raw_nano2_data: " + str(e))
    return raw_nano2_data


def get_gps_data():
    try:
        if os.stat(position_file).st_size > 0:
           position = Path(position_file).read_text().strip()  # trim trailing whitespace
           (latitude,longitude,altitudeFloat,mphFloat,utc) = position.split(',')
           altitudeFt = altitudeFloat.split('.')[0] # truncate the string
           mph = mphFloat.split('.')[0]
           return latitude + ',' + longitude + ',' + altitudeFt + ',' + mph + ',' + utc
    except OSError:
        print("No POSITION file found")
    except Exception as e:
        print("exception in get_gps_data: " + str(e))
    # gps_header is defined above as: 'latitude,longitude,altitudeFt,mph,utc'
    return '0.0,0.0,0,0,unknown' # 5 elements, no newline


def get_wheel_rpm(pulseCount, elapsedMicros):
    micros_per_minute = 1000000 * 60  # microseconds
    # one magnet per wheel means one pulse per revolution
    pulses_per_minute = 0
    if pulseCount > 0:
        # each pulse took, on average
        average_pulse_micros = (elapsedMicros / pulseCount)
        pulses_per_minute = micros_per_minute / average_pulse_micros
    return int(pulses_per_minute)  # int throws away the fraction


def get_wheel_rpms(raw_nano_data):
    # millis,frontCount,deltaFrontCount,deltaFrontMicros,rearCount,deltaRearCount,deltaRearMicros,
    nano_data = raw_nano_data.split(',')
    deltaFrontCount = int(nano_data[2])
    deltaFrontMicros = int(nano_data[3])
    deltaRearCount = int(nano_data[5])
    deltaRearMicros = int(nano_data[6])
    fRpm = get_wheel_rpm(deltaFrontCount, deltaFrontMicros)
    rRpm = get_wheel_rpm(deltaRearCount, deltaRearMicros)
    return (fRpm, rRpm)


def provision_for_live_readings():
    try:
        # clear the live reading flag on startup. Only the PickleDisplay sets it.
        # PickleDisplay will tail the ./current symlink for a raw_data line
        if os.path.islink(current_symlink):
            os.remove(current_symlink)
        os.symlink(raw_log_file_path, current_symlink)
    except Exception as e:
        print('Error provisioning for live readings;' + str(e))


##### MAIN MAIN MAIN ###################################
init_nano()
init_nano2()

# our primary output is a .csv file of raw values. Writing this is Job #1.
# if this open() fails, we should just die.
RAW_LOG_FILE = open(raw_log_file_path, mode='w', buffering=1)
RAW_LOG_FILE.write('timestamp,' + get_nano_header() + ',' +
                   get_nano2_header() + ',' + gps_header + '\n')
print('Writing raw log to ' + raw_log_file_path)

# secondary function is providing live data if commanded by the PickleDisplay.
provision_for_live_readings()


print('Starting sensor collection loop... Ctrl-C to stop loop')
while True:
    try:
        time.sleep(sleep_time)
        # example timestamp: 1526430861.829
        timestamp = datetime.now().strftime('%s.%f')[:-3]

        gps_data = get_gps_data()
        mph = float(gps_data.split(',')[3])

        raw_nano_data = get_raw_nano_data()
        raw_nano2_data = get_raw_nano2_data()

        (fRpm, rRpm) = get_wheel_rpms(raw_nano_data)

        # only write if we are moving or doing live readings
        if mph > 2 or fRpm > 1 or rRpm > 1 or os.path.isfile(live_readings):
            RAW_LOG_FILE.write(timestamp + ',' + raw_nano_data +
                               ',' + raw_nano2_data + ',' + gps_data + '\n') # 1+15+8+5=29 elements

    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except Exception as e:
        print("exception in main loop: " + str(e))

RAW_LOG_FILE.close()
print('Finished program, raw_data is in ' + raw_log_file_path)
