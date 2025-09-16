from __future__ import annotations
# import os
# import time
import evdev  # pip install evdev (parece ser linux-only)
from .. import log
from .keyboard_controller import KeyController
from .keyboard_robot import KeyboardRobot
from .keyboard_events import KeyboardEvent


def _find_keyboard_device(device_path: str, device_name: str) -> evdev.InputDevice:
    """Tries to find the keyboard device with the given path and/or name.
    If neither path or name are given, it tries to find the only keyboard device available, raising an error if it can't.
    IMPORTANT: It may be needed to add the system user to the input group. Details on keyboard_robot.
    """
    devices_str: list[str] = evdev.list_devices()  # type: ignore
    devices: list[evdev.InputDevice] = [evdev.InputDevice(path) for path in devices_str]
    filtered_devices: list[evdev.InputDevice] = devices

    log.info(
        f"Searching for keyboard device. Given name: {device_name or 'any'}. Given path: {device_path or 'any'}")

    if device_name:
        filtered_devices = [d for d in filtered_devices if device_name == d.name]
    else:
        filtered_devices = [d for d in filtered_devices if 'keyboard' in d.name.lower()]

    if device_path:
        filtered_devices = [d for d in filtered_devices if device_path == d.path]  # type: ignore

    if not filtered_devices:
        log.error('No keyboard device found! Check the list below:')
        log.error('\n' + '\n'.join([d.path + ' - ' + d.name for d in devices]))  # type: ignore
        quit()
    elif len(filtered_devices) > 1:
        log.warn('More than one possible device found. Choosing the last one.'
                 ' If it is not the right one, specify it from the list below:')
        # type: ignore
        log.warn('\n' + '\n'.join([d.path + ' - ' + d.name for d in filtered_devices]))
    return filtered_devices[-1]


class KeyboardListener:
    """Listens to keyboard events from a given device and calls controllers for each event.
    If no device is specified, it tries to figure out the only keyboard device available (and raises an error if it can't tell).
    It must be supplied with a keyboard_robot to re-send intercepted events to the system.
    """

    def __init__(self, keyboard_robot: KeyboardRobot) -> None:
        self.suppressed_buffer = KeyboardListener.EventBuffer(keyboard_robot)
        self.controllers: list[KeyController] = []

    def connect(self, device_path: str = '', device_name: str = ''):
        log.info('STARTING KEYBOARD LISTENER')
        # Wait for the X server to be ready
        # while 'DISPLAY' not in os.environ:
        #     log.info("Waiting for X server...")
        #     time.sleep(5)
        # log.info(f'Display: {os.environ["DISPLAY"]}')

        device = _find_keyboard_device(device_path, device_name)

        log.info('Grabbing device (its events might be suppressed if the controllers choose so): ', device.name)
        device.grab()

        try:
            self.__listen_event_loop(device)
        finally:
            device.ungrab()
            device.close()

        log.info('ENDING KEYBOARD LISTENER')

    class EventBuffer:
        def __init__(self, keyboard_robot: KeyboardRobot):
            self.events: list[KeyboardEvent] = []
            self.keyboard_robot = keyboard_robot

        def add(self, event: KeyboardEvent):
            self.events.append(event)

        def flush(self, discard: bool):
            if not discard:
                for event in self.events:
                    # log.warn('Replicating events: ', event)
                    self.keyboard_robot.input_event(event)
            self.events.clear()

    def __listen_event_loop(self, device: evdev.InputDevice):
        for event in device.read_loop():  # type: ignore
            if not isinstance(event, evdev.events.InputEvent) or not event.code \
                    or event.type >= 3:   # SYNC EVENT or other non-key event
                continue
            log.debug('Captured event: ', event)
            event = KeyboardEvent.from_evdev(event)
            log.debug('Converted to: ', event)
            self.suppressed_buffer.add(event)
            controllers_expecting_event = [
                controller for controller in self.controllers if controller.check_expected_event(event)]

            # Unless there are suppressing controllers expecting this event (and only them),
            # we immediately replicate/propagate the buffered events.
            if not controllers_expecting_event or any(controller.propagate for controller in controllers_expecting_event):
                self.suppressed_buffer.flush(discard=False)

            # If there is a suppressing controller being triggered, we can discard the buffered events.
            elif controllers_expecting_event and any(controller.next_expected_event_index == 0 for controller in controllers_expecting_event):
                self.suppressed_buffer.flush(discard=True)

            for controller in controllers_expecting_event:
                controller.handle_event(event)

    def add_controller(self, controller: KeyController):
        log.debug(f'Registering controller {type(controller)}')

        for already_registered in self.controllers:
            if already_registered.trigger_events[0] == controller.trigger_events[0] and \
                    already_registered.propagate != controller.propagate:
                log.error('Conflicting controllers: There are at least 2 different controllers associated with a same subset of events, '
                          f'but different propagation policies. Target event: {controller.trigger_events[0]}. Aborting...')
                exit(1)
        self.controllers.append(controller)
