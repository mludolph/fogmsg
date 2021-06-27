#!/bin/bash

python fogmsg/executables/sensor.py --type=metrics --pipe-file="/tmp/metrics" --log-level="critical" &
python fogmsg/executables/sensor.py --type=gps --pipe-file="/tmp/gps" --log-level="critical" &

# wait for sensors to come up
sleep 0.5

python fogmsg/executables/node.py