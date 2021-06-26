#!/bin/bash
MASTER_IP=localhost
EXTERNAL_IP=localhost

python fogmsg/executables/sensor.py --type=metrics --pipe-file="/tmp/metrics" --log-level="critical" &
python fogmsg/executables/sensor.py --type=gps --pipe-file="/tmp/gps" --log-level="critical" &

# wait for sensors to come up
sleep 0.5

python fogmsg/executables/node.py --master="tcp://${MASTER_IP}:4000" \
                                  --advertised-listener="tcp://${EXTERNAL_IP}:4001" \
                                  --pipe-files="/tmp/metrics;/tmp/gps"

