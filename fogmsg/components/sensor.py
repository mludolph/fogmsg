from fogmsg.utils.logger import configure_logger
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

try:
    import psutil
except ImportError:
    print("PSUTIL disabled")

from fogmsg.components.gps_data import gps_data_list

LOGGER = configure_logger("sensor")


class Sensor(ABC):
    @abstractmethod
    def get_reading(self) -> Optional[dict]:
        pass

    @abstractmethod
    def continuous_log(self):
        pass


class PipeSensor(Sensor):
    def __init__(self, pipe_file: str, freq: float = 1000):
        self.pipe_file = pipe_file
        self.freq = freq
        self.last_reading = 0
        self.pipe_fd = os.open(self.pipe_file, os.O_RDONLY | os.O_NONBLOCK)

    def get_reading(self):
        if self.last_reading + self.freq > int(time.time() * 1000):
            return None
        self.last_reading = int(time.time() * 1000)

        if not os.path.exists(self.pipe_file):
            return None

        try:
            buffer = os.read(self.pipe_fd, 1024)
            decoded = buffer.decode("utf-8")
            data = json.loads(decoded)
            LOGGER.debug(f"generated data for pipe sensor {self.pipe_file}")
            return data
        except Exception:
            return None

    def close(self):
        pass

    def continuous_log(self):
        return None


class GPSSensor(Sensor):
    def __init__(self, freq: float = 1000):
        self.freq = freq
        self.index = 0
        self.last_reading = 0

    def _get_data(self):
        data = gps_data_list[self.index]
        self.index = (self.index + 1) % len(gps_data_list)
        return data

    def continuous_log(self, callback):
        self.running = True
        while self.running:
            data = self.get_reading()
            callback(data)
            time.sleep(self.freq / 1000)

    def get_reading(self):
        if self.last_reading + self.freq > int(time.time() * 1000):
            return None
        self.last_reading = int(time.time() * 1000)

        data = self._get_data()
        result = {"time": int(time.time()), "lat": data[0], "lng": data[1]}
        return result


class MetricsSensor(Sensor):
    def __init__(self, freq: float = 1000):
        self.freq = freq
        self.running = False
        self.last_reading = 0

    def continuous_log(self, callback):
        self.running = True
        while self.running:
            data = self.get_reading()
            callback(data)
            time.sleep(self.freq / 1000)

    def get_reading(self) -> Optional[dict]:
        if self.last_reading + self.freq > int(time.time() * 1000):
            return None
        self.last_reading = int(time.time() * 1000)

        mem = psutil.virtual_memory()
        net = psutil.net_io_counters()
        return {
            "time": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "mem_used": mem.available,
            "mem_free": mem.used,
            "mem_percent": mem.percent,
            "net_sent": net.bytes_sent,
            "net_received": net.bytes_recv,
        }
