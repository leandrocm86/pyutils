import threading
import time
from typing import Callable


def spawn_interval_runner(task: Callable[[], None], stop_condition: Callable[[], bool], interval: float = 1.0):
    """Run 'task' every 'interval' seconds in a background thread until 'stop_condition' returns True."""

    assert interval > 0

    def loop():
        while not stop_condition():
            task()
            time.sleep(interval)
    threading.Thread(target=loop).start()
