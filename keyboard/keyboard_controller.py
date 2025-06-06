from enum import Enum
from abc import ABC, abstractmethod
from time import sleep, time
from .. import log, system
from .keyboard_robot import KeyboardRobot
from .keyboard_events import EventType, KeyboardEvent


class EventResult(Enum):
    """Identifies the possible results of the processing of a keyboard event by a keyboard controller.
    NO_ACTION: Means the event is irrelevant and is not part of any action trigger.
    POSSIBLE_ACTION: Means the event is part of an action trigger that might get completed in following events.
    ACTION_SUPPRESS: Means the event triggered an action and the triggers must be suppresed to the system.
    ACTION_PROPAGATE: Means the event triggered an action but the triggers can propagate to the system.
    """
    NO_ACTION = 0
    POSSIBLE_ACTION = 1
    ACTION_SUPPRESS = 2
    ACTION_PROPAGATE = 3


class ActionExecutor(ABC):
    """Interface for classes that execute actions triggered by keyboard controllers."""
    @abstractmethod
    def execute(self) -> None:
        """Method to be implemented by subclasses to execute the action triggered by the controller."""
        raise NotImplementedError('All ActionExecutors must implement the execute method.')


class KeyController(ABC):
    """Base class for keyboard controllers.
    KeyControllers may trigger custom actions when a sequence of events are processed.
    By default, they propagate these events to the system, but they can suppress them with propagate=False.
    """
    def __init__(self, trigger_events: tuple[KeyboardEvent, ...], action: ActionExecutor, propagate: bool = True):
        assert trigger_events != (), 'All controllers must be bound with at least one trigger event.'
        for event in trigger_events:
            assert isinstance(event, KeyboardEvent), f'Event {event} is {type(event)}'
        self.trigger_events = trigger_events
        self.next_expected_event_index = 0
        self.action = action
        self.propagate = propagate

    def _check_expected_event(self, event: KeyboardEvent) -> bool:
        """Checks if the given event matches the next expected event in the controller's trigger sequence.
        It also updates the next expected event index accordingly.
        Returns True if the event matches the expected one, False otherwise.
        """
        if event == self.trigger_events[self.next_expected_event_index]:
            if len(self.trigger_events) == self.next_expected_event_index + 1:
                self.next_expected_event_index = 0
            else:
                self.next_expected_event_index += 1
            return True
        else:
            self.next_expected_event_index = 0
            return False

    def handle_event(self, event: KeyboardEvent) -> EventResult:
        """Default implementation for event handling to be called by the KeyboardListener at each event.
        It checks if the sequence of last events match the trigger events needed to execute an action.
        Returns the result of the event processing, indicating to the listener what to do with the original events.
        """
        if self._check_expected_event(event):
            if self.next_expected_event_index == 0:
                self.action.execute()
                return EventResult.ACTION_PROPAGATE if self.propagate else EventResult.ACTION_SUPPRESS
            return EventResult.POSSIBLE_ACTION
        return EventResult.NO_ACTION


# ===== COMMON KEY CONTROLLERS: =====

class TextMacroAction(ActionExecutor):
    """Used in controllers for text macros, typing each character with 10ms intervals.
    Each character in the given macro_text is searched in KeyboardEvent's dictionary, and two events are generated with its code (down and up).
    If the character is uppercase, additional shift events (up and down) are generated surrounding the character's (lowercase form) events.
    Additionally, if the character is a special character (present in shift_dictionary), the shift events are also generated for it.
    Notice that for this controller to work as intended, each character (1 letter) must correspond to a code in KeyboardEvent.dictionary or KeyboardEvent.shift_dictionary.
    """
    def __init__(self, keyboard_robot: KeyboardRobot, macro_text: str):
        self.keyboard_robot = keyboard_robot
        self.macro_sequence: list[KeyboardEvent] = []
        for char in macro_text:
            if char.isupper():
                self.macro_sequence.append(KeyboardEvent.from_dictionary('shift', EventType.MOV_DOWN))
                self.macro_sequence.append(KeyboardEvent.from_dictionary(char.lower(), EventType.MOV_DOWN))
                self.macro_sequence.append(KeyboardEvent.from_dictionary(char.lower(), EventType.MOV_UP))
                self.macro_sequence.append(KeyboardEvent.from_dictionary('shift', EventType.MOV_UP))
            else:
                self.macro_sequence += KeyboardEvent.from_dictionary_tap(char)

    def execute(self) -> None:
        log.debug('Typing macro text: ', self.macro_sequence)
        for macro_event in self.macro_sequence:
            self.keyboard_robot.input_event(macro_event)
            sleep(0.01)


class MouseAction(ActionExecutor):
    """Base class for mouse actions.
    It encapsulates its own pynput.MouseController instance to perform the mouse actions.
    The pynput module is lazy loaded through the get_mouse_robot() method, to avoid errors before X11 is available.
    """
    def __init__(self):
        self.__mouse_robot = None

    def _get_mouse_robot(self):
        if not self.__mouse_robot:
            from pynput.mouse import Controller as MouseController
            self.__mouse_robot = MouseController()
        return self.__mouse_robot


class ExecuteCommandAction(ActionExecutor):
    """Executes a shell command when triggered."""
    def __init__(self, command: str):
        self.command = command

    def execute(self) -> None:
        system.exec_async(self.command)


class ToggleProgramAction(ActionExecutor):
    """Toggles a program window.
    If the program is not running, it starts it.
    If the program is running and minimized, it restores it.
    If the program is running and maximized, it minimizes or kill it (depending on minimize_not_kill).
    """
    def __init__(self, program: str, minimize_not_kill: bool, wayland: bool):
        self.program = program
        self.minimize_not_kill = minimize_not_kill
        self.wayland = wayland

    def execute(self):
        if self.wayland:
            self._toggle_program_wayland()
        else:
            self._toggle_program_x11()

    def _toggle_program_x11(self):
        window_id = system.read(f'xdotool search --onlyvisible --classname {self.program}', check=False)
        if window_id:
            if len(window_id.splitlines()) > 1:
                log.debug(f'Found multiple windows for {self.program}. Will pick the last one: {window_id}')
                window_id = window_id.splitlines()[-1]
            opened = 'window state: Normal' in system.read(f'xprop -id {window_id} WM_STATE')
            if opened:
                if self.minimize_not_kill:
                    system.exec(f'xdotool windowminimize {window_id}')
                else:
                    system.exec_async('killall ' + self.program)
            else:
                cmd = f'xdotool windowactivate {window_id}'
                system.exec(cmd, ignore_output=True)
        else:
            system.exec_async(f'nohup {self.program} &')

    def _toggle_program_wayland(self):
        gdbus_cmd = 'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval'
        filter_window_cmd = f"global.get_window_actors().map(a=>a.meta_window).filter(w=>w.get_wm_class().toLowerCase() == '{self.program.lower()}')"
        list_window_state_cmd = f"{filter_window_cmd}.map(w=>({{wmclass: w.get_wm_class(), minimized: w.minimized}}))"

        window_info = system.read(f'{gdbus_cmd} "{list_window_state_cmd}"')
        if '"minimized":' in window_info:
            if '"minimized":false' in window_info:
                log.debug(f'{self.program} is running and maximized: {window_info}')
                if self.minimize_not_kill:
                    min_cmd = f'{filter_window_cmd}.forEach(w=>w.minimize())'
                    system.exec(f'{gdbus_cmd} "{min_cmd}"', ignore_output=True)
                else:
                    system.exec_async('killall ' + self.program)
            else:
                log.debug(f'{self.program} is running and minimized: {window_info}')
                max_cmd = filter_window_cmd + \
                    '.forEach(w=>{w.unminimize(); w.focus(0); w.make_above()})'
                system.exec(f'{gdbus_cmd} "{max_cmd}"', ignore_output=True)
        else:
            log.debug(f'{self.program} has no window: {window_info}')
            system.exec_async(f'{self.program} &')


class DoubleTapController(KeyController):
    """A controller that only triggers an action when a key is double tapped within a given time interval."""
    def __init__(self, trigger_key: str, repetition_time: float, action: ActionExecutor, propagate: bool = True):
        KeyController.__init__(self, KeyboardEvent.from_dictionary_tap(trigger_key), action, propagate)
        self.repetition_time = repetition_time
        self.last_tap_timestamp = 0

    def handle_event(self, event: KeyboardEvent) -> EventResult:
        if self._check_expected_event(event):
            if self.next_expected_event_index == 0:
                if time() - self.last_tap_timestamp < self.repetition_time:
                    self.action.execute()
                    return EventResult.ACTION_PROPAGATE if self.propagate else EventResult.ACTION_SUPPRESS
                else:
                    self.last_tap_timestamp = time()
                    return EventResult.POSSIBLE_ACTION
            return EventResult.POSSIBLE_ACTION
        return EventResult.NO_ACTION


# class SingleToChar(KeyController):
#     """ Maps a button press to a specific char."""
#     def __init__(self, key: int, to_char: str):
#         super().__init__(key)
#         self.to_char = to_char

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_release(listener)
#         keyboard_controller.tap(self.to_char)
#         return ResultadoEvento.GEROU_ACAO


# class DoubleToChar(KeyController):
#     """ Maps a double button press to a specific char."""
#     def __init__(self, key: int, to_char):
#         super().__init__(key)
#         self.to_char = to_char

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_release(listener)
#         if hasattr(self, 'last_typed') and time.time() - self.last_typed < 0.2:
#             keyboard_controller.tap(self.to_char)
#         else:
#             self.last_typed = time.time()


# class SingleExecute(KeyController):
#     """ Maps a button press to a command execution."""
#     def __init__(self, key: int, command: str):
#         super().__init__(key)
#         self.command = command

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_release(listener)
#         KeyController.execute(self.command)


# class DoubleToMacro(KeyController):
#     """ Maps a double button press to macro text."""
#     def __init__(self, keycode: int, macro_text: str):
#         super().__init__(keycode)
#         self.macro_text = macro_text

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_release(listener)
#         if hasattr(self, 'last_typed') and time.time() - self.last_typed < 0.2:
#             debug('digitando mapeamento Double_to_Macro')
#             keyboard_controller.tap(BACKSPACE)
#             keyboard_controller.tap(BACKSPACE)
#             keyboard_controller.type(self.macro_text)
#         else:
#             debug('no last_typed' if not hasattr(self, 'last_typed')
#                   else str(time.time() - self.last_typed))
#             self.last_typed = time.time()


# class HoldToMacro(KeyController):
#     """ Maps a long button press to macro text."""
#     def __init__(self, keycode: int, macro_text: str):
#         super().__init__(keycode)
#         self.macro_text = macro_text
#         self.total_presses = 0

#     def handle_press(self, listener: KeyboardListener):
#         super().handle_press(listener)
#         self.total_presses += 1
#         debug(f'Total presses: {self.total_presses}')
#         if (self.total_presses == 2):
#             debug('digitando mapeamento Hold_To_Macro')
#             keyboard_controller.tap(BACKSPACE)
#             keyboard_controller.type(self.macro_text)

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_release(listener)
#         self.total_presses = 0


# class ShiftToMacro(KeyController):
#     def __init__(self, keycode: int, macro_text: str):
#         super().__init__(keycode)
#         self.macro_text = macro_text

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_press(listener)
#         if 'SHIFT' in listener.control_keys_pressed:
#             keyboard_controller.type(self.macro_text)


# class ControlShiftToProgram(KeyController):
#     def __init__(self, keycode: int, program: str,
#                  minimize_not_kill=False, wayland=False):
#         super().__init__(keycode)
#         self.program = program
#         self.minimize_not_kill = minimize_not_kill
#         self.wayland = wayland

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_press(listener)
#         control_keys = 'CONTROL', 'SHIFT'
#         if all(k in listener.control_keys_pressed for k in control_keys):
#             KeyController.toggle_program(self.program, self.minimize_not_kill,
#                                          wayland=self.wayland)


# class ControlAltToProgram(KeyController):
#     def __init__(self, keycode: int, program: str,
#                  minimize_not_kill=False, wayland=False):
#         super().__init__(keycode)
#         self.program = program
#         self.minimize_not_kill = minimize_not_kill
#         self.wayland = wayland

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_press(listener)
#         control_keys = 'CONTROL', 'ALT'
#         if all(k in listener.control_keys_pressed for k in control_keys):
#             KeyController.toggle_program(self.program, self.minimize_not_kill,
#                                          wayland=self.wayland)


# class KeyToProgram(KeyController):
#     def __init__(self, keycode: int, program: str,
#                  minimize_not_kill=False, wayland=False):
#         super().__init__(keycode)
#         self.program = program
#         self.minimize_not_kill = minimize_not_kill
#         self.wayland = wayland

#     def handle_release(self, listener: KeyboardListener):
#         super().handle_press(listener)
#         KeyController.toggle_program(self.program, self.minimize_not_kill,
#                                      wayland=self.wayland)
