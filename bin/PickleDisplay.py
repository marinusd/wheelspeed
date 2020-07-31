#!/usr/bin/python

import pygame
import os
from time import sleep
import RPi.GPIO as GPIO

#Colours
BLACK = (0,0,0)
WHITE = (255,255,255)
GREY = (128,128,128)
RED = (255,0,0)
GREEN = (0,200,0)
BLUE = (0,0,255)

raw_file = '/var/www/html/data/current'
reading_flag = '/var/www/bin/reading'
if os.path.isfile(reading_flag):
  os.remove(reading_flag)

## BUTTON INPUT
button_map = {
  17:{'color':GREY, 'text':'Restarting Recorder',  'os_cmd':'/var/www/bin/kill_recorder.sh'},
  22:{'color':GREEN,'text':'Starting Live Read',   'action':'start'},
  23:{'color':RED,  'text':'Stopping Live Read',   'action':'stop'},
  27:{'color':BLUE, 'text':'Switching Read Source','action':'switch'}
} 
options_map = { # key is the vertical position
  40:'Restart Recorder->', 
 100:'Start Live Read->', 
 160:'Stop Live Read->', 
 220:'Switch Read Source->'
}
reading_map = {'AFR':4,'MAP':5,'FP':6,'fRPM':7,'rRPM':9}
def next_reading(key):
  next = False
  for k,v in reading_map.items():
   if next:
     return v
   if k==key:
     next = True

#Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
GPIO.setmode(GPIO.BCM)
print(GPIO.RPI_INFO)

for k in button_map.keys():
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# hookup the display for output
print('initing pygame display')
os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()
pygame.mouse.set_visible(False)
font_30 = pygame.font.Font(None, 30)
font_big = pygame.font.Font(None, 40)
lcd = pygame.display.set_mode((320, 240))
lcd.fill(BLACK)
pygame.display.update()
print('pygame display set')

# show the startup
def show_options():
  lcd.fill(WHITE)
  for (VERT_CENTER,MESSAGE) in options_map.items():
    text_surface = font_30.render('%s'%MESSAGE, True, BLACK)
    rect = text_surface.get_rect(center=(160,VERT_CENTER))
    lcd.blit(text_surface, rect)
    pygame.display.update()

show_options()
try:
  while True:
    button_pressed = False
    # Scan the buttons
    for (BUTTON,DICT) in button_map.items():
      if GPIO.input(BUTTON) == False:
        button_pressed = True
        lcd.fill(DICT['color'])
        words = DICT['text']
        text_surface = font_big.render('%s'%words, True, WHITE)
        rect = text_surface.get_rect(center=(160,120))
        lcd.blit(text_surface, rect)
        pygame.display.update()
        if 'os_cmd' in DICT:
	  os.system(DICT['os_cmd'])
        else:
	  action = DICT['action']
          print('Action: ' + action)
        sleep(3)
    if not button_pressed:
      show_options()
    sleep(0.2)

except KeyboardInterrupt:
    print("Quitting on Ctrl-C")
except Exception as e:
    print('Exception in display loop: ' + str(e))
finally:
    GPIO.cleanup()
