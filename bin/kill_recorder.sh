#!/bin/bash

kill -SIGINT $(</var/run/RecordValues.pid)
cat /var/log/RecordValues.log

