from fogmsg.utils import messaging
import threading
from typing import Dict

import zmq
from fogmsg.master.config import MasterConfig
from fogmsg.master.persistence import SQLitePersistence
from fogmsg.master.sender import NodeSender
from fogmsg.utils.logger import configure_logger
from zmq import Context


class Master:
    def __init__(self, config: MasterConfig):
        self.logger = configure_logger("master")
        self.ctx = Context.instance()

        self.config = config
        self.hostname = config.IP
        self.port = config.PORT

        self.db = SQLitePersistence(config)

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

            self.nodes[advertised_hostname] = NodeSender(
                advertised_hostname, self.config, ctx
            )
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

    def get_registered_nodes(self):
        with self.nodes_lock:
            return list(self.nodes.keys())

    def persist(self, msg: dict):
        if self.db:
            self.db.persist_message(msg)

    def send_to_all(self, msg, exclude=None):
        with self.nodes_lock:
            self.logger.debug("sending message to all nodes...")

            for advertised_hostname, sender in self.nodes.items():
                if not exclude or advertised_hostname not in exclude:
                    sender.enqueue(msg)

    def send_to_one(self, msg, receiver: str):
        with self.nodes_lock:
            if receiver not in self.nodes:
                self.logger.critical("tried sending to unknown receiver")
                return
            self.nodes[receiver].enqueue(msg)

    def join(self):
        self.running = False
        self.logger.debug("shutting down master...")
        if self.socket:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

        with self.nodes_lock:
            for sender in self.nodes.values():
                sender.join()

        self.logger.info("closing db")
        self.db.close()
        self.logger.info("master shut down")

    def handle_message(self, msg, orig_msg):
        origin = msg.get("origin", None)
        # handle non registered nodes
        if origin and not self.is_node_registered(origin):
            self.register_node(origin)

        # persist all messages
        self.persist(msg)

        # broadcast gps location to all other nodes
        if msg.get("sensor", None) == "gps":
            self.send_to_all(orig_msg, exclude=[origin])
        elif msg.get("sensor", None) == "metrics":
            payload = msg.get("payload")
            if payload["cpu_percent"] > self.config.CPU_PERCENT_THRESHOLD:
                self.send_to_one(messaging.control_message("THROTTLE"), origin)
            else:
                self.send_to_one(messaging.control_message("NOTHROTTLE"), origin)

    def run(self):
        self.logger.debug("starting fogmsg master...")

        self.socket = self.ctx.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.hostname}:{self.port}")

        self.logger.info(
            f"started master (hostname={self.hostname}, ports={self.port})"
        )

        self.running = True
        while self.running:
            if self.socket.poll(1000) == 0:
                continue

            orig_msg = self.socket.recv()
            msg = messaging.deserialize(orig_msg)

            if msg["cmd"] == "register":
                self.register_node(msg["advertised_hostname"])
            elif msg["cmd"] == "unregister":
                self.unregister_node(msg["advertised_hostname"])
            elif msg["cmd"] == "publish":
                self.handle_message(msg, orig_msg)

            self.socket.send(messaging.ack_message())
