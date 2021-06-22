import argparse
import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

from fogmsg.components import Node  # noqa
from fogmsg.components.sensor import MockSensor  # noqa

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

    args = parser.parse_args()

    sensor = MockSensor()
    node = Node(
        sensor=sensor,
        hostname=args.ip,
        port=args.port,
        advertised_hostname=args.advertised_listener,
    )
    try:
        node.run()
    except KeyboardInterrupt:
        node.join()
