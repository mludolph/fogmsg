from collections import deque
from typing import Any, Optional
import shelve
import threading


class MessageQueue:
    def __init__(self, max_size: int = 1000, persistence_path: Optional[str] = None):
        self._lock = threading.Lock()
        if persistence_path:
            self._shelve = shelve.open(persistence_path, writeback=True)
            self._q = self._shelve.get("queue", deque([]))
        else:
            self._q = deque([])

        self.max_size = max_size

    def _save(self):
        if self._shelve:
            self._shelve["queue"] = self._q

    def enqueue(self, msg: Any) -> bool:
        with self._lock:
            if len(self._q) >= self.max_size:
                return False

            self._q.append(msg)
            self._save()
            return True

    def dequeue(self) -> Optional[Any]:
        with self._lock:
            if len(self._q) == 0:
                return None

            obj = self._q.popleft()
            self._save()
            return obj

    def peek(self) -> Optional[Any]:
        with self._lock:
            if len(self._q) == 0:
                return None

            return self._q[0]
