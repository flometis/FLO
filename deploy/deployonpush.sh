#!/bin/bash

if [ -z "$1" ]; then
  exit
fi

if [ -z "$2" ]; then
  exit  
fi

if [ -z "$3" ]; then
  exit
fi


filetocheck=$1
deploycommand=$2
appname=$3

PIDFILE=/tmp/$appname.pid
if [ -f $PIDFILE ]
then
  PID=$(cat $PIDFILE)
  ps -p $PID > /dev/null 2>&1
  if [ $? -eq 0 ]; then exit; fi
fi
echo $$ > $PIDFILE
if [ $? -ne 0 ]
  then
    echo "Could not create PID file"
    exit 1
fi


while true; do
  watch -d -t -g ls -l $filetocheck
  /bin/bash -c "$deploycommand"
  sleep 10
done

