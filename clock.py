from __future__ import annotations
import time


class Clock:
    """ Timer that tracks elapsed time, allowing for multiple instances to be created and managed. """

    clocks_by_name: dict[str, Clock] = {}

    def __init__(self, name: str | None = None):
        if name:
            Clock.clocks_by_name[name] = self
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
        return cls.clocks_by_name.setdefault(clock_name, Clock())
