import sys
from os import path

sys.path.append(path.join(path.dirname(__file__), "..", ".."))

from fogmsg.components import Master  # noqa


if __name__ == "__main__":
    master = Master()
    try:
        master.run()
    except KeyboardInterrupt:
        master.join()
