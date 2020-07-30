#!/bin/bash

sudo kill -SIGINT $(</var/run/PickleDisplay.pid)
cat /var/log/PickleDisplay.log

