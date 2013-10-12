#!/bin/bash
COUNT=$1
for ((i = 1; i <= $COUNT; i++)); do
    python2.7 main.py $i &
done