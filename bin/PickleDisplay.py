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
GREEN = (0,255,0)
BLUE = (0,0,255)

raw_file = '/var/www/html/data/current'
reading_flag = '/var/www/bin/reading'

## BUTTON INPUT
color_map = {
  17:GREY,
  22:GREEN, 
  23:RED, 
  27:BLUE} 
text_map = {
  17:"Restarting Recorder", 
  22:"Starting Live Read", 
  23:"Stopping Live Read", 
  27:"Switching Read Source"}
cmd_map = {
  17:'/var/www/bin/kill_recorder.sh',
  22:'echo AFR >'+reading_flag,
  23:'rm -f '+reading_flag,
  27:'echo MAP >'+reading_flag}
print_options_map = { # key is the vertical position
  40:"Restart Recorder->", 
 100:"Start Live Read->", 
 160:"Stop Live Read->", 
 220:"Switch Read Source->"}

#Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
GPIO.setmode(GPIO.BCM)
print(GPIO.RPI_INFO)

for k in color_map.keys():
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
  for (VERT_CENTER,MESSAGE) in print_options_map.items():
    text_surface = font_30.render('%s'%MESSAGE, True, BLACK)
    rect = text_surface.get_rect(center=(160,VERT_CENTER))
    lcd.blit(text_surface, rect)
    pygame.display.update()

show_options()
try:
  while True:
    button_pressed = False
    # Scan the buttons
    for (BUTTON,COLOR) in color_map.items():
      if GPIO.input(BUTTON) == False:
        button_pressed = True
        lcd.fill(COLOR)
        words = text_map[BUTTON]
        text_surface = font_big.render('%s'%words, True, WHITE)
        rect = text_surface.get_rect(center=(160,120))
        lcd.blit(text_surface, rect)
        pygame.display.update()
        os.system(cmd_map[BUTTON])
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
