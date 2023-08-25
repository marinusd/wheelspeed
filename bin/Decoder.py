#!/usr/bin/env python3

#  version 2022-08-13
from datetime import datetime
import time
import sys
import os

# constants
micros_per_minute = 1000000 * 60  # microseconds
analog_factor = 0.004887585      # 0 = 0V, 512 = ~2.5V, 1023 = 5V


def get_axle_rpm(pulseCount, elapsedMicros):
    # one magnet per wheel means one pulse per revolution
    rpm = 0
    if pulseCount > 0:
        # each pulse took, on average
        average_pulse_micros = (elapsedMicros / pulseCount)
        rpm = micros_per_minute / average_pulse_micros
    return str(int(rpm))  # int throws away the fraction


def get_engine_rpm(pulseCount, elapsedMicros):
    # one pulse per cam rotation means two crank revolutions
    doublePulseCount = pulseCount * 2
    rpm = 0
    if doublePulseCount > 0:
        # each pulse-pair took, on average, this many ms
        average_double_pulse_micros = (elapsedMicros / doublePulseCount)
        rpm = micros_per_minute / average_double_pulse_micros
    return str(int(rpm))  # int throws away the fraction

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

# the EGT controller gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_egt(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    egt = (250 * voltage)  # reveltronics
    return str(int(egt))

# the NTK controller gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_afr(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    afr = (1.4 * voltage) + 9   # according to the NTK doc, 0V = 9.0, 5V = 16.0
    (whole, fraction) = str(afr).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

# the MAP gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_map(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage

    # Option One:  # https://www.robietherobot.com/storm/mapsensor.htm
    # psi = (voltage * 8.94) - 14.53

    # Option Two: From DIYautotune, calibration GM 3-bar ... Datasheet: 1.1kPa = 0V,  315.50kPa = 5V (linear)
    #   pinValueRef: range is: 315.5 - 1.1 = 314.4, divide the range by the number of pin values above zero: 314.4/1023  = .307331 per click
    # kpa = (.307331 * pinValue) + 1.1
    #   voltageRef: range is: 315.5 - 1.1 = 314.4, divide the range by the max volts: 314.4/5  = 62.88000
    kpa = (62.88 * voltage) + 2.1

    # Option Three: calibration of GM 3-bar, Ballenger Motorsports  https://www.bmotorsports.com/shop/product_info.php/cPath/129_143/products_id/1584?osCsid=dp41bpdfqtmg2habab5h8d3nh3
    #               V = 0.0162 * P - 0.0179
    #     algebra   P = (0.0179 + V) / 0.0162
    # kpa = (voltage + 0.0179) / 0.0162

    psi = kpa * 0.145038 # google says so
    #print("MAP pin: " + str(pinValue) + " V: " + str(voltage) + " kpa: " + str(kpa) + " psi: " + str(psi))
    (whole, fraction) = str(psi).split('.')
    map_val = whole + '.' + fraction[:1]  # return one fractional digit
    return map_val

# the ACT sensor gives a voltage from 0V-5V; the arduino turns that into a int between 0-1023
def get_act(pinValue):
    voltage = pinValue * analog_factor  # convert from 10bits to voltage
    # we linearize that (though it's actually a curve) with two points and a fixed 3077 ohm R1 in a voltage divider
    # Ballenger chart says: 0C=9256 ohms, 35C=1778 ohms, that's 32F=9256, 95F=1778, 32F=3.753V, 95F=1.831V
    # 63 degrees cover 1.922 volts, so .03051 volts per degree is the increment
    act = (voltage / -.03051) + 155 # it's inverse, so we multiply by the inverse of the increment
    (whole, fraction) = str(act).split('.')
    return whole + '.' + fraction[:1]  # return one fractional digit

def get_readings(raw_data):   # fed 30 elements, returns 16 elements
    mph = fRpm = rRpm = afr = man = ft = fp = lrh = rrh = utc = '0'
    rpm = egt1 = egt2 = egt3 = egt4 = act = '0'
    try:
        # cook the raw data
        (timestamp, millis,
         frontCount, deltaFrontCount, deltaFrontMicros,
         rearCount, deltaRearCount, deltaRearMicros,
         rawLeftRideHeight, rawRightRideHeight,
         rawFuelPressure, rawFuelTemperature,
         rawGearPosition, rawAirFuelRatio,
         rawManifoldAbsolutePressure, rawExhaustGasTemperature,
         millis2,
         camPositionCount, deltaCamPositionCount, deltaCamPositionMicros,
         rawEGT1, rawEGT2, rawEGT3, rawEGT4, rawACT,
         lat, lon, alt, mph, utc) = raw_data.split(',')

        # calcs and transforms
        fRpm = get_axle_rpm(int(deltaFrontCount), int(deltaFrontMicros))
        rRpm = get_axle_rpm(int(deltaRearCount), int(deltaRearMicros))
        afr = get_afr(int(rawAirFuelRatio))
        man = get_map(int(rawManifoldAbsolutePressure))
        ft = get_fuel_temperature(int(rawFuelTemperature))
        fp = get_fuel_pressure(int(rawFuelPressure))
        lrh = get_ride_height(int(rawLeftRideHeight))
        rrh = get_ride_height(int(rawRightRideHeight))
        rpm = get_engine_rpm(int(deltaCamPositionCount), int(deltaCamPositionMicros))
        egt1 = get_egt(int(rawEGT1))
        egt2 = get_egt(int(rawEGT2))
        egt3 = get_egt(int(rawEGT3))
        egt4 = get_egt(int(rawEGT4))
        act  = get_act(int(rawACT))
    except Exception as e:
        print("exception in Decode:get_readings: " + str(e))
        print("RawData: " + raw_data)

    #returnCols = 'mph,fRpm,rRpm,afr,man,ftemp,fpress,lrh,rrh,utc,rpm,egt1,egt2,egt3,egt4,act'
    return (mph + ',' + fRpm + ',' + rRpm + ','
            + afr + ',' + man + ','
            + ft + ',' + fp + ','
            + lrh + ',' + rrh + ','
            + utc + ',' + rpm + ','
            + egt1 + ',' + egt2 + ','
            + egt3 + ',' + egt4 + ','
            + act
            )


# # # # #  MAIN # # # #
if __name__ == "__main__":
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
    data_file_path = raw_file_path.replace('raw', 'data')

    try:
        with open(raw_file_path, 'r') as raw_file:
            with open(data_file_path, 'w') as data_file:
                data_file.write('mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc,rpm,egt1,egt2,egt3,egt4,act\n')
                for line in raw_file:
                    if line.startswith('1'):  # all epoch times will
                        data_file.write(get_readings(line.rstrip()) + '\n')
        print('Wrote data file to: ' + data_file_path)

    except Exception as e:
        print('Exception in main loop: ' + str(e))
        sys.exit()
    except:
        print('Some non-Exception problem in main loop')
