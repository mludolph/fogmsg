import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

from fogmsg.components import Node  # noqa
from fogmsg.components.sensor import MockSensor  # noqa

if __name__ == "__main__":
    sensor = MockSensor()
    node = Node(sensor=sensor)
    try:
        node.run()
    except KeyboardInterrupt:
        node.join()
