#!/bin/bash

sudo kill -SIGINT $(</var/run/PickleRecorder.pid)
sudo kill -SIGINT $(</var/run/PickleRecorder.pid)
sudo kill -SIGKILL $(</var/run/PickleRecorder.pid)
cat /var/log/pickle/PickleRecorder.log

