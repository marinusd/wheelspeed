#!/usr/bin/python3

#  version 2021-08-02
#  We write a STATUS file and a POSITION on a ramdisk
#   STATUS is writen every time a message comes in, POSITION only if the message
#   is a 'TPV'.
#
from datetime import datetime
import time
import os
import gps

# constants
data_dir = '/mnt/ramdisk/'
gps_header = 'latitude,longitude,altitudeFt,mph,utc'

# start files
POSITION = open(data_dir + 'POSITION', mode='w')
POSITION.write("0.0,0.0,0,0,unknown\n") 
POSITION.close()

STATUS   = open(data_dir + 'STATUS',   mode='w')
timestamp = datetime.now().strftime('%s.%f')[:-3]
STATUS.write("Starting at: " + timestamp + "\n")
STATUS.close()


# hook up to the daemon, will probably die if it's not up
def get_session():
  while True:
    try:
      timestamp = datetime.now().strftime('%s.%f')[:-3]
      print(timestamp + ": Attempting to connect to GPSD")
      session = gps.gps("localhost", "2947")
      session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
      break
    except:
      time.sleep(0.4)
  return session

# grab the gpsd handle
session = get_session()

# wait for new messages and process each
while True:
  try:
    lat = lon = alt = mph = utc = 0
    report = session.next()
    # update POSITION if we have a new TPV
    if report['class'] == 'TPV':
      if hasattr(report, 'lat'):
        lat = str(report['lat'])
      if hasattr(report, 'lon'):
        lon = str(report['lon'])
      if hasattr(report, 'alt'):
        alt = str(report['alt'] * 3.2808399) # alt in meters, we use feet
      if hasattr(report, 'speed'):
        mph = str(report['speed'] * gps.MPS_TO_MPH)
      if hasattr(report, 'time'):
        utc = str(report['time'])
      POSITION = open(data_dir + 'POSITION', mode='w')
      POSITION.write(lat + ',' + lon + ',' + alt + ',' + mph + ',' + utc + "\n")
      POSITION.close()

    STATUS = open(data_dir + 'STATUS',   mode='w')
    timestamp = datetime.now().strftime('%s.%f')[:-3]
    STATUS.write(timestamp + ": " + report['class'] + "\n")
    STATUS.close

  except KeyError:
    pass
  except KeyboardInterrupt:
    quit()
  except StopIteration:
    print("GPSD has terminated")
    session = get_session()
  except Exception as e:
    print("exception in main loop: " + str(e))      
    

