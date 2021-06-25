#!/bin/bash
MASTER_IP=
EXTERNAL_IP=
SENSOR=metrics

python fogmsg/executables/sensor.py --type=${SENSOR} --pipe-file="/tmp/${SENSOR}data" --log-level="critical"

python fogmsg/executables/node.py --master="tcp://${MASTER_IP}:4000" \
                                  --advertised-listener="tcp://${EXTERNAL_IP}:4001" \
                                  --pipe-files="/tmp/${SENSOR}data"

