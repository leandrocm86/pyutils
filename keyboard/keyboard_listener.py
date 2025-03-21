from __future__ import annotations
# import os
# import time
import evdev  # pip install evdev (parece ser linux-only)
from .. import log
from .keyboard_controller import KeyController, EventResult
from .keyboard_robot import KeyboardRobot
from .keyboard_events import KeyboardEvent


def _find_keyboard_device(device_path: str, device_name: str) -> evdev.InputDevice:
    """Tries to find the keyboard device with the given path and name.
    If no path and name are given, it tries to find the only keyboard device available, raising an error if it can't.
    IMPORTANT: It may be needed to add the system user to the input group (ex: sudo usermod -aG input username).
    """
    devices_str: list[str] = evdev.list_devices()  # type: ignore
    devices: list[evdev.InputDevice] = [
        evdev.InputDevice(path) for path in devices_str]
    if device_name and device_path:
        device = next((d for d in devices if device_path ==
                      d.path and device_name == d.name), None)  # type: ignore
        assert device, f'No device found with name {device_name} in {device_path}'
        log.info(f'Keyboard found with the given path and name: {device_path} - {device.name}')
        return device
    else:
        keyboards = [
            device for device in devices if 'keyboard' in device.name.lower()]
        if len(keyboards) != 1:
            for device in devices:
                print(device.path, device.name, device.phys)  # type: ignore
            raise OSError(f'{len(devices)} devices found, {len(keyboards)} seem keyboards. Check the list printed above.')
        log.info(f'Only keyboard found: {keyboards[0].path} - {keyboards[0].name}')  # type: ignore
        return keyboards[0]


class KeyboardListener:
    """Listens to keyboard events from a given device and calls controllers for each event.
    If no device is specified, it tries to figure out the only keyboard device available (and raises an error if it can't tell).
    It must be supplied with a keyboard_robot to re-send intercepted events to the system.
    """
    def __init__(self, keyboard_robot: KeyboardRobot) -> None:
        self.keyboard_robot = keyboard_robot
        self.controllers: list[KeyController] = []
        self.buffered_events: list[KeyboardEvent] = []

    def connect(self, device_path: str = '', device_name: str = ''):
        assert (device_path and device_name) or (not device_path and not device_name), \
            'If path or name of the keyboard are specified, both must be, to ensure consistency.'

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

    def __listen_event_loop(self, device: evdev.InputDevice):
        for event in device.read_loop():  # type: ignore
            if not isinstance(event, evdev.events.InputEvent) or not event.code \
                    or event.type >= 3:   # SYNC EVENT or other non-key event
                continue
            log.debug('Captured event: ', event)
            event = KeyboardEvent.from_evdev(event)
            log.debug('Converted to: ', event)
            self.buffered_events.append(event)
            controller_results: list[EventResult] = []
            for controller in self.controllers:
                controller_results.append(controller.handle_event(event))
            log.debug('Controller results: ', controller_results)
            self.__handle_results(controller_results)

    def __handle_results(self, controller_results: list[EventResult]):
        if all(result == EventResult.NO_ACTION for result in controller_results) \
                or EventResult.ACTION_PROPAGATE in controller_results:  # Propagation has priority if mixed results.
            for event in self.buffered_events:
                self.keyboard_robot.input_event(event)
            self.buffered_events.clear()
        elif EventResult.ACTION_SUPPRESS in controller_results:
            self.buffered_events.clear()
#       elif EventResult.POSSIBLE_ACTION in controller_results:
#           pass
# When there is a POSSIBLE_ACTION ongoing, but no action was triggered, the events keep getting buffered.

    def add_controller(self, controller: KeyController):
        log.debug(f'Registering controller {type(controller)}')
        self.controllers.append(controller)
