from fogmsg.utils import messaging
from fogmsg.node.config import NodeConfig
import threading
import zmq
from zmq import Context
from fogmsg.utils.logger import configure_logger


class NodeReceiver(threading.Thread):
    def __init__(self, config: NodeConfig, message_callback, ctx: Context = None):
        threading.Thread.__init__(self)
        self.logger = configure_logger("receiver")
        self.message_callback = message_callback

        self.config = config
        self.hostname = config.IP
        self.port = config.PORT

        self.running = threading.Event()
        self.running.set()

        ctx = ctx or Context.instance()
        self.socket = ctx.socket(zmq.REP)

    def join(self, timeout=None):
        self.logger.debug("joining...")
        self.running.clear()
        threading.Thread.join(self, timeout)

        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()

        self.logger.info(
            f"node receiver shut down (hostname={self.hostname}, port={self.port})"
        )

    def run(self):
        self.socket.bind(f"tcp://{self.hostname}:{self.port}")
        self.logger.info(
            f"started node receiver (hostname={self.hostname}, port={self.port})"
        )

        while self.running.is_set():
            if self.socket.poll(1000) == 0:
                continue

            msg = self.socket.recv()
            msg = messaging.deserialize(msg)
            self.socket.send(messaging.ack_message())

            if not msg:
                continue

            self.message_callback(msg)
