import threading
import time
from collections import deque
from pprint import PrettyPrinter

import zmq
from fogmsg.components.errors import NoAcknowledgementError
from fogmsg.components.sensor import Sensor
from fogmsg.utils.logger import configure_logger
from zmq import Context


class NodeReceiver(threading.Thread):
    def __init__(self, hostname: str, port: int, ctx: Context = None):
        threading.Thread.__init__(self)
        self.logger = configure_logger("receiver")
        self.pp = PrettyPrinter(indent=4)
        self.hostname = hostname
        self.port = port

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

            msg = self.socket.recv_json()
            self.socket.send_json("ack")
            if msg["cmd"] == "publish":
                self.logger.info(f"messsage from {msg['origin']}:")
                self.pp.pprint(msg)


class Node:
    def __init__(
        self,
        sensor: Sensor,
        hostname: str = "0.0.0.0",
        port: int = 4001,
        advertised_hostname: str = "tcp://localhost:4001",
        master_hostname: str = "tcp://localhost:4000",
    ):
        self.logger = configure_logger("node")
        self.ctx = Context.instance()

        self.hostname = hostname
        self.port = port
        self.advertised_hostname = advertised_hostname
        self.master_hostname = master_hostname
        self.master = None

        self.msg_queue = deque([])

        self.running = False

        self.sensor = sensor

    def reconnect(self):
        if self.master:
            self.master.setsockopt(zmq.LINGER, 0)
            self.master.close()

        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(self.master_hostname)
        self.logger.info(f"connecting to master (hostname={self.master_hostname})")

    def try_send_messages(self) -> bool:
        self.logger.debug(f"message queue: {len(self.msg_queue)}")
        while len(self.msg_queue) > 0:
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
            self.master.send_json(msg, zmq.NOBLOCK)
        except zmq.error.Again:
            self.logger.warn("could not reach host!")
            raise TimeoutError

        if self.master.poll(timeout) == 0:
            self.logger.warn("sending of message timed out!")
            raise TimeoutError

        msg = self.master.recv_json()
        if msg != "ack":
            self.logger.warn("message was not ack'ed")
            raise NoAcknowledgementError

    def join(self):
        self.running = False
        self.msg_queue.append(
            {"cmd": "unregister", "advertised_hostname": self.advertised_hostname}
        )
        self.try_send_messages()

        self.receiver.join()
        self.master.close()

    def run(self):
        self.logger.info("starting fogmsg node...")

        # Start local receiver to receive messages
        self.receiver = NodeReceiver(self.hostname, self.port, ctx=self.ctx)
        self.receiver.start()

        # Start master socket
        self.reconnect()

        # wait for registration at master
        self.msg_queue.append(
            {"cmd": "register", "advertised_hostname": self.advertised_hostname}
        )

        self.running = True
        while not self.try_send_messages():
            time.sleep(0.5)

        self.logger.info("registered and started node")

        while self.running:
            payload = self.sensor.get_reading()
            if not payload:
                continue

            self.msg_queue.append(
                {
                    "cmd": "publish",
                    "payload": payload,
                    "origin": self.advertised_hostname,
                }
            )
            self.try_send_messages()
