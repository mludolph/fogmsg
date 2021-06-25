import argparse
import json
import os
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

import fogmsg.utils as utils  # noqa
from fogmsg.components.sensor import GPSSensor, MetricsSensor  # noqa
from fogmsg.utils.logger import configure_logger  # noqa


LOGGER = configure_logger("sensor")


def write_to_pipe(pipe_fd: str, data):
    try:
        os.write(pipe_fd, json.dumps(data).encode("utf-8"))
        LOGGER.debug("data generated")
    except BrokenPipeError:
        LOGGER.critical("node shut down, shutting down sensor...")
        exit(0)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="fogmsg Sensor")

    parser.add_argument(
        "--pipe-file",
        dest="pipe_file",
        type=str,
        help="the pipe file to use for ipc (default: /tmp/metricsdata)",
        default="/tmp/metricsdata",
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=["gps", "metrics"],
        help="the type of data that should be generated (default: metrics)",
        default="metrics",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        dest="log_level",
        choices=["debug", "info", "warn", "critical"],
        help="the log-level (default: info)",
        default="debug",
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

    try:
        if os.path.exists(args.pipe_file):
            os.remove(args.pipe_file)
        os.mkfifo(args.pipe_file, mode=0o777)
        LOGGER.info(f"started sensor with (pipe={args.pipe_file})!")
    except OSError:
        LOGGER.critical(f"could not create FIFO pipe at {args.pipe_file}!")
        exit(-1)

    sensor = None
    if args.type == "gps":
        sensor = GPSSensor()
    elif args.type == "metrics":
        sensor = MetricsSensor()
    else:
        LOGGER.critical(f"unsupported sensor type '{args.type}'!")
        exit(-1)

    pipe_fd = os.open(args.pipe_file, os.O_WRONLY)
    try:
        LOGGER.info("generating data...")
        sensor.continuous_log(callback=lambda data: write_to_pipe(pipe_fd, data))
    except KeyboardInterrupt:
        os.close(pipe_fd)
        exit(0)
