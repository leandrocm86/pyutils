The ideia of this module is to listen keyboard events through evdev, and execute actions with either evdev or pynput.
Evdev seems limited/challenging for sending events to wayland, but pynput is limited/challenging for reproducing suppressed evdev events, while itself can't suppress selected devices (pynput's listener seems to suppress events only globally).

Unless we have changes in wayland, evdev or pynput in the future, we can't have suppressing (non-propagating) events in wayland.
Maybe we could try to use pynput for both listening and resending events, supposing it can reliably reproduce all events it suppresses. But it's probably better to avoid suppression if we can.  