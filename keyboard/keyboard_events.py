from enum import Enum
from typing import Self
from evdev import InputEvent


class EventType(Enum):
    """Identifies the types of keyboard events in evdev."""
    MOV_UP = 0
    MOV_DOWN = 1
    MOV_HOLD = 2


class KeyboardEvent:
    keycode: int
    event_type: EventType

    @classmethod
    def from_evdev(cls, event: InputEvent) -> Self:
        assert event.value <= 3, f'Invalid evdev keyboard event type: {event.value}'
        return cls(event.code, EventType(event.value))

    @classmethod
    def from_dictionary(cls, keylabel: str, event_type: EventType) -> Self:
        """Creates a KeyboardEvent from a dictionary key label and a specific type."""
        assert keylabel in KeyboardEvent.dictionary, f'Key name not found in dictionary: {keylabel}'
        return cls(KeyboardEvent.dictionary[keylabel], event_type)

    @classmethod
    def from_tap(cls, key: str | int) -> tuple[Self, Self] | tuple[Self, Self, Self, Self]:
        """Creates a tuple of KeyboardEvents from a key (label or code) for tapping (down/up) events.
        If the key is a special character (present in shift_dictionary), it will add 2 more events for shift.
        """

        if isinstance(key, str):
            if key in KeyboardEvent.shift_dictionary:
                assert 'shift' in KeyboardEvent.dictionary, "Shift key not found in dictionary. Can't use special characters!"
                return (
                    cls(KeyboardEvent.dictionary['shift'], EventType.MOV_DOWN),
                    cls(KeyboardEvent.shift_dictionary[key], EventType.MOV_DOWN),
                    cls(KeyboardEvent.shift_dictionary[key], EventType.MOV_UP),
                    cls(KeyboardEvent.dictionary['shift'], EventType.MOV_UP)
                )
            else:
                return cls.from_dictionary(key, EventType.MOV_DOWN), \
                    cls.from_dictionary(key, EventType.MOV_UP)
        else:
            return cls(key, EventType.MOV_DOWN), \
                cls(key, EventType.MOV_UP)

    @classmethod
    def from_hold(cls, key: str | int) -> tuple[Self, Self]:
        """Creates a tuple of KeyboardEvents from a key (label or code) for hold events."""

        if isinstance(key, str):
            return cls.from_dictionary(key, EventType.MOV_DOWN), \
                cls.from_dictionary(key, EventType.MOV_HOLD)
        else:
            return cls(key, EventType.MOV_DOWN), \
                cls(key, EventType.MOV_HOLD)

    def __init__(self, keycode: int, event_type: EventType):
        self.keycode = keycode
        self.event_type = event_type

    def __eq__(self, value: object) -> bool:
        return isinstance(value, KeyboardEvent) and value.keycode == self.keycode and value.event_type == self.event_type

    def __str__(self):
        return f'{self.event_type.name} {self.keycode}'

    def __repr__(self):
        return str(self)

    # Dictionary to map text to its respective key code.
    # https://community.bistudio.com/wiki/DIK_KeyCodes
    dictionary: dict[str, int] = {
        "␈": 14,  # Backspace symbol
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 5,
        "5": 6,
        "6": 7,
        "7": 8,
        "8": 9,
        "9": 10,
        "0": 11,
        "-": 12,
        "=": 13,
        "tab": 15,
        "q": 16,
        "w": 17,
        "e": 18,
        "r": 19,
        "t": 20,
        "y": 21,
        "u": 22,
        "i": 23,
        "o": 24,
        "p": 25,
        "acento": 26,
        "\n": 28,
        "ctrl": 29,
        "a": 30,
        "s": 31,
        "d": 32,
        "f": 33,
        "g": 34,
        "h": 35,
        "j": 36,
        "k": 37,
        "l": 38,
        "ç": 39,
        "til": 40,
        "shift": 42,
        "z": 44,
        "x": 45,
        "c": 46,
        "v": 47,
        "b": 48,
        "n": 49,
        "m": 50,
        ",": 51,
        ".": 52,
        ";": 53,
        "shift_dir": 54,
        "alt": 56,
        " ": 57,
        "f9": 67,
        "f10": 68,
        "pause": 70,
        "f12": 88,
        "ctrl_dir": 97,
        "alt_gr": 100,
        "win": 125,
        "menu": 127,
    }

    # Maps special characters to their respective key codes when combined with SHIFT.
    shift_dictionary: dict[str, int] = {
        "@": 3,
        ":": 53,
        "_": 12
    }
