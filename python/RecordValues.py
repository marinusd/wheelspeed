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
