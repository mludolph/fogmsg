import time
#from abc import ABC, abstractmethod
#from typing import Optional
from fogmsg.components.gps_sensor import GPS_Sensor
#import psutil


class Sensor():
    #@abstractmethod
    def get_reading(self):
        pass


class MockSensor():
    def __init__(self, freq=1):
        self.gps = GPS_Sensor()
        self.freq = freq

    def get_reading(self):
        time.sleep(self.freq)
        data = self.gps.get_data()
        result = {
            'time': int(time.time()),
            'lat': data[0],
            'lng': data[1]
        }
        return result
        #mem = psutil.virtual_memory()
        #net = psutil.net_io_counters()
        #return {
         #   "time": int(time.time()),
         #   "cpu_percent": psutil.cpu_percent(),
         #   "mem_used": mem.available,
         #   "mem_free": mem.used,
         #   "mem_percent": mem.percent,
         #   "net_sent": net.bytes_sent,
         #   "net_received": net.bytes_recv,
        #}
