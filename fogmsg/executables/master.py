import argparse
import os
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

import fogmsg.utils as utils  # noqa
from fogmsg.master import Master  # noqa
from fogmsg.master.config import MasterConfig  # noqa
from fogmsg.frontend.app import APIThread  # noqa

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fogmsg Master")
    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        help="address that the node will bind to (default: 0.0.0.0, env: MASTER_IP)",
        default=os.environ.get("MASTER_IP", "0.0.0.0"),
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="port that the node will bind to (default: 4000, env: MASTER_PORT)",
        default=os.environ.get("MASTER_PORT", 4000),
    )

    parser.add_argument(
        "-uip",
        "--ui-port",
        dest="ui_port",
        type=int,
        help="port that the node will bind to (default: 4002, env: MASTER_UI_PORT)",
        default=os.environ.get("MASTER_UI_PORT", 4002),
    )

    parser.add_argument(
        "--sender-queue-length",
        type=int,
        dest="sender_queue_length",
        help="length of the sender queues (default: 1000, env: MASTER_SENDER_QUEUE_LENGTH)",
        default=os.environ.get("MASTER_SENDER_QUEUE_LENGTH", 1000),
    )

    parser.add_argument(
        "--sender-timeout",
        type=int,
        dest="sender_timeout",
        help="timeout of the sender in ms (default: 1000, env: MASTER_SENDER_TIMEOUT)",
        default=os.environ.get("MASTER_SENDER_TIMEOUT", 1000),
    )

    parser.add_argument(
        "--persistence-dir",
        type=str,
        dest="persistence_dir",
        help="directory for queue files (default: ./, env: MASTER_PERSISTENCE_DIR)",
        default=os.environ.get("MASTER_PERSISTENCE_DIR", "./"),
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

    config = MasterConfig(args)
    master = Master(config=config)
    api_thread = APIThread(master=master, config=config)

    try:
        api_thread.start()
        master.run()
    except KeyboardInterrupt:
        api_thread.join()
        master.join()
