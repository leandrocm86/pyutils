from __future__ import annotations
import time


class Clock:
    """ Timer that tracks elapsed time, allowing for multiple instances to be created and managed. """

    clocks_by_name: dict[str, Clock] = {}

    def __init__(self, name: str | None = None):
        if name:
            Clock.clocks_by_name[name] = self
        self.name = name
        self.last_timestamp = time.time()
        self.total_time = 0

    def check(self) -> float:
        ''' Returns how much time has passed since the previous check (or since the start, for the first call). '''
        penultimate_timestamp = self.last_timestamp
        self.last_timestamp = time.time()
        diff = self.last_timestamp - penultimate_timestamp
        self.total_time += diff
        return diff

    def restart(self):
        ''' Restarts the counting for the next check. It doesn't erase the accumulated total time. '''
        self.last_timestamp = time.time()

    @classmethod
    def get(cls, clock_name: str) -> Clock:
        if clock_name not in cls.clocks_by_name:
            Clock(clock_name)
        return cls.clocks_by_name[clock_name]

    def __str__(self):
        return f"Clock('{self.name}'): {self.total_time:.2f}s"

    def __repr__(self):
        return f"Clock('{self.name}'): {self.total_time:.2f}s"
