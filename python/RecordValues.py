#!/usr/bin/env python3

#  version 2018-05-13
# Basic approach for reporting: store all readings as strings in a postgres table
#  Write a logfile with the raw values (no processing here)
from datetime import datetime
import time
import serial  #  pip3 install pyserial
import gpsd    #  pip3 install gpsd-py3 https://github.com/MartijnBraam/gpsd-py3

# this prints a header every 20 lines
tuning = True

now = datetime.now()
file_path = '/home/pi/datalogs/' + now.strftime('%Y-%m-%d.%H:%M') + '.csv'
nano = 0 # this will be a serial connection
micros_per_minute = 1000000  # microseconds
analog_factor = 0.0048828125  # 0 = 0V, 512 = 2.5V, 1024 = 5V
sql_string = """INSERT INTO run_data (
    front_rpm,rear_rpm,
    lrh,rrh,
    ft,fp,gp,
    afr,man,egt,
    lat,lon,alt,mph,utc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""

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

def write_raw_data_to_log(raw_nano_data,gps_data):
    global output_file
    output_file.write(raw_nano_data + ',' + gps_data + '\n')

def store_values_in_db(gps_data,nano_data):
    sql_string = "INSERT INTO domes_hundred (name,name_slug,status) VALUES (%s,%s,%s) RETURNING id;"
    cursor.execute(sql_string, (hundred_name, hundred_slug, status))
    hundred = cursor.fetchone()[0]

def store_values_in_db(gps_data,raw_nano_data):
    (lat,lon,alt,mph,utc) = gps_data.split(',')
    # cook the nano data
    (millis,
    frontCount,deltaFrontCount,deltaFrontMicros,
    rearCount,deltaRearCount,deltaRearMicros,
    rawLeftRideHeight,rawRightRideHeight,
    rawFuelPressure,rawFuelTemperature,
    rawGearPosition,rawAirFuelRatio,
    rawManifoldAbsolutePressure,rawExhaustGasTemperature
    ) = raw_nano_data.split(',')
    # calcs and transforms
    front_rpm = get_axle_rpm(deltaFrontCount,deltaFrontMicros)
    rear_rpm  = get_axle_rpm(deltaRearCount,deltaRearMicros)
    lrh = get_ride_height(rawLeftRideHeight)
    rrh = get_ride_height(rawRightRideHeight)
    fp  = get_fuel_pressure(rawFuelPressure)
    ft  = get_fuel_temperature(rawFuelTemperature)
    gp  = get_gear_position(rawGearPosition)
    afr = get_afr(rawAirFuelRatio)
    man = get_man_abs_pressure(rawManifoldAbsolutePressure)
    egt = get_egt(rawExhaustGasTemperature)

    # we have all the values
    sql_string = "INSERT INTO run_data (name,name_slug,status) VALUES (%s,%s,%s);"
    cursor.execute(sql_string, (hundred_name, hundred_slug, status))

    return (front_rpm + ',' +
             rear_rpm + ',' +
                  lrh + ',' +
                  rrh + ',' +
                   ft + ',' +
                   fp + ',' +
                   gp + ',' +
                  afr + ',' +
                  man + ',' +
                  egt
            )

def write_header_to_file():
    global nano
    global output_file
    nano.write(str('h').encode())
    nano_header = nano.readline().decode('ascii').rstrip()
    gps_header = 'latitude,longitude,altitudeFt,mph,utc'
    output_file.write(nano_header + ',' + gps_header + '\n')

##### MAIN MAIN MAIN ###################################
init_nano()
init_gps()

output_file = open(file_path,'w')
write_header_to_file()
print('Writing log to ' + file_path)

print('Starting data collection loop... Ctrl-C to stop loop')
try:
    i = 0
    while True:
        #if (i % 20 == 0 and tuning):
        #    write_header_to_file()
        raw_nano_data = get_nano_data()
        gps_data = get_gps_data()
        write_raw_data_to_log(raw_nano_data,gps_data)



        time.sleep(0.33) # 3Hz max
        i =+ 1
except KeyboardInterrupt:
    print("\nShutting down")

output_file.close()
print('Finished program, log is in ' + file_path)
