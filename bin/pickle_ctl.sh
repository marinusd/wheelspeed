#!/bin/bash

PATH=/sbin:/bin:/usr/sbin:/usr/bin

. /lib/lsb/init-functions

DAEMON=/var/www/python/RecordValues.py
PIDFILE=/var/run/RecordValues.pid

test -x $DAEMON || exit 5

case $1 in
    start)
        log_daemon_msg "Starting RecordValues server" "RecordValues"
        start-stop-daemon --start --quiet --oknodo --pidfile $PIDFILE --startas $DAEMON --
        status=$?
        log_end_msg $status
        ;;
    stop)
        log_daemon_msg "Stopping RecordValues server" "RecordValues"
        start-stop-daemon --stop --quiet --oknodo --pidfile $PIDFILE
        log_end_msg $?
        rm -f $PIDFILE
        ;;
    restart|force-reload)
        $0 stop && sleep 2 && $0 start
        ;;
    status)
        status_of_proc $DAEMON "RecordValues server"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 2
        ;;
esac
