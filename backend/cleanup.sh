#!/bin/bash
find /tmp/Bran -mmin +30 -exec rm -rf {} \;
ps aux | grep Bran | grep python3 |
while read -r line; do
  pid=$(echo $line | grep -o 'root *[0-9]*' | grep -o '[0-9]*')
  filename=$(echo $line | grep -o '/tmp/Bran[^ ]*')
  if [ ! -f $filename ] && [[ ! -z $filename ]]; then
    kill -9 $pid
  fi
done

