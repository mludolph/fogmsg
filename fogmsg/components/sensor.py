import time
from abc import ABC, abstractmethod
from typing import Optional

import psutil


class Sensor(ABC):
    @abstractmethod
    def get_reading(self) -> Optional[dict]:
        pass


class MockSensor(Sensor):
    def __init__(self, freq=1):
        self.freq = freq

    def get_reading(self) -> Optional[dict]:
        time.sleep(self.freq)

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
