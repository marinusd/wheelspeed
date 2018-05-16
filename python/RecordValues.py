#!/usr/bin/env python3

#  version 2018-05-13
# Basic approach for reporting:
#  1. Write a logfile with the raw values
#  2. Write a datafile with calculated info
from datetime import datetime
import time
import serial  #  pip3 install pyserial
import gpsd    #  pip3 install gpsd-py3 https://github.com/MartijnBraam/gpsd-py3

# constants
data_dir = '/home/pi/datalogs'
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

def get_gps_data():
    lat = lon = alt = mph = utc = '' # make them empty strings
    try:
        packet = gpsd.get_current()
        if (packet.mode >= 2):
            lat = str(packet.lat)
            lon = str(packet.lon)
            mph = str(int(packet.hspeed * 2.2369363)) # speed in m/s, we use mph
            utc = str(packet.time)
        if (packet.mode >= 3):
            alt = str(int(packet.alt * 3.2808399)) # alt in meters, we use feet
    except:
        print("Exception in get_gps_data")
    return lat + ',' + lon + ',' + alt + ',' + mph + ',' + utc

def get_axle_rpm(micros,count):
    pulses_per_minute = 0
    if count > 0:
        pulse_time_micros = (micros / count)  # each pulse arrived, on average
        pulses_per_minute = micros_per_minute / pulse_time_micros
    return str(int(pulses_per_minute))

# linear potentiometers give a voltage between 0V-3.3V;
#   arduino encodes to an int 0-1024; and we want a range 0..100
# The ride height sensor readings go DOWN as the accordion units are extended
#  and the readings go UP as the units are compressed, so we must invert.
def get_ride_height(pinValue):
    return str(int(100 - (pinValue * 100 / 1024)))

# VDO 10-bar pressure sensor has resistance between 8ohms and 180ohms
#  A voltage divider circuit gives between about 1.6V and 4.8V to the arduino
#  arduino encodes to an int 0-1024; we will not see the min/max values
#  when pressure is high, voltage is low; so invert (and normalize to 0-100)
def get_fuel_pressure(pinValue):
    return str(int(100 - (pinValue * 100 / 1024)))

# temp sensor resistance is between 3200 and 12 ohms
#  Resistance decreases with increasing temperature
#  The voltage divider circuit converts the resistance to a voltage between about
#   1.6V (low) and 4.9V (high)
#  The arduino will report that voltage as an int between 0-1024
def get_fuel_temperature(pinValue):
    return str(int(pinValue * 100 / 1024))

# the NTK gives a voltage from 0V-5V; the arduino turns that into a int between 0-1024
def get_afr(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    afr = 9 + (1.4 * voltage)   # according to the NTK doc, 0V = 9.0, 5V = 16.0
    (whole,fraction) = str(afr).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

# the MAP gives a voltage from 0V-5V; the arduino turns that into a int between 0-1024
def get_map(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    # 11kPa = 0.25V, 307kPa = 4.75V, so
    kpa = voltage * 64.6315789473
    psi = kpa * 0.14503774
    (whole,fraction) = str(psi).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

def get_readings(raw_nano_data,gps_data):
    mph = fRpm = rRpm = afr = man = ft = fp = lrh = rrh = utc = ''
    # cook the nano data
    try:
        (millis,
        frontCount,deltaFrontCount,deltaFrontMicros,
        rearCount,deltaRearCount,deltaRearMicros,
        rawLeftRideHeight,rawRightRideHeight,
        rawFuelPressure,rawFuelTemperature,
        rawGearPosition,rawAirFuelRatio,
        rawManifoldAbsolutePressure,rawExhaustGasTemperature
        ) = raw_nano_data.split(',')
        (lat,lon,alt,mph,utc) = gps_data.split(',')
        # calcs and transforms
        fRpm = get_axle_rpm(deltaFrontCount,deltaFrontMicros)
        rRpm = get_axle_rpm(deltaRearCount,deltaRearMicros)
        afr = get_afr(rawAirFuelRatio)
        man = get_man_abs_pressure(rawManifoldAbsolutePressure)
        ft  = get_fuel_temperature(rawFuelTemperature)
        fp  = get_fuel_pressure(rawFuelPressure)
        lrh = get_ride_height(rawLeftRideHeight)
        rrh = get_ride_height(rawRightRideHeight)
        #gp  = get_gear_position(rawGearPosition)
        #egt = get_egt(rawExhaustGasTemperature)
    except:
        print("exception in get_readings")
    # returnCols = 'mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc'
    return ( mph + ',' +
            fRpm + ',' +
            rRpm + ',' +
             afr + ',' +
             man + ',' +
              ft + ',' +
              fp + ',' +
             lrh + ',' +
             rrh + ',' +
             utc
            )

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
init_gps()
init_nano()

RAW_LOG_FILE = open(raw_log_file_path,'w')
print('Writing raw log to ' + raw_log_file_path)
write_raw_log_header()

DATA_FILE = open(data_file_path,'w')
print('Writing data to ' + data_file_path)
write_data_header()

print('Starting sensor collection loop... Ctrl-C to stop loop')
while True:
    try:
        time.sleep(0.33) # 3Hz max
        # example timestamp: 1526430861.829
        timestamp = datetime.now().strftime('%s.%f')[:-3]
        gps_data = get_gps_data()
        raw_nano_data = get_raw_nano_data()
        write_raw_log(timestamp, raw_nano_data, gps_data)
        # now the processed numbers
        readings = get_readings(raw_nano_data, gps_data)
        write_data_file(timestamp, readings)
    except KeyboardInterrupt:
        print("\nShutting down")
        break
    except:
        print("exception in main loop")

RAW_LOG_FILE.close()
DATA_FILE.close()
print('Finished program, data is in ' + data_file_path)
