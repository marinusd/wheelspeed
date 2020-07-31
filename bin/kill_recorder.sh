#!/bin/bash

sudo kill -SIGINT $(</var/run/PickleRecorder.pid)
cat /var/log/PickleRecorder.log

