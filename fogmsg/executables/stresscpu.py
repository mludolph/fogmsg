import threading


class NonsenseThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = threading.Event()

    def stop(self):
        self.running.clear()

    def run(self):
        self.running.set()
        while self.running.is_set():
            pr = 213123  # generate load
            pr * pr
            pr = pr + 1


if __name__ == "__main__":
    threads = []
    num_threads = 16

    for _ in range(num_threads):
        t = NonsenseThread()
        t.start()
        threads.append(t)

    try:
        while True:
            pr = 213123  # generate load
            pr * pr
            pr = pr + 1
    except KeyboardInterrupt:
        for thread in threads:
            thread.stop()
            thread.join()
