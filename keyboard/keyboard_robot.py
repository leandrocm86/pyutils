from .keyboard_events import KeyboardEvent, EventType
from .. import log


class KeyboardEvdevRobot:
    """A class that simulates a keyboard and generates artificial input events.
    It uses evdev (linux-only) and the user should have access to /dev/uinput.
    The close() method should be called when the robot is no longer needed.

    PS: For wayland systems, you probably should use KeyboardPynputRobot instead.

    Configuring access to /dev/uinput:
    - Add the user to the input group: sudo usermod -a -G input $USER
    - Create a udev rule: echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
    - Reload the udev rules: sudo udevadm control --reload-rules; sudo udevadm trigger
    """

    def __init__(self, virtual_device_name: str):
        from evdev import UInput  # pip install evdev (parece ser linux-only)
        self.ui = UInput(name=virtual_device_name)

    def input_event(self, event: KeyboardEvent):
        """Generates a key input event, given a KeyboardEvent."""
        from evdev import ecodes  # pip install evdev (parece ser linux-only)
        self.ui.write(ecodes.EV_KEY, event.keycode, event.event_type.value)  # type: ignore
        self.ui.syn()  # type: ignore
        log.debug('Robot input (evdev): %s', event)

    def close(self):
        self.ui.close()


class KeyboardPynputRobot:
    """A class that simulates a keyboard and generates artificial input events.
    It uses pynput, and it works with both x11 and wayland systems,
    but it's not reliable to reproduce suppressed evdev events.
    """

    def __init__(self):
        from pynput import keyboard
        from pynput.keyboard import Key
        self.controller = keyboard.Controller()

        # pynput works with the char text, not code. So it uses its own inverted dictionary if given codes.
        self.dictionary: dict[int, str | Key] = {v: k for k, v in KeyboardEvent.dictionary.items()}

        # mapping special keys that may be absent or different in KeyboardEvent's dictionary
        self.dictionary.update({
            14: Key.backspace,
            15: Key.tab,
            28: Key.enter,
            29: Key.ctrl,
            41: "'",
            42: Key.shift,
            56: Key.alt,
            57: Key.space,
            68: Key.f10,
            70: Key.pause,
            88: Key.f12,
            97: Key.ctrl_r,
            100: Key.alt_r,
            125: Key.cmd,
            127: Key.menu,
            102: Key.home,
            103: Key.up,
            104: Key.page_up,
            105: Key.left,
            106: Key.right,
            107: Key.end,
            108: Key.down,
            109: Key.page_down,
            110: Key.insert,
            111: Key.delete
        })

    def input_event(self, event: KeyboardEvent):
        """Generates a key input event, given a KeyboardEvent.
        This method should actually not be necessary, unless trying to propagate suppressed keys"""

        char = self.dictionary.get(event.keycode)
        assert char, f"Key code not found for pynput's inverted dictionary: {event.keycode}"

        if event.event_type == EventType.MOV_DOWN:
            self.controller.press(char)
        elif event.event_type == EventType.MOV_UP:
            self.controller.release(char)
        else:
            log.warn('Ignoring event type in pynput: %s', event.event_type)
            return

        log.debug('Robot input (pynput): %s (%s)', event, char)

    def input_text(self, text: str):
        "Inputs text directly, using pynput's abstraction instead of converting to codes."
        self.controller.type(text)
        log.info('Robot typing text (pynput): %s', text)
