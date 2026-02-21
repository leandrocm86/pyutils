import subprocess
import threading
import time
from typing import Callable


class WindowMonitor:
    """Monitor the active window title in a Linux environment using xdotool and xprop."""
    def __init__(self, logfunc: Callable[[str], None] | None = print):
        self.current_window = None
        self.previous_window = None
        self._running = False
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._logfunc = logfunc

    def __log(self, message: str):
        if self._logfunc:
            self._logfunc(message)

    def get_active_window_title(self) -> str | None:
        try:
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            xprop_output = subprocess.check_output(['xprop', '-id', window_id, 'WM_NAME']).decode().strip()
            return xprop_output.split('=')[-1].strip().strip('"')
        except Exception:
            return None

    def _monitor_loop(self):
        while self._running:
            current_title = self.get_active_window_title()
            if current_title != self.current_window:
                with self._lock:
                    self.previous_window = self.current_window
                    self.current_window = current_title
                self.__log(f"Window changed: {current_title}")
            time.sleep(0.5)

    def start(self):
        """Start the window monitoring in a separate thread."""
        if not self._running:
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop)
            self._monitor_thread.daemon = True  # Thread will stop when main program exits
            self._monitor_thread.start()

    def stop(self):
        """Stop the window monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join()

    def get_windows(self) -> tuple[str | None, str | None]:
        """Get the current and previous window titles in a thread-safe way."""
        self.__log('get_windows called')
        with self._lock:
            self.__log(f'Lock acquired in get_windows. Returning current_window: {self.current_window}, previous_window: {self.previous_window}')
            return self.current_window, self.previous_window
