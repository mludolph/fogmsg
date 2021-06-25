from fogmsg.components.gps_data import gps_data_list
import threading
import time

class GPS_Sensor:

	def __init__(self):
		self.index = 0
		self.running = False
		self.thread = None
		return

	def get_data(self):
		data = gps_data_list[self.index]
		self.index = (self.index + 1) % len(gps_data_list)
		return data

	def continuous_log(self,callback):
		while(True):
			if (self.running == False):
				break
			data = self.get_data()
			callback(data)
			time.sleep(3)
		return

	def start_continuous_logging(self, callback):
		self.thread = threading.Thread(target=self.continuous_log, args=(callback,))
		self.running = True
		self.thread.start()
		self.thread.deamon = True
		return

	def stop_continuous_logging(self):
		self.running = False
		return