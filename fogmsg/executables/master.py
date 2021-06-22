import argparse
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

import fogmsg.utils as utils  # noqa
from fogmsg.components import Master  # noqa

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fogmsg Master")
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
        help="port that the node will bind to (default: 4000)",
        default=4000,
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

    master = Master(hostname=args.ip, port=args.port)
    try:
        master.run()
    except KeyboardInterrupt:
        master.join()
