#!/bin/bash

sudo kill -SIGINT $(</var/run/RecordValues.pid)
cat /var/log/RecordValues.log

