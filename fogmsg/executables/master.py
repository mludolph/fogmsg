import argparse
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

from fogmsg.components import Master  # noqa

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fogmsg Node")
    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        help="address that the node will bind to",
        default="0.0.0.0",
    )

    parser.add_argument(
        "-p", "--port", type=int, help="port that the node will bind to", default=4000
    )

    args = parser.parse_args()
    master = Master(hostname=args.ip, port=args.port)
    try:
        master.run()
    except KeyboardInterrupt:
        master.join()
