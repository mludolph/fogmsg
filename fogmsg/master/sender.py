import hashlib
import os
import threading
import time

import zmq
from fogmsg.master.config import MasterConfig
from fogmsg.utils.errors import NoAcknowledgementError
from fogmsg.utils.logger import configure_logger
from fogmsg.utils.queue import MessageQueue
from zmq import Context


class NodeSender(threading.Thread):
    def __init__(
        self, advertised_hostname: str, config: MasterConfig, ctx: Context = None
    ):
        threading.Thread.__init__(self)
        self.logger = configure_logger(f"sender({advertised_hostname})")

        self.config = config
        self.advertised_hostname = advertised_hostname

        path = os.path.join(
            config.PERSISTENCE_DIR,
            hashlib.md5(advertised_hostname.encode("utf-8")).hexdigest(),
        )
        self.msg_queue = MessageQueue(config.SENDER_QUEUE_LENGTH, path)

        self.running = threading.Event()
        self.running.set()

        self.ctx = ctx or Context.instance()
        self.socket = None

    def enqueue(self, msg):
        self.logger.debug("enqueuing message")
        self.msg_queue.enqueue(msg)

    def join(self, timeout=None):
        self.logger.debug("joining...")
        self.running.clear()
        threading.Thread.join(self, timeout)

        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()

        self.logger.info(f"closed connection (hostname={self.advertised_hostname}")

    def reconnect(self):
        if not self.running.is_set():
            return

        if self.socket:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect(self.advertised_hostname)
        self.logger.info(
            f"connecting to node receiver (hostname={self.advertised_hostname})"
        )

    def try_send_messages(self) -> bool:
        while self.msg_queue.peek():
            self.logger.debug(f"message queue: {len(self.msg_queue)}")
            msg = self.msg_queue.peek()
            try:
                self._send_message(msg)
                self.msg_queue.dequeue()
            except (TimeoutError, NoAcknowledgementError):
                self.reconnect()
                return False
        return True

    def _send_message(self, msg):
        self.logger.debug("sending message...")
        try:
            self.socket.send_json(msg, zmq.NOBLOCK)
        except zmq.error.Again:
            self.logger.warn("could not reach host!")
            raise TimeoutError

        if self.socket.poll(self.config.SENDER_TIMEOUT) == 0:
            self.logger.warn("sending of message timed out!")
            raise TimeoutError

        msg = self.socket.recv_json()
        if msg != "ack":
            self.logger.warn("message was not ack'ed")
            raise NoAcknowledgementError

    def run(self):
        self.logger.info("started node sender")
        self.reconnect()

        while self.running.is_set():
            self.try_send_messages()
            time.sleep(0.1)
