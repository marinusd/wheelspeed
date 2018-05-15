#!/usr/bin/env python3

#  version 2018-05-13
# Basic approach for reporting:
#  1. Write a logfile with the raw values
#  2. Write a datafile with calculated info
from datetime import datetime
import time
import serial  #  pip3 install pyserial
import gpsd    #  pip3 install gpsd-py3 https://github.com/MartijnBraam/gpsd-py3

# this prints a header every 20 lines
tuning = True

file_timestamp = datetime.now().strftime('%Y-%m-%d.%H:%M')
raw_log_file_path = '/home/pi/datalogs/raw-' + file_timestamp + '.csv'
data_file_path = '/home/pi/datalogs/data-' + file_timestamp + '.csv'
nano = 0 # this will be a serial connection
micros_per_minute = 1000000  # microseconds
analog_factor = 0.0048828125  # 0 = 0V, 512 = 2.5V, 1024 = 5V
gps_header = 'latitude,longitude,altitudeFt,mph,utc'
readings_header = 'time,mph,fRpm,rRpm,afr,map,fTemp,fPress,lrh,rrh,utc'

##### FUNCTIONS #############################################
#initialize serial (UART) connection to arduino
def init_nano():
    global nano
    # baud must match what's in the Arduino sketch
    nano = serial.Serial('/dev/serial0', 38400, timeout = 1)
    nano.close()
    nano.open()
    if nano.isOpen():
        print('Nano open: ' + nano.portstr)
    else:
        print('Nano not open?')

def init_gps():
    gpsd.connect()
    packet = gpsd.get_current()
    if (packet.mode > 1):   # then we have either a 2D or 3D fix
    # See the inline docs for GpsResponse for the available data
        print('GPS: ' + str(packet.position()))
    else:
        print('GPS: no position fix from device: ' + str(gpsd.device()))

def get_raw_nano_data():
    global nano
    nano.write(str('d').encode())
    raw_nano_data = nano.readline().decode('ascii').rstrip()
    return raw_nano_data

def get_gps_data():
    lat = lon = alt = mph = utc = '' # make them empty strings
    packet = gpsd.get_current()
    if (packet.mode >= 2):
        lat = str(packet.lat)
        lon = str(packet.lon)
        mph = str(int(packet.hspeed * 2.2369363)) # speed in m/s, we use mph
        utc = str(packet.time)
    if (packet.mode >= 3):
        alt = str(int(packet.alt * 3.2808399)) # alt in meters, we use feet
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
    # cook the nano data
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
    lrh = get_ride_height(rawLeftRideHeight)
    rrh = get_ride_height(rawRightRideHeight)
    fp  = get_fuel_pressure(rawFuelPressure)
    ft  = get_fuel_temperature(rawFuelTemperature)
    gp  = get_gear_position(rawGearPosition)
    afr = get_afr(rawAirFuelRatio)
    man = get_man_abs_pressure(rawManifoldAbsolutePressure)
    egt = get_egt(rawExhaustGasTemperature)
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
    global nano
    global raw_log_file
    nano.write(str('h').encode())
    nano_header = nano.readline().decode('ascii').rstrip()
    raw_log_file.write('timestamp,' + nano_header + ',' + gps_header + '\n')

def write_raw_log(timestamp,raw_nano_data,gps_data):
    global raw_log_file
    raw_log_file.write(timestamp + ',' +raw_nano_data + ',' + gps_data + '\n')

def write_data_header():
    global data_file
    data_file.write(readings_header + '\n')

def write_data_file(timestamp,readings):
    global data_file
    data_file.write(timestamp + ',' + readings + '\n')

##### MAIN MAIN MAIN ###################################
init_nano()
init_gps()

raw_log_file = open(raw_log_file_path,'w')
write_raw_log_header()
print('Writing raw log to ' + raw_log_file_path)

data_file = open(data_file_path,'w')
write_data_header()
print('Writing data to ' + data_file_path)

print('Starting sensor collection loop... Ctrl-C to stop loop')
try:
    i = 0
    while True:
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        #if (i % 20 == 0 and tuning):
        #    write_header_to_raw_file()
        gps_data = get_gps_data()
        raw_nano_data = get_nano_data()
        write_raw_log(timestamp, raw_nano_data,gps_data)
        # now the processed numbers
        readings = get_readings(raw_nano_data,gps_data)
        write_data_file(timestamp, readings)
        time.sleep(0.33) # 3Hz max
        i =+ 1
except KeyboardInterrupt:
    print("\nShutting down")

raw_log_file.close()
data_file.close()
print('Finished program, data is in ' + data_file_path)
