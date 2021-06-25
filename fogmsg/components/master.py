import threading
import time
from collections import deque
from typing import Dict

import zmq
from fogmsg.components.errors import NoAcknowledgementError
from fogmsg.utils.logger import configure_logger
from zmq import Context

import pprint

pp = pprint.PrettyPrinter(indent=4)


class NodeSender(threading.Thread):
    def __init__(self, advertised_hostname: str, ctx: Context = None):
        threading.Thread.__init__(self)
        self.logger = configure_logger(f"sender({advertised_hostname})")

        self.advertised_hostname = advertised_hostname

        self.msg_queue = deque([])

        self.running = threading.Event()
        self.running.set()

        self.ctx = ctx or Context.instance()
        self.socket = None

    def enqueue(self, msg):
        self.logger.debug("enqueuing message")
        self.msg_queue.append(msg)
        self.logger.info("enqueue message")
        pp.pprint(msg)

    def join(self, timeout=None):
        self.logger.debug("joining...")
        self.running.clear()
        threading.Thread.join(self, timeout)

        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()

        self.logger.info("closed connection (hostname={self.advertised_hostname}")

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
        while len(self.msg_queue) > 0 and self.running.is_set():
            self.logger.debug(f"message queue: {len(self.msg_queue)}")
            msg = self.msg_queue[0]
            try:
                self._send_message(msg)
                self.msg_queue.popleft()
            except (TimeoutError, NoAcknowledgementError):
                self.reconnect()
                return False
        return True

    def _send_message(self, msg, timeout=1000):
        self.logger.debug("sending message...")
        try:
            self.socket.send_json(msg, zmq.NOBLOCK)
        except zmq.error.Again:
            self.logger.warn("could not reach host!")
            raise TimeoutError

        if self.socket.poll(timeout) == 0:
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


class Master:
    def __init__(self, hostname: str = "0.0.0.0", port: int = 4000):
        self.logger = configure_logger("master")
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

            if advertised_hostname in self.nodes:
                self.logger.warn(f"node ({advertised_hostname}) already registered")
                return

            self.nodes[advertised_hostname] = NodeSender(advertised_hostname, ctx)
            self.nodes[advertised_hostname].start()

    def unregister_node(self, advertised_hostname):
        with self.nodes_lock:
            if advertised_hostname in self.nodes:
                self.logger.info(f"unregistering node ({advertised_hostname})")
                self.nodes[advertised_hostname].join()
                del self.nodes[advertised_hostname]

    def is_node_registered(self, advertised_hostname):
        with self.nodes_lock:
            return advertised_hostname in self.nodes

    def send_to_all(self, msg, exclude=None):
        with self.nodes_lock:
            self.logger.debug("sending message to all nodes...")

            for advertised_hostname, sender in self.nodes.items():
                if not exclude or advertised_hostname not in exclude:
                    sender.enqueue(msg)

    def join(self):
        self.running = False
        self.logger.debug("shutting down master...")
        if self.socket:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

        with self.nodes_lock:
            for sender in self.nodes:
                sender.join()

        self.logger.debug("master shut down")

    def run(self):
        self.logger.debug("starting fogmsg master...")

        self.socket = self.ctx.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.hostname}:{self.port}")

        self.logger.info(
            f"started master (hostname={self.hostname}, ports={self.port})"
        )

        self.running = True
        while self.running:
            try:
                if self.socket.poll(1000) == 0:
                    continue
            except KeyboardInterrupt:
                break

            msg = self.socket.recv_json()

            if msg["cmd"] == "register":
                self.register_node(msg["advertised_hostname"])
            elif msg["cmd"] == "unregister":
                self.unregister_node(msg["advertised_hostname"])
            elif msg["cmd"] == "publish":
                self.send_to_all(msg)  # TODO , exclude=origin)

                origin = msg.get("origin", None)
                if origin and not self.is_node_registered(origin):
                    self.register_node(origin)

            self.socket.send_json("ack")
