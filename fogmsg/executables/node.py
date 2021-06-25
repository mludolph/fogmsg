import argparse
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

from fogmsg.components import Node  # noqa
from fogmsg.components.sensor import PipeSensor  # noqa
import fogmsg.utils as utils  # noqa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fogmsg Node")
    parser.add_argument(
        "--master",
        type=str,
        help="hostname of the master (default: tcp://localhost:4000)",
        default="tcp://localhost:4000",
    )

    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        help="address that the node will bind to (default: 0.0.0.0)",
        default="0.0.0.0",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="port that the node will bind to (default: 4001)",
        default=4001,
    )

    parser.add_argument(
        "--advertised_listener",
        type=str,
        help="the advertisement listener of this node (default: tcp://localhost:4001)",
        default="tcp://localhost:4001",
    )
    parser.add_argument(
        "--pipe-files",
        dest="pipe_files",
        type=str,
        help="the pipe file to use for ipc, to use multiple pipes, \
             seperate them by ';' (default: /tmp/gpsdata)",
        default="/tmp/gpsdata",
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

    node = Node(
        sensors=sensors,
        hostname=args.ip,
        port=args.port,
        advertised_hostname=args.advertised_listener,
    )

    try:
        node.run()
    except KeyboardInterrupt:
        node.join()
