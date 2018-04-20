#!/usr/bin/env python3

from datetime import datetime
import time
import serial
import gpsd

# this prints a header every 20 lines
tuning = True

now = datetime.now()
file_path = '/home/pi/datalogs/' + now.strftime('%Y-%m-%d.%H:%M') + '.csv'
nano = 0 # this will be a serial connection
micros_per_minute = 1000000
analog_factor = 0.0048828125  # 0 = 0V, 512 = 2.5V, 1024 = 5V

#####FUNCTIONS#############################################
#initialize serial connection
def init_serial():
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
    if (packet.mode > 1):   # we have either a 2D or 3D fix
    # See the inline docs for GpsResponse for the available data
        print('GPS: ' + str(packet.position()))
    else:
        print('GPS: no position fix from device: ' + str(gpsd.device()))

def get_gps():
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

# the NTK gives a voltage from 0V-5V; the arduino turns that into a int between 0-1024
def get_afr(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    afr = 9 + (1.4 * voltage)   # according to the NTK doc, 0V = 9.0, 5V = 16.0
    (whole,fraction) = str(afr).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

def get_nano():
    global nano
    nano.write(str('d').encode())
    nano_data = nano.readline().decode('ascii').rstrip()
    (millis,
    frontCount,deltaFrontCount,deltaFrontMicros,
    rearCount,deltaRearCount,deltaRearMicros,
    rawLeftRideHeight,rawRightRideHeight,
    rawFuelPressure,rawFuelTemperature,
    rawGearPosition,rawAirFuelRatio,
    rawManifoldAbsolutePressure,rawExhaustGasTemperature) = nano_data.split(',')

    front_rpm = get_axle_rpm(deltaFrontCount,deltaFrontMicros)
    rear_rpm = get_axle_rpm(deltaRearCount,deltaRearMicros)
    afr = get_afr(rawAirFuelRatio)

    return lat + ',' + lon + ',' + alt + ',' + mph + ',' + utc

def write_header():
    global nano
    global output_file
    nano.write(str('h').encode())
    nano_header = nano.readline().decode('ascii').rstrip()
    gps_header = 'latitude,longitude,altitudeFt,mph,utc'
    output_file.write(nano_header + ',' + gps_header + '\n')

#####################################################
init_serial()
init_gps()

output_file = open(file_path,'w')
write_header()
print('Writing log to ' + file_path)

print('Starting data collection loop... Ctrl-C to stop loop')
try:
    i = 0
    while True:
        if (i % 20 == 0 and tuning):
            write_header()
        nano.write(str('d').encode())
        nano_data = nano.readline().decode('ascii').rstrip()
        gps_data = get_gps()
        output_file.write(nano_data + ',' + gps_data + '\n')
        time.sleep(0.33) # 3Hz max
        i =+ 1
except KeyboardInterrupt:
    print("\nShutting down")

output_file.close()
print('Finished program, log is in ' + file_path)
