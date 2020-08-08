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
#serial_dev = '/dev/serial0' # /dev/ttyS0 # NANO connected via rPi UART;
serial_dev = '/dev/ttyUSB0' # NANO connected via rPi USB;
data_dir = '/var/www/html/data'
current_symlink = data_dir+'/current'
file_timestamp = datetime.now().strftime('%Y-%m-%dT%H%M')
raw_log_file_path = data_dir + '/raw-' + file_timestamp + '.csv'
live_readings = data_dir+'/live_readings'

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

def set_system_time(gpstime):
  if gpstime != None and gpstime != '':
    #gpstime is formatted like"2015-04-01T17:32:04.000Z"
    #convert it to a form the date -u command will accept: "20140401 17:32:04"
    gpsutc = gpstime[0:4]+gpstime[5:7]+gpstime[8:10]+' '+gpstime[11:19]
    print('Trying to set system time to GPS UTC: ' + gpsutc)
    os.system('sudo date -u --set="%s"' % gpsutc)
  else:
    print('set_system_time: gpstime parameter null')

def init_gps():
  i = 0
  while i < 9:
    try:
      gpsd.connect()   # gpsd daemon should be running in O.S.
      break
    except Exception as e:
      print("init_gps: cannot connect to gpsd daemon: " +str(e))
      i = i + 1
      time.sleep(1.5)
  i = 0
  while i < 9:
    try:
      packet = gpsd.get_current()  # this will blow up if we are not connected
      break
    except:
      print("init_gps:exception getting current position")
      i = i + 1
      time.sleep(1.5)
  i = 0
  while i < 9:
    try:
      if (packet.mode > 1):   # then we have either a 2D or 3D fix
        print('GPS position: ' + str(packet.position()))
        set_system_time(packet.time)
        break
      else:
        print('GPS: no position fix from device yet: ' + str(gpsd.device()))
        i = i + 1
        time.sleep(1.5)
    except:
      print("init_gps:exception reading packet or setting time")

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

def provision_for_live_readings():
  try:
    # clear the live reading flag on startup. Only the PickleDisplay sets it.
    if os.path.isfile(live_readings):
      os.remove(live_readings)
    # PickleDisplay will tail the ./current symlink for a raw_data line
    if os.path.islink(current_symlink):
      os.remove(current_symlink)
    os.symlink(raw_log_file_path,current_symlink)
  except:
    print('Error provisioning for live readings')

##### MAIN MAIN MAIN ###################################
init_gps()
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
        mph = int(gps_data.split(',')[3])

        raw_nano_data = get_raw_nano_data()
        (fRpm,rRpm) = get_wheel_rpms(raw_nano_data)

	# only write if we are moving or doing live readings
        if mph>2 or fRpm>1 or rRpm>1 or os.path.isfile(live_readings):
          RAW_LOG_FILE.write(timestamp + ',' + raw_nano_data + ',' + gps_data + '\n')

    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except Exception as e:
        print("exception in main loop: " + str(e))

RAW_LOG_FILE.close()
print('Finished program, raw_data is in ' + raw_log_file_path)
