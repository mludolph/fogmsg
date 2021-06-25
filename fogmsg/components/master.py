import threading
import time
from collections import deque
#from typing import Dict

import zmq
from fogmsg.components.errors import NoAcknowledgementError
from fogmsg.utils.logger import configure_logger
from zmq import Context


class NodeSender(threading.Thread):
    def __init__(self, advertised_hostname, ctx = None):
        threading.Thread.__init__(self)
        self.logger = configure_logger("sender("+str(advertised_hostname) + ")")

        self.advertised_hostname = advertised_hostname

        self.msg_queue = deque([])

        self.running = threading.Event()
        self.running.set()

        self.ctx = ctx or Context.instance()
        self.socket = None

    def enqueue(self, msg):
        self.logger.debug("enqueuing message")
        self.msg_queue.append(msg)

    def join(self, timeout=None):
        self.logger.debug("joining...")
        self.running.clear()
        threading.Thread.join(self, timeout)

        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()

        self.logger.info("closed connection (hostname="+str(self.advertised_hostname))

    def reconnect(self):
        if self.socket:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect(self.advertised_hostname)
        self.logger.info("connecting to node receiver (hostname="+ str(self.advertised_hostname) +")")

    def try_send_messages(self):
        while len(self.msg_queue) > 0:
            self.logger.debug("message queue:"+ str(len(self.msg_queue)))
            msg = self.msg_queue[-1]
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
    def __init__(self, hostname = "0.0.0.0", port = 4000):
        self.logger = configure_logger("master")
        self.ctx = Context.instance()
        self.hostname = hostname
        self.port = port

        self.nodes = dict()
        self.nodes_lock = threading.Lock()
        self.running = False

    def register_node(self, advertised_hostname, ctx = None):
        ctx = ctx or Context.instance()
        with self.nodes_lock:
            self.logger.info("registering node (" +str(advertised_hostname) + ")")

            if advertised_hostname in self.nodes:
                self.logger.warn("node ("+str({advertised_hostname})+") already registered")
                return

            self.nodes[advertised_hostname] = NodeSender(advertised_hostname, ctx)
            self.nodes[advertised_hostname].start()

    def unregister_node(self, advertised_hostname):
        with self.nodes_lock:
            if advertised_hostname in self.nodes:
                self.logger.info("unregistering node ("+ str(advertised_hostname) + ")")
                self.nodes[advertised_hostname].join()
                del self.nodes[advertised_hostname]

    def send_to_all(self, msg, exclude=None):
        with self.nodes_lock:
            self.logger.debug("sending message to all nodes...")

            for advertised_hostname, sender in self.nodes.items():
                if not exclude or advertised_hostname not in exclude:
                    sender.enqueue(msg)

    def join(self):
        self.logger.debug("shutting down master...")
        self.socket.close()
        self.running = False
        with self.nodes_lock:
            for sender in self.nodes:
                sender.join()

        self.logger.debug("master shut down")

    def run(self):
        self.logger.debug("starting fogmsg master...")

        self.socket = self.ctx.socket(zmq.REP)
        self.socket.bind("tcp://"+str(self.hostname)+ ":" + str(self.port))

        self.logger.info(
            "started master (hostname="+str(self.hostname) +", ports=" + str(self.port) +")"
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
