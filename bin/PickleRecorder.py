#!/usr/bin/python3

#  version 2020-07-29
# Basic approach for reporting:
#  1. Write a logfile with the raw values (RecordValues)
#  2. Decode the values after the run. (Decode)
from datetime import datetime
import time
import serial  # pip3 install pyserial
import gpsd    # pip3 install gpsd-py3 https://github.com/MartijnBraam/gpsd-py3
import os

# constants
sleep_time = 0.2 # seconds
serial_dev = '/dev/serial0' # NANO connected via rPi UART;
serial_dev = '/dev/ttyUSB0' # NANO connected via rPi USB;
data_dir = '/var/www/html/data'
current_symlink = data_dir+'/current'
file_timestamp = datetime.now().strftime('%Y-%m-%dT%H%M')
raw_log_file_path = data_dir + '/raw-' + file_timestamp + '.csv'

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
            NANO = serial.Serial(serial_dev, 38400, timeout = 1)
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
  while i < 9:
    try:
      gpsd.connect()   # gpsd daemon should be running in O.S.
    except Exception as e:
      print("init_gps: cannot connect to gpsd daemon: " +str(e))
      time.sleep(1.5)
      continue
    try:
      packet = gpsd.get_current()  # this will blow up if we are not connected
      if (packet.mode > 1):   # then we have either a 2D or 3D fix
        print('GPS position: ' + str(packet.position()))
      else:
        print('GPS: no position fix from device yet: ' + str(gpsd.device()))
      break
    except:
      print("init_gps:exception getting current position")
      time.sleep(1.5)


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
    lat = lon = alt = mph = utc = '0' # make them numeric
    try:
        packet = gpsd.get_current()
        if (packet.mode >= 2):
            lat = str(packet.lat)
            lon = str(packet.lon)
            mph = str(int(packet.hspeed * 2.2369363)) # speed in m/s, we use mph
            utc = str(packet.time)
        if (packet.mode >= 3):
            alt = str(int(packet.alt * 3.2808399)) # alt in meters, we use feet
    except Exception as e:
        print("exception in get_gps_data: " + str(e))
    return lat + ',' + lon + ',' + alt + ',' + mph + ',' + utc

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

def write_raw_log_header():
    global RAW_LOG_FILE
    RAW_LOG_FILE.write('timestamp,' + nano_header + ',' + gps_header + '\n')

def write_raw_log(timestamp,raw_nano_data,gps_data):
    global RAW_LOG_FILE
    RAW_LOG_FILE.write(timestamp + ',' + raw_nano_data + ',' + gps_data + '\n')


##### MAIN MAIN MAIN ###################################
init_gps()
init_nano()

RAW_LOG_FILE = open(raw_log_file_path,mode='w',buffering=1)
if os.path.islink(current_symlink):
  os.unlink(current_symlink)
os.symlink(raw_log_file_path,current_symlink)
print('Writing raw log to ' + raw_log_file_path)
write_raw_log_header()

print('Starting sensor collection loop... Ctrl-C to stop loop')
while True:
    try:
        time.sleep(sleep_time) 
        # example timestamp: 1526430861.829
        timestamp = datetime.now().strftime('%s.%f')[:-3]

        gps_data = get_gps_data()
        mph = int(gps_data.split(',')[3])

        raw_nano_data = get_raw_nano_data()
        (fRpm,rRpm) = get_wheel_rpms(raw_nano_data)

        #print('MPH: ' + str(mph) + 'fRpm: ' + str(fRpm) + ' rRpm: ' + str(rRpm))
	# only write if we are moving
        if 1==1 or mph>1 or fRpm>1 or rRpm>1:
          write_raw_log(timestamp, raw_nano_data, gps_data)
        #else:
        #  print("MPH: %s fRPM: %s rRPM: %s - not enough movement." % (str(mph),str(fRpm),str(rRpm)))
    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except Exception as e:
        print("exception in main loop: " + str(e))

RAW_LOG_FILE.close()
print('Finished program, raw_data is in ' + raw_log_file_path)
