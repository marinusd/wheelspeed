#!/bin/bash

kill -SIGINT $(</var/run/PickleDisplay.pid)
cat /var/log/PickleDisplay.log

