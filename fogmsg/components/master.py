import logging
import threading
import time
from collections import deque
from typing import Dict

import zmq
from fogmsg.components.errors import NoAcknowledgementError
from fogmsg.utils.logger import configure_logger
from zmq import Context


class NodeSender(threading.Thread):
    def __init__(self, advertised_hostname: str, ctx: Context = None):
        threading.Thread.__init__(self)
        self.logger = configure_logger(logging.getLogger(f"({advertised_hostname})"))

        self.advertised_hostname = advertised_hostname

        self.msg_queue = deque([])

        self.running = threading.Event()
        self.running.set()

        ctx = ctx or Context.instance()
        self.socket = ctx.socket(zmq.REQ)
        self.socket.connect(self.advertised_hostname)
        self.logger.info("connected")

    def enqueue(self, msg):
        self.logger.info("enqueuing message")
        self.msg_queue.append(msg)

    def join(self, timeout=None):
        self.logger.info("joining...")
        self.running.clear()
        threading.Thread.join(self, timeout)
        self.socket.close()
        self.logger.info("joined!")

    def reconnect(self):
        self.socket.connect(self.advertised_hostname)

    def try_send_messages(self) -> bool:
        while len(self.msg_queue) > 0:
            self.logger.info(f"message queue: {len(self.msg_queue)}")
            msg = self.msg_queue[-1]
            try:
                self._send_message(msg)
                self.msg_queue.popleft()
            except (TimeoutError, NoAcknowledgementError):
                self.reconnect()
                return False
        return True

    def _send_message(self, msg, timeout=1000):
        self.logger.info("sending message...")
        try:
            self.socket.send_json(msg, zmq.NOBLOCK)
        except zmq.error.Again:
            self.logger.critical("could not reach host!")
            raise TimeoutError

        if self.socket.poll(timeout) == 0:
            self.logger.critical("sending of message timed out!")
            raise TimeoutError

        msg = self.socket.recv_json()
        if msg != "ack":
            self.logger.critical("message was not ack'ed")
            raise NoAcknowledgementError

    def run(self):
        self.logger.info("started")

        while self.running.is_set():
            self.try_send_messages()
            time.sleep(0.1)


class Master:
    def __init__(self, hostname: str = "0.0.0.0", port: int = 4000):
        self.logger = configure_logger(logging.getLogger("master"))
        self.ctx = Context.instance()
        self.hostname = hostname
        self.port = port

        self.nodes: Dict[str, NodeSender] = dict()
        self.nodes_lock = threading.Lock()
        self.running = False

    def register_node(self, advertised_hostname: str, ctx: Context = None):
        ctx = ctx or Context.instance()
        with self.nodes_lock:
            self.logger.info(f"registering node ({advertised_hostname})")

            self.nodes[advertised_hostname] = NodeSender(advertised_hostname, ctx)
            self.nodes[advertised_hostname].start()

    def unregister_node(self, advertised_hostname):
        with self.nodes_lock:
            if advertised_hostname in self.nodes:
                self.logger.info(f"unregistering node ({advertised_hostname})")
                self.nodes[advertised_hostname].join()
                del self.nodes[advertised_hostname]

    def send_to_all(self, msg, exclude=None):
        with self.nodes_lock:
            self.logger.info("sending message to all nodes...")

            for advertised_hostname, sender in self.nodes.items():
                if not exclude or advertised_hostname not in exclude:
                    sender.enqueue(msg)

    def join(self):
        self.socket.close()
        self.running = False
        with self.nodes_lock:
            for sender in self.nodes:
                sender.join()

    def run(self):
        self.logger.info("starting fogmsg master...")

        self.socket = self.ctx.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.hostname}:{self.port}")

        self.logger.info(
            f"started master (hostname={self.hostname}, ports={self.port})"
        )

        self.running = True
        while self.running:
            msg = self.socket.recv_json()
            self.socket.send_json("ack")

            if msg["cmd"] == "register":
                self.register_node(msg["advertised_hostname"])
            elif msg["cmd"] == "unregister":
                self.unregister_node(msg["advertised_hostname"])
            elif msg["cmd"] == "publish":
                self.send_to_all(msg)
