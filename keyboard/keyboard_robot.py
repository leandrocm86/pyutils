from evdev import UInput, ecodes  # pip install evdev (parece ser linux-only)
from .keyboard_events import KeyboardEvent


class KeyboardRobot:
    """A class that simulates a keyboard and generates artificial input events.
    It uses evdev (linux-only) and the user should have access to /dev/uinput.
    The close() method should be called when the robot is no longer needed.

    Configuring access to /dev/uinput:
    - Add the user to the input group: sudo usermod -a -G input $USER
    - Create a udev rule: echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
    - Reload the udev rules: sudo udevadm control --reload-rules; sudo udevadm trigger
    """
    def __init__(self, virtual_device_name: str):
        self.ui = UInput(name=virtual_device_name)

    def input_event(self, event: KeyboardEvent):
        """Generates a key input event, given a KeyboardEvent."""
        self.ui.write(ecodes.EV_KEY, event.keycode, event.event_type.value)  # type: ignore
        self.ui.syn()  # type: ignore

    def close(self):
        self.ui.close()
