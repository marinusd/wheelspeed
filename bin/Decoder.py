#!/usr/bin/env python3

#  version 2020-07-31
from datetime import datetime
import time
import sys
import os

# constants
micros_per_minute = 1000000 * 60 # microseconds
analog_factor = 0.004887585  # 0 = 0V, 512 = ~2.5V, 1023 = 5V

def get_axle_rpm(pulseCount,elapsedMicros):
    # one magnet per wheel means one pulse per revolution
    pulses_per_minute = 0
    if pulseCount > 0:
        average_pulse_micros = (elapsedMicros / pulseCount)  # each pulse took, on average
        pulses_per_minute = micros_per_minute / average_pulse_micros
    return str(int(pulses_per_minute)) # int throws away the fraction

# linear potentiometers give a voltage between 0V-3.3V;
#   arduino encodes to an int 0-1023; and we want a range 0..100
# The ride height sensor readings go DOWN as the accordion units are extended
#  and the readings go UP as the units are compressed, so we must invert.
def get_ride_height(pinValue):
    return str(int(100 - (pinValue * 100 / 1023)))

# VDO 10-bar pressure sensor has resistance between 8ohms and 180ohms
#  A voltage divider circuit gives between about 1.6V and 4.8V to the arduino
#  arduino encodes to an int 0-1023; we will not see the min/max values
#  when pressure is high, voltage is low; so invert (and normalize to 0-100)
def get_fuel_pressure(pinValue):
    return str(int(100 - (pinValue * 100 / 1023)))

# temp sensor resistance is between 3200 and 12 ohms
#  Resistance decreases with increasing temperature
#  The voltage divider circuit converts the resistance to a voltage between about
#   1.6V (low) and 4.9V (high)
#  The arduino will report that voltage as an int between 0-1023
def get_fuel_temperature(pinValue):
    return str(int(pinValue * 100 / 1023))

# the NTK gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_afr(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    afr = (1.4 * voltage) + 9   # according to the NTK doc, 0V = 9.0, 5V = 16.0
    (whole,fraction) = str(afr).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

# the MAP gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_map(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    # calibration... userReport:      11kPa = 0.25V, 307kPa = 4.75V
      # y = 65.7778 x - 5.44444
    # calibration... Motec Datasheet: 20kPa = 0.4V,  300kPa = 4.65V
      # y = 65.8824 x - 6.35294
    kpa = (65.83 * voltage) - 5.8986   # (averaged)
    psi = kpa * 0.145038 # google says so
    #print("MAP pin: " + str(pinValue) + " V: " + str(voltage) + " kpa: " + str(kpa) + " psi: " + str(psi))
    (whole,fraction) = str(psi).split('.')
    map_val = whole + '.' + fraction[:1]  # return one fractional digit
    return map_val

def get_readings(raw_data):
    mph = fRpm = rRpm = afr = man = ft = fp = lrh = rrh = utc = '0'
    try:
      # cook the raw data
      (timestamp,millis,
      frontCount,deltaFrontCount,deltaFrontMicros,
      rearCount,deltaRearCount,deltaRearMicros,
      rawLeftRideHeight,rawRightRideHeight,
      rawFuelPressure,rawFuelTemperature,
      rawGearPosition,rawAirFuelRatio,
      rawManifoldAbsolutePressure,rawExhaustGasTemperature,
      lat,lon,alt,mph,utc) = raw_data.split(',')

      # calcs and transforms
      fRpm = get_axle_rpm(int(deltaFrontCount),int(deltaFrontMicros))
      rRpm = get_axle_rpm(int(deltaRearCount),int(deltaRearMicros))
      afr = get_afr(int(rawAirFuelRatio))
      man = get_map(int(rawManifoldAbsolutePressure))
      ft  = get_fuel_temperature(int(rawFuelTemperature))
      fp  = get_fuel_pressure(int(rawFuelPressure))
      lrh = get_ride_height(int(rawLeftRideHeight))
      rrh = get_ride_height(int(rawRightRideHeight))
      #gp  = get_gear_position(int(rawGearPosition))
      #egt = get_egt(int(rawExhaustGasTemperature))
    except Exception as e:
        print("exception in Decode:get_readings: " + str(e))

    #returnCols = 'mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc'
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

def get_reading(raw_data, column):
  (mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc) = get_readings(raw_data)
  readings = {'fRpm': fRpm, 'rRpm': rRpm, 'AFR': afr, 'MAP': map, 'FP': fpress}
  return readings[column]



# # # # #  MAIN # # # # 
if len(sys.argv) != 2:
  print('Error: supply path to raw file')
  sys.exit()
raw_file_path = sys.argv[1]
if not os.path.isfile(raw_file_path):
  print('Error: file not found at ' + raw_file_path)
  sys.exit()
if not 'raw' in raw_file_path:
  print("Error: filename must have 'raw' in it. NoGood: " + raw_file_path)
  sys.exit()
data_file_path = raw_file_path.replace('raw','data')

try:
  with open(raw_file_path, 'r') as raw_file:
    with open(data_file_path, 'w') as data_file:
      data_file.write('mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc\n')
      for line in raw_file:
        if line.startswith('1'): # all epoch times will
          data_file.write(get_readings(line)) 
  print('Wrote data file to: ' + data_file_path)

except Exception as e:
  print('Exception in main loop: ' + str(e))
  sys.exit()
except:
  print('Some non-Exception problem in main loop')

