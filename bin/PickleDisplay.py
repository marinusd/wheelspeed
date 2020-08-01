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
font_40 = pygame.font.Font(None, 40)
font_60 = pygame.font.Font(None, 60)
lcd = pygame.display.set_mode((320, 240))
lcd.fill(BLACK)
pygame.display.update()
print('pygame display set')


# start out with reading disabled
get_live_reading = False
readings = ['AFR','MAP','FP','fRpm','rRpm','mph']
reading = 'AFR'
# for 'live values', be able to walk through the possible signals.
def switch_reading():
  global reading
  index = readings.index(reading)
  index = index + 1
  if index >= len(readings):
    index = 0
  reading = readings[index]

# try to be independent of the PickleRecorder, just tail its output file.
def fetch_reading():
  value = '?!'
  try:
    raw_data_line = subprocess.check_output('tail -1 /var/www/html/data/current', shell=True)
    value = Decoder.get_reading(raw_data_line, reading)
  except Exception as e: # might be anything...
    print('Error in fetch_reading: ' + str(e))
  return value

def ctl_reading(action):
  global get_live_reading
  try:
    if action == 'start':
      os.system('touch /var/www/html/data/live_readings')
      get_live_reading = True
    elif action == 'stop':
      os.system('rm -f /var/www/html/data/live_readings')
      get_live_reading = False
    elif action == 'switch':
      switch_reading()
    else:
      pass
  except:
    print('ctl_reading: error... of some sort')
def show_live_reading():
  lcd.fill(CYAN)
  # first the header
  text_surface = font_60.render('%s'%reading, True, BLACK)
  rect = text_surface.get_rect(center=(160,80))
  lcd.blit(text_surface, rect)
  pygame.display.update()
  # then the value
  words = fetch_reading()
  text_surface = font_60.render('%s'%words, True, BLACK)
  rect = text_surface.get_rect(center=(160,160))
  lcd.blit(text_surface, rect)
  pygame.display.update()


# show the startup
def show_options():
  lcd.fill(WHITE)
  for (VERT_CENTER,MESSAGE) in options_map.items():
    text_surface = font_30.render('%s'%MESSAGE, True, BLACK)
    rect = text_surface.get_rect(center=(160,VERT_CENTER))
    lcd.blit(text_surface, rect)
    pygame.display.update()

## BUTTON INPUT
button_map = {
  17:{'color':GREY, 'text':'Restarting Recorder',  'os_cmd':'/var/www/bin/kill_recorder.sh'},
  22:{'color':GREEN,'text':'Starting Live Read',   'action':'start'},
  23:{'color':RED,  'text':'Stopping Live Read',   'action':'stop'},
  27:{'color':BLUE, 'text':'Switching Read Signal','action':'switch'}
} 
options_map = { # key is the vertical position
  40:'Restart Recorder->', 
 100:'Start Live Read->', 
 160:'Stop Live Read->', 
 220:'Switch Read Signal->'
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
        pygame.display.update()
        if 'os_cmd' in DICT:
	  os.system(DICT['os_cmd'])
        else:
          action = DICT['action']
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

