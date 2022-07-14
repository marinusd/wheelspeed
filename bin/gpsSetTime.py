#!/usr/bin/python3
import os
import sys
import time
from gpsd import *

print('Set System Clock to GPS UTC time')

try:
  gps = gpsd(mode=WATCH_ENABLE)
except:
  print('ERROR: No GPS Present, time not set!!')
  sys.exit()

while True:
  #wait until the next GPSD time tick
  gps.next()
  if gps.utc != None and gpsd.utc != '':
    #gpsd.utc is formatted like"2015-04-01T17:32:04.000Z"
    #convert it to a form the date -u command will accept: "20140401 17:32:04"
    #use python slice notation [start:end] (where end desired end char + 1)
    #   gpsd.utc[0:4] is "2015"
    #   gpsd.utc[5:7] is "04"
    #   gpsd.utc[8:10] is "01"
    gpsutc = gps.utc[0:4]+gps.utc[5:7]+gps.utc[8:10]+' '+gps.utc[11:19]
    os.system('sudo date -u --set="%s"' % gpsutc)
    sys.exit()
