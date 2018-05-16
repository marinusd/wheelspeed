#!/usr/bin/env python3

#  version 2018-05-13
# Basic approach for reporting:
#  1. Write a logfile with the raw values
#  2. Write a datafile with calculated info
from datetime import datetime
import time
import serial  #  pip3 install pyserial
import gpsd    #  pip3 install gpsd-py3 https://github.com/MartijnBraam/gpsd-py3
import Decode

# constants
data_dir = '/tmp/pi/datalogs'
file_timestamp = datetime.now().strftime('%Y-%m-%d.%H:%M')
raw_log_file_path = data_dir + '/raw-' + file_timestamp + '.csv'
data_file_path = data_dir + '/data-' + file_timestamp + '.csv'
micros_per_minute = 1000000  # microseconds
analog_factor = 0.0048828125  # 0 = 0V, 512 = 2.5V, 1024 = 5V
gps_header = 'latitude,longitude,altitudeFt,mph,utc'
readings_header = 'time,mph,fRpm,rRpm,afr,map,fTemp,fPress,lrh,rrh,utc'

# globals
NANO = 0
DATA_FILE = 0
RAW_LOG_FILE = 0

##### FUNCTIONS #############################################
#initialize serial (UART) connection to arduino
def init_nano():
    global NANO
    isOpen = False
    while not isOpen:
        try:
            # baud must match what's in the Arduino sketch
            NANO = serial.Serial('/dev/serial0', 38400, timeout = 1)
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

def init_gps():
    i = 0
    while i < 3:
        try:
            gpsd.connect()   # gpsd daemon should be running in O.S.
        except:
            print("exception in init_gps")
            time.sleep(1.5)
            i = i + 1
        else:
            break
    packet = gpsd.get_current()  # this will blow up if we are not connected
    if (packet.mode > 1):   # then we have either a 2D or 3D fix
        print('GPS position: ' + str(packet.position()))
    else:
        print('GPS: no position fix from device: ' + str(gpsd.device()))

def get_raw_nano_data():
    global NANO
    raw_nano_data = ''
    try:
        NANO.write(str('d').encode())
        raw_nano_data = NANO.readline().decode('ascii').rstrip()
    except:
        print("exception in get_raw_nano_data")
    return raw_nano_data

def write_raw_log_header():
    global NANO
    global RAW_LOG_FILE
    NANO.write(str('h').encode())
    NANO_header = NANO.readline().decode('ascii').rstrip()
    RAW_LOG_FILE.write('timestamp,' + nano_header + ',' + gps_header + '\n')

def write_raw_log(timestamp,raw_nano_data,gps_data):
    global RAW_LOG_FILE
    RAW_LOG_FILE.write(timestamp + ',' +raw_nano_data + ',' + gps_data + '\n')

def write_data_header():
    global DATA_FILE
    DATA_FILE.write(readings_header + '\n')

def write_data_file(timestamp,readings):
    global DATA_FILE
    DATA_FILE.write(timestamp + ',' + readings + '\n')

##### MAIN MAIN MAIN ###################################
#init_gps()
#init_nano()

RAW_LOG_FILE = open(raw_log_file_path,'w')
print('Writing raw log to ' + raw_log_file_path)
#write_raw_log_header()

DATA_FILE = open(data_file_path,'w')
print('Writing data to ' + data_file_path)
write_data_header()

print('Starting sensor collection loop... Ctrl-C to stop loop')
while True:
    try:
        time.sleep(0.33) # 3Hz max
        # example timestamp: 1526430861.829
        timestamp = datetime.now().strftime('%s.%f')[:-3]
        gps_data = Decode.get_gps_data()
        raw_nano_data = get_raw_nano_data()
        write_raw_log(timestamp, raw_nano_data, gps_data)
        # now the processed numbers
        readings = Decode.get_readings(raw_nano_data, gps_data)
        write_data_file(timestamp, readings)
    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except:
        print("exception in main loop")

RAW_LOG_FILE.close()
DATA_FILE.close()
print('Finished program, data is in ' + data_file_path)
