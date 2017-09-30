#!/bin/bash

tty=tty.usbmodem1421

java -Dioio.SerialPorts=/dev/$tty -jar dist/WheelSpeedJava.jar
