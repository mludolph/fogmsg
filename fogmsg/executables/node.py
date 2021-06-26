import argparse
import os
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

import fogmsg.utils as utils  # noqa
from fogmsg.node import Node, NodeConfig  # noqa
from fogmsg.node.sensor import PipeSensor  # noqa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fogmsg Node")
    parser.add_argument(
        "--master-hostname",
        dest="master_hostname",
        type=str,
        help="hostname of the master (default: tcp://localhost:4000)",
        default=os.environ.get("MASTER_HOSTNAME", "tcp://localhost:4000"),
    )

    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        help="address that the node will bind to (default: 0.0.0.0)",
        default=os.environ.get("NODE_IP", "0.0.0.0"),
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="port that the node will bind to (default: 4001)",
        default=os.environ.get("NODE_PORT", 4001),
    )

    parser.add_argument(
        "--advertised-listener",
        dest="advertised_hostname",
        type=str,
        help="the advertisement listener of this node (default: tcp://localhost:4001)",
        default=os.environ.get("NODE_ADVERTISED_LISTENER", "tcp://localhost:4001"),
    )

    parser.add_argument(
        "--pipe-files",
        dest="pipe_files",
        type=str,
        help="the pipe file to use for ipc, to use multiple pipes, \
             seperate them by ';' (default: /tmp/metrics;/tmp/gps)",
        default="/tmp/metrics;/tmp/gps",
    )

    parser.add_argument(
        "--sender-queue-length",
        type=int,
        dest="sender_queue_length",
        help="length of the sender queues (default: 1000)",
        default=os.environ.get("NODE_SENDER_QUEUE_LENGTH", 1000),
    )

    parser.add_argument(
        "--sender-timeout",
        type=int,
        dest="sender_timeout",
        help="timeout of the sender in ms (default: 1000)",
        default=os.environ.get("NODE_SENDER_TIMEOUT", 1000),
    )

    parser.add_argument(
        "--persistence-dir",
        type=str,
        dest="persistence_dir",
        help="directory for queue files (default: ./)",
        default=os.environ.get("NODE_PERSISTENCE_DIR", "./"),
    )

    parser.add_argument(
        "--log-level",
        type=str,
        dest="log_level",
        choices=["debug", "info", "warn", "critical"],
        help="the log-level (default: info)",
        default="info",
    )

    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=str,
        help="the path to the log file, default is to write to console",
        default="",
    )
    args = parser.parse_args()

    setattr(utils.logger, "LOGLEVEL", args.log_level)
    setattr(utils.logger, "LOGFILE", args.log_file)

    sensors = []
    for pipe_path in args.pipe_files.split(";"):
        sensors.append(PipeSensor(pipe_path))

    config = NodeConfig(args)
    node = Node(sensors=sensors, config=config)

    try:
        node.run()
    except KeyboardInterrupt:
        node.join()

        for sensor in sensors:
            sensor.close()
