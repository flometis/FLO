#!/bin/bash
/var/www/app/main.py &
sleep 2
/var/www/app/processqueue.py &

/etc/init.d/cron start

sleep infinity
