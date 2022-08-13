#!/usr/bin/python3

#  version 2020-07-29
# Basic approach for reporting:
#  1. Write a logfile with the raw values (RecordValues)
#  2. Decode the values after the run. (Decode)
from datetime import datetime
import time
import serial  # pip3 install pyserial
import os
from pathlib import Path

# constants
sleep_time = 0.2 # seconds
# see udev rules for device construction
serial_dev = '/dev/NANO' # NANO connected via rPi USB;
data_dir = '/var/www/html/data'
current_symlink = data_dir+'/current'
file_timestamp = datetime.now().strftime('%Y-%m-%dT%H%M')
raw_log_file_path = data_dir + '/raw-' + file_timestamp + '.csv'
live_readings = data_dir+'/live_readings'
position_file = "/mnt/ramdisk/POSITION"  ## written by PickleGPS.py

nano_header = 'millis,frontCount,deltaFrontCount,deltaFrontMicros,rearCount,deltaRearCount,deltaRearMicros,rawLeftRideHeight,rawRightRideHeight,rawFuelPressure,rawFuelTemperature,rawGearPosition,rawAirFuelRatio,rawManifoldAbsolutePressure,rawExhaustGasTemperature'
gps_header = 'latitude,longitude,altitudeFt,mph,utc'

# globals
NANO = 0
RAW_LOG_FILE = 0

##### FUNCTIONS #############################################
#initialize serial (UART) connection to arduino
def init_nano():
    global NANO
    isOpen = False
    while not isOpen:
        try:
            # baud must match what's in the Arduino sketch
            NANO = serial.Serial(serial_dev, 57600, timeout = 1)
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

def get_raw_nano_data():
    global NANO
    raw_nano_data = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
    try:
        NANO.write(str('d').encode())
        raw_nano_data = NANO.readline().decode('ascii').rstrip()
    except Exception as e:
        print("exception in get_raw_nano_data: " + str(e))
    return raw_nano_data

def get_gps_data():
    try:
        if os.stat(position_file).st_size > 0:
           return Path(position_file).read_text()
    except OSError:
        print("No POSITION file found")
    except Exception as e:
        print("exception in get_gps_data: " + str(e))
    # gps_header is defined above as: 'latitude,longitude,altitudeFt,mph,utc'
    return '0.0,0.0,0,0,unknown'

def get_wheel_rpm(pulseCount,elapsedMicros):
    micros_per_minute = 1000000 * 60 # microseconds
    # one magnet per wheel means one pulse per revolution
    pulses_per_minute = 0
    if pulseCount > 0:
        average_pulse_micros = (elapsedMicros / pulseCount)  # each pulse took, on average
        pulses_per_minute = micros_per_minute / average_pulse_micros
    return int(pulses_per_minute) # int throws away the fraction

def get_wheel_rpms(raw_nano_data):
    # millis,frontCount,deltaFrontCount,deltaFrontMicros,rearCount,deltaRearCount,deltaRearMicros,
    nano_data = raw_nano_data.split(',')
    deltaFrontCount  = int(nano_data[2])
    deltaFrontMicros = int(nano_data[3])
    deltaRearCount   = int(nano_data[5])
    deltaRearMicros  = int(nano_data[6])
    fRpm = get_wheel_rpm(deltaFrontCount,deltaFrontMicros)
    rRpm = get_wheel_rpm(deltaRearCount,deltaRearMicros)
    return(fRpm,rRpm)

def provision_for_live_readings():
  try:
    # clear the live reading flag on startup. Only the PickleDisplay sets it.
    #if not os.path.isfile(live_readings):
    #  os.remove(live_readings)
    # PickleDisplay will tail the ./current symlink for a raw_data line
    if os.path.islink(current_symlink):
      os.remove(current_symlink)
    os.symlink(raw_log_file_path,current_symlink)
  except Exception as e:
    print('Error provisioning for live readings;' + str(e))

##### MAIN MAIN MAIN ###################################
init_nano()

# our primary output is a .csv file of raw values. Writing this is Job #1.
# if this open() fails, we should just die.
RAW_LOG_FILE = open(raw_log_file_path,mode='w',buffering=1)
RAW_LOG_FILE.write('timestamp,' + nano_header + ',' + gps_header + '\n')
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
        (fRpm,rRpm) = get_wheel_rpms(raw_nano_data)

	# only write if we are moving or doing live readings
        if mph>2 or fRpm>1 or rRpm>1 or os.path.isfile(live_readings):
          RAW_LOG_FILE.write(timestamp + ',' + raw_nano_data + ',' + gps_data)

    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except Exception as e:
        print("exception in main loop: " + str(e))

RAW_LOG_FILE.close()
print('Finished program, raw_data is in ' + raw_log_file_path)
