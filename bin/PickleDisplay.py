#!/usr/bin/python

import pygame
import os
import subprocess
from time import sleep
import RPi.GPIO as GPIO
import Decoder

#Colours
BLACK = (0,0,0)
WHITE = (255,255,255)
GREY = (128,128,128)
RED = (255,0,0)
GREEN = (0,200,0)
BLUE = (0,0,255)
CYAN = (0,255,255)

# hookup the display for output
print('initing pygame display')
os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()
pygame.mouse.set_visible(False)
font_30 = pygame.font.Font(None, 30)
font_33 = pygame.font.Font(None, 33)
font_40 = pygame.font.Font(None, 40)
font_50 = pygame.font.Font(None, 50)
font_60 = pygame.font.Font(None, 60)
lcd = pygame.display.set_mode((320, 240))
lcd.fill(BLACK)
pygame.display.update()
print('pygame display set')


# start out with reading disabled
get_live_reading = False
# try to be independent of the PickleRecorder, just tail its output file.
def fetch_reading():
  readings_map = {}
  try:
    raw_data_line = subprocess.check_output('tail -1 /var/www/html/data/current', shell=True)
    (mph,fRpm,rRpm,afr,map,ftemp,fpress,lrh,rrh,utc) = Decoder.get_readings(raw_data_line).split(',')
    readings_map = {'GPS MPH':mph,
	'Front Wheel RPM':fRpm,
	'Rear Wheel RPM':rRpm,
	'A/F Ratio':afr,
	'MAP':map,
	'Fuel Pressure':fpress,
	'Fuel Temp':ftemp
	}
  except Exception as e: # might be anything...
    print('Error in fetch_reading: ' + str(e))
  return readings_map

def ctl_reading(action):  # 'toggle' is the only action value
  global get_live_reading
  try:
    if get_live_reading:
      os.system('rm -f /var/www/html/data/live_readings')
      get_live_reading = False
    else:
      os.system('touch /var/www/html/data/live_readings')
      get_live_reading = True
  except:
    print('ctl_reading: error... of some sort')

def show_live_reading():
  lcd.fill(CYAN)
  readings_map = fetch_reading()
  # we have seven readings, and 240 pixels total. 
  row_increment = 33
  row_center = 20 ## the offset from the top of the display
  for name,value in readings_map.items():
    text_surface = font_33.render('%s'%name, True, BLACK)
    rect = text_surface.get_rect(center=(120,row_center))
    lcd.blit(text_surface, rect)
    text_surface = font_33.render('%s'%value, True, BLACK)
    rect = text_surface.get_rect(center=(280,row_center))
    lcd.blit(text_surface, rect)
    row_center = row_center + row_increment
  lcd.blit(pygame.transform.rotate(lcd,180),(0,0))
  pygame.display.update()

# show the startup
def show_options():
  lcd.fill(WHITE)
  for (VERT_CENTER,MESSAGE) in options_map.items():
    text_surface = font_30.render('%s'%MESSAGE, True, BLACK)
    rect = text_surface.get_rect(center=(160,VERT_CENTER))
    lcd.blit(text_surface, rect)
  lcd.blit(pygame.transform.rotate(lcd,180),(0,0))
  pygame.display.update()

## BUTTON INPUT
button_map = {
  17:{'color':BLUE, 'text':'Restarting WiFi',      'os_cmd':'sudo service hostapd restart'},
  22:{'color':GREY, 'text':'Restarting Recorder',  'os_cmd':'/var/www/bin/kill_recorder.sh'},
  23:{'color':GREEN,'text':'Toggling Live Read',   'action':'toggle'},
  27:{'color':RED,  'text':'Shutting Down Now',    'os_cmd':'sudo shutdown -h now'}
} 
options_map = { # key is the vertical position
  40:'    Restart WiFi ->',
 100:'Restart Recorder ->',
 160:'Toggle Live Read ->',
 220:'Shutdown picklePi->'
}

  
# # # MAIN # # # 
#Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
GPIO.setmode(GPIO.BCM)
print(GPIO.RPI_INFO)
for k in button_map.keys():
  GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# initial display
show_options()

# loop indefinitely
while True:
  try:
    button_pressed = False
    # Scan the buttons
    for (BUTTON,DICT) in button_map.items():
      if GPIO.input(BUTTON) == False:
        button_pressed = True
        lcd.fill(DICT['color'])
        words = DICT['text']
        text_surface = font_40.render('%s'%words, True, WHITE)
        rect = text_surface.get_rect(center=(160,120))
        lcd.blit(text_surface, rect)
        lcd.blit(pygame.transform.rotate(lcd,180),(0,0))
        pygame.display.update()
        if 'os_cmd' in DICT:
          os.system(DICT['os_cmd'])
        else:
          ctl_reading(DICT['action'])
        sleep(1.1)
    if not button_pressed:
      if get_live_reading:
        show_live_reading()
        sleep(0.2)
      else:
        show_options()
        sleep(0.2)

  except KeyboardInterrupt:
    print("Quitting on Ctrl-C")
    break
  except Exception as e:
    print('Exception in display loop: ' + str(e))

# last act of a desperate program
GPIO.cleanup()

