#!/usr/bin/python

import pygame
import os
import subprocess
from time import sleep
import RPi.GPIO as GPIO
import Decoder

# Colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)

# Buttons (GPIO pins)
WIFI = 17
RECORDER = 22
LIVEREAD = 23
SHUTDOWN = 27

# BUTTON INPUTS
button_map = {
    WIFI: {    'color': BLUE, 'text': 'Restarting WiFi',     'os_cmd': 'sudo service hostapd restart'},
    RECORDER: {'color': GREY, 'text': 'Restarting Recorder', 'os_cmd': '/var/www/bin/kill_recorder.sh'},
    LIVEREAD: {'color': GREEN,'text': 'Toggling Live Read',  'action': 'toggle'},
    SHUTDOWN: {'color': RED,  'text': 'Shutdown; wait 10s',  'os_cmd': 'sleep 3; /var/www/bin/screen_off_and_shutdown.sh'}
}
options_map = {  # key is the vertical position
    40: '    Restart WiFi ->',
    100: 'Restart Recorder ->',
    160: 'Toggle Live Read ->',
    220: 'Shutdown picklePi->'
}


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


def paint_row(text, row_center):
    text_surface = font_36.render(text, True, BLACK)
    rect = text_surface.get_rect(center=(160, row_center))
    lcd.blit(text_surface, rect)


def paint_row_with_font(text, font, row_center):
    text_surface = font.render(text, True, BLACK)
    rect = text_surface.get_rect(center=(160, row_center))
    lcd.blit(text_surface, rect)


# try to be independent of the PickleRecorder, just tail its output file.
#  The raw file has 29 elements separated by commas
def show_live_reading():
    try:
        # grab the voltages, etc.
        raw_data_line = subprocess.check_output(
            'tail -1 /var/www/html/data/current', shell=True)
        # Decoder returns 15 values we can show
        (mph, fRpm, rRpm, afr, man, ftemp, fpress, lrh, rrh, utc,
         rpm, egt1, egt2, egt3, egt4) = Decoder.get_readings(raw_data_line).split(',')

        lcd.fill(CYAN)
        # we have six rows, in 240 pixels total.
        row_increment = 36
        row_center = row_increment  # the offset from the top of the display

        row1 = ' MPH: ' + str(mph) + '    RPM: ' + str(rpm) + ' '
        row2 = ' AFR: ' + str(afr) + '    MAP: ' + str(man) + ' '
        row3 = ' FWHL: ' + str(fRpm) + '    RWHL: ' + str(rRpm) + ' '
        row4 = ' FTMP: ' + str(ftemp) + '    FPRS: ' + str(fpress) + ' '
        row5 = ' EGT1  EGT2  EGT3  EGT4 '
        row6 = ' ' + str(egt1) + '    ' + str(egt2) + '    ' + str(egt3) + '    ' + str(egt4) + ' '

        paint_row(row1, row_center)
        row_center = row_center + row_increment
        paint_row(row2, row_center)
        row_center = row_center + row_increment
        paint_row(row3, row_center)
        row_center = row_center + row_increment
        paint_row(row4, row_center)
        row_center = row_center + row_increment + 2
        paint_row_with_font(row5, font_33, row_center)
        row_center = row_center + row_increment - 4
        paint_row(row6, row_center)

        lcd.blit(pygame.transform.rotate(lcd, 180), (0, 0))
        pygame.display.update()

    except Exception as e:  # might be anything...
        print('Error in fetch_reading: ' + str(e))


# show the startup
def show_options():
    lcd.fill(WHITE)
    for (VERT_CENTER, MESSAGE) in options_map.items():
        text_surface = font_30.render('%s' % MESSAGE, True, BLACK)
        rect = text_surface.get_rect(center=(160, VERT_CENTER))
        lcd.blit(text_surface, rect)
    lcd.blit(pygame.transform.rotate(lcd, 180), (0, 0))
    pygame.display.update()


# # # MAIN # # #
# hookup the display for output
print('initing pygame display')
os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()
pygame.mouse.set_visible(False)
font_30 = pygame.font.Font(None, 30)
font_33 = pygame.font.Font(None, 33)
font_36 = pygame.font.Font(None, 36)
font_40 = pygame.font.Font(None, 40)
font_50 = pygame.font.Font(None, 50)
font_60 = pygame.font.Font(None, 60)
lcd = pygame.display.set_mode((320, 240))
lcd.fill(BLACK)
pygame.display.update()
print('pygame display set')

# Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
GPIO.setmode(GPIO.BCM)
print(GPIO.RPI_INFO)
for k in button_map.keys():
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# start out with reading disabled
get_live_reading = False

# initial display
show_options()

# loop indefinitely
while True:
    try:
        button_pressed = False
        # Scan the buttons
        for (BUTTON, DICT) in button_map.items():
            if GPIO.input(BUTTON) == False:  # when the button is down, its value is False
                button_pressed = True
                lcd.fill(DICT['color'])
                words = DICT['text']
                text_surface = font_40.render('%s' % words, True, WHITE)
                rect = text_surface.get_rect(center=(160, 120))
                lcd.blit(text_surface, rect)
                lcd.blit(pygame.transform.rotate(lcd, 180), (0, 0))
                pygame.display.update()

                if 'os_cmd' in DICT:
                    os.system(DICT['os_cmd'])
                    if BUTTON == SHUTDOWN:
                        quit()  # keeps us from re-drawing the options screen
                else:
                    ctl_reading(DICT['action'])
                sleep(1.1)

        if not button_pressed:
            if get_live_reading:
                show_live_reading()
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
