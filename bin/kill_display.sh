#!/bin/bash

sudo kill -SIGINT $(</var/run/PickleDisplay.pid)
sudo kill -SIGKILL $(</var/run/PickleDisplay.pid)
cat /var/log/PickleDisplay.log

