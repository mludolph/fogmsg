import hashlib
import os
import time
from typing import List

import zmq
from fogmsg.node.config import NodeConfig
from fogmsg.node.receiver import NodeReceiver
from fogmsg.node.sensor import Sensor
from fogmsg.utils import messaging
from fogmsg.utils.errors import NoAcknowledgementError
from fogmsg.utils.logger import configure_logger
from fogmsg.utils.queue import MessageQueue
from zmq import Context

from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)


class Node:
    def __init__(
        self,
        sensors: List[Sensor],
        config: NodeConfig,
    ):
        self.logger = configure_logger("node")
        self.ctx = Context.instance()

        self.config = config

        self.hostname = config.IP
        self.port = config.PORT
        self.advertised_hostname = config.ADVERTISED_HOSTNAME
        self.master_hostname = config.MASTER_HOSTNAME
        self.master = None

        path = os.path.join(
            config.PERSISTENCE_DIR,
            hashlib.md5(self.master_hostname.encode("utf-8")).hexdigest(),
        )
        self.msg_queue = MessageQueue(config.SENDER_QUEUE_LENGTH, path)

        self.running = False

        self.sensors = sensors

    def reconnect(self):
        if self.master:
            self.master.setsockopt(zmq.LINGER, 0)
            self.master.close()

        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(self.master_hostname)
        self.logger.info(f"connecting to master (hostname={self.master_hostname})")

    def try_send_messages(self) -> bool:
        while self.msg_queue.peek():
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
            # self.master.send_json(msg, zmq.NOBLOCK)
            self.master.send(msg)
        except zmq.error.Again:
            self.logger.warn("could not reach host!")
            raise TimeoutError

        if self.master.poll(self.config.SENDER_TIMEOUT) == 0:
            self.logger.warn("sending of message timed out!")
            raise TimeoutError

        msg = self.master.recv()
        msg = messaging.deserialize(msg)
        if msg != "ack":
            self.logger.warn("message was not ack'ed")
            raise NoAcknowledgementError

    def join(self):
        # self.running = False
        self.logger.info("unregistering node...")

        try:
            self._send_message(messaging.unregister_message(self.advertised_hostname))
        except Exception:
            pass

        self.receiver.join()
        self.master.close()

    def handle_message(self, msg):
        pp.pprint(msg)

    def run(self):
        self.logger.info("starting fogmsg node...")

        # Start local receiver to receive messages
        self.receiver = NodeReceiver(
            self.config,
            message_callback=lambda msg: self.handle_message(msg),
            ctx=self.ctx,
        )
        self.receiver.start()

        # Start master socket
        self.reconnect()

        # wait for registration at master
        self.msg_queue.enqueue(messaging.register_message(self.advertised_hostname))

        self.running = True

        self.logger.info("registered and started node")

        try:
            while self.running:
                for sensor in self.sensors:
                    payload = sensor.get_reading()
                    if not payload:
                        continue

                    self.msg_queue.enqueue(
                        messaging.publish_message(
                            self.advertised_hostname, sensor.name(), payload
                        )
                    )

                self.try_send_messages()
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.join()
