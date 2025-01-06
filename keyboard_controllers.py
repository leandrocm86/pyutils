from __future__ import annotations
from abc import ABC
from enum import Enum
from pynput import keyboard
import os
import time
import evdev  # pip install evdev
from pyutils.system import System


keyboard_controller = keyboard.Controller()
BACKSPACE = keyboard.Key.backspace
CONTROL_KEYS = {
    42: 'SHIFT',
    29: 'CONTROL',
    56: 'ALT'
}


debugging = False


def debug(msg):
    if debugging:
        msg = '[KeyboardController][DEBUG] ' + msg
        print(msg)


def info(msg):
    msg = '[KeyboardController][INFO] ' + msg
    print(msg)


class TipoEvento(Enum):
    TECLA = 0
    MOV_UP = 1
    MOV_DOWN = 2
    MOV_HOLD = 3


# @dataclass(frozen=True)
class EventoEvdev:
    cod_tipo: int
    value: int
    tipo: TipoEvento

    def __init__(self, cod_tipo: int, value: int):
        self.cod_tipo = cod_tipo
        self.value = value

        if cod_tipo == 4:
            self.tipo = TipoEvento.TECLA
        elif cod_tipo == 1:
            if self.value == 0:
                self.tipo = TipoEvento.MOV_UP
            elif self.value == 1:
                self.tipo = TipoEvento.MOV_DOWN
            elif self.value == 2:
                self.tipo = TipoEvento.MOV_HOLD

        assert self.tipo, 'Nao foi possivel interpretar tipo de evento!'


class KeyboardListener:
    ''' Para que o listener funcione com o evdev, é necessário que o usuário
        esteja no grupo input do sistema: sudo usermod -aG input l86 '''
    def __init__(self) -> None:
        self.controllers_by_key: dict[int, list[KeyController]] = {}
        self.control_keys_pressed: set[str] = set()

    @staticmethod
    def _find_keyboard_device():
        '''Pode ser necessário adicionar o usuário ao grupo input'''
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        keyboards = [device for device in devices if 'keyboard' in device.name]
        if len(keyboards) != 1:
            for device in devices:
                print(device.path, device.name, device.phys)
            raise OSError(f'{len(devices)} devices encontrados, '
                          f'{len(keyboards)} parecem teclado.')
        return keyboards[0]

    def connect(self):
        info('STARTING KEYBOARD LISTENER')
        # Wait for the X server to be ready
        while 'DISPLAY' not in os.environ:
            info("Waiting for X server...")
            time.sleep(5)
        info(f'Display: {os.environ["DISPLAY"]}')

        device = KeyboardListener._find_keyboard_device()

        tecla_pressionada = None
        for event in device.read_loop():
            if not event.code:  # SYNC EVENT
                continue
            evento = EventoEvdev(event.type, event.value)
            if evento.tipo == TipoEvento.TECLA:
                tecla_pressionada = evento
            elif evento.tipo == TipoEvento.MOV_UP:
                assert tecla_pressionada, 'Evento UP sem tecla prévia!'
                debug(f'UP {tecla_pressionada.value}')
                self.on_release(tecla_pressionada.value)
                tecla_pressionada = None
            elif evento.tipo == TipoEvento.MOV_DOWN:
                assert tecla_pressionada, 'Evento DOWN sem tecla prévia!'
                debug(f'DOWN {tecla_pressionada.value}')
                self.on_press(tecla_pressionada.value)
            elif evento.tipo == TipoEvento.MOV_HOLD:
                assert tecla_pressionada, 'Evento HOLD sem tecla prévia!'
                debug(f'HOLD {tecla_pressionada.value}')
                self.on_press(tecla_pressionada.value)
            else:
                print('Nao foi possivel interpretar o evento!')
                print(evdev.categorize(event))

        info('ENDING KEYBOARD LISTENER')

    def on_release(self, keycode):
        if keyname := CONTROL_KEYS.get(keycode):
            self.control_keys_pressed.discard(keyname)
        debug(f'Release event key: {keycode}')
        controllers = self.controllers_by_key.get(keycode)
        if controllers:
            for c in controllers:
                info(f'Calling keyboard controller for key release: {keycode}')
                c.handle_release(self)
        else:
            debug(f'No controller found for {keycode}')

    def on_press(self, keycode):
        if keyname := CONTROL_KEYS.get(keycode):
            self.control_keys_pressed.add(keyname)
        debug(f'Press event key: {keycode}')
        controllers = self.controllers_by_key.get(keycode)
        if controllers:
            for c in controllers:
                info(f'Calling keyboard controller for key press: {keycode}')
                c.handle_press(self)
        else:
            debug(f'No controller found for {keycode}')

    def add_controller(self, controller: KeyController):
        key = controller.key
        debug(f'Registering controller for key {key}')
        self.controllers_by_key.setdefault(key, []).append(controller)


class KeyController(ABC):
    def __init__(self, keycode: int):
        self.key = keycode

    def handle_release(self, listener: KeyboardListener):
        debug(f'Executing release controller for {self.key}')

    def handle_press(self, listener: KeyboardListener):
        debug(f'Executing press controller for {self.key}')

    @staticmethod
    def toggle_program(program: str, minimize_not_kill: bool, wayland=False):
        if wayland:
            KeyController._toggle_program_wayland(program, minimize_not_kill)
        else:
            KeyController._toggle_program_x11(program, minimize_not_kill)

    @staticmethod
    def _toggle_program_x11(prog_name: str, minimize_not_kill: bool):
        cmd = f'xdotool search --onlyvisible --classname {prog_name}'
        window_id = System.read(cmd)
        if window_id:
            if len(window_id.splitlines()) > 1:
                debug(f'Found multiple windows for {prog_name}. '
                      f'Will pick the last one: {window_id}')
                window_id = window_id.splitlines()[-1]
            cmd = f'xprop -id {window_id} WM_STATE'
            opened = 'window state: Normal' in System.read(cmd)
            if opened:
                if minimize_not_kill:
                    cmd = f'xdotool windowminimize {window_id}'
                    System.exec(cmd)
                else:
                    KeyController.execute('killall ' + prog_name)
            else:
                cmd = f'xdotool windowactivate {window_id}'
                System.exec(cmd, ignore_output=True)
        else:
            KeyController.execute(f'nohup {prog_name} &')

    @staticmethod
    def _toggle_program_wayland(prog_name: str, minimize_not_kill: bool):
        gdbus_cmd = 'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval'
        filter_window_cmd = f"global.get_window_actors().map(a=>a.meta_window).filter(w=>w.get_wm_class().toLowerCase() == '{prog_name.lower()}')"
        list_window_state_cmd = f"{filter_window_cmd}.map(w=>({{wmclass: w.get_wm_class(), minimized: w.minimized}}))"

        window_info = System.read(f'{gdbus_cmd} "{list_window_state_cmd}"')
        if '"minimized":' in window_info:
            if '"minimized":false' in window_info:
                debug(f'{prog_name} is running and maximized: {window_info}')
                if minimize_not_kill:
                    min_cmd = f'{filter_window_cmd}.forEach(w=>w.minimize())'
                    System.exec(f'{gdbus_cmd} "{min_cmd}"', ignore_output=True)
                else:
                    KeyController.execute('killall ' + prog_name)
            else:
                debug(f'{prog_name} is running and minimized: {window_info}')
                max_cmd = filter_window_cmd + \
                    '.forEach(w=>{w.unminimize(); w.focus(0); w.make_above()})'
                System.exec(f'{gdbus_cmd} "{max_cmd}"', ignore_output=True)
        else:
            debug(f'{prog_name} has no window: {window_info}')
            KeyController.execute(f'{prog_name} &')

    @staticmethod
    def execute(command: str):
        debug(f'Executing command: {command}')
        System.exec_async(command)


class SingleToChar(KeyController):
    """ Maps a button press to a specific char."""
    def __init__(self, key: int, to_char):
        super().__init__(key)
        self.to_char = to_char

    def handle_release(self, listener: KeyboardListener):
        super().handle_release(listener)
        keyboard_controller.tap(self.to_char)


class DoubleToChar(KeyController):
    """ Maps a double button press to a specific char."""
    def __init__(self, key: int, to_char):
        super().__init__(key)
        self.to_char = to_char

    def handle_release(self, listener: KeyboardListener):
        super().handle_release(listener)
        if hasattr(self, 'last_typed') and time.time() - self.last_typed < 0.2:
            keyboard_controller.tap(self.to_char)
        else:
            self.last_typed = time.time()


class SingleExecute(KeyController):
    """ Maps a button press to a command execution."""
    def __init__(self, key: int, command: str):
        super().__init__(key)
        self.command = command

    def handle_release(self, listener: KeyboardListener):
        super().handle_release(listener)
        KeyController.execute(self.command)


class DoubleToMacro(KeyController):
    """ Maps a double button press to macro text."""
    def __init__(self, keycode: int, macro_text: str):
        super().__init__(keycode)
        self.macro_text = macro_text

    def handle_release(self, listener: KeyboardListener):
        super().handle_release(listener)
        if hasattr(self, 'last_typed') and time.time() - self.last_typed < 0.2:
            debug('digitando mapeamento Double_to_Macro')
            keyboard_controller.tap(BACKSPACE)
            keyboard_controller.tap(BACKSPACE)
            keyboard_controller.type(self.macro_text)
        else:
            debug('no last_typed' if not hasattr(self, 'last_typed')
                  else str(time.time() - self.last_typed))
            self.last_typed = time.time()


class HoldToMacro(KeyController):
    """ Maps a long button press to macro text."""
    def __init__(self, keycode: int, macro_text: str):
        super().__init__(keycode)
        self.macro_text = macro_text
        self.total_presses = 0

    def handle_press(self, listener: KeyboardListener):
        super().handle_press(listener)
        self.total_presses += 1
        debug(f'Total presses: {self.total_presses}')
        # if self.total_presses >= 2:
        # keyboard_controller.tap(BACKSPACE)
        if (self.total_presses == 2):
            debug('digitando mapeamento Hold_To_Macro')
            keyboard_controller.tap(BACKSPACE)
            keyboard_controller.type(self.macro_text)

    def handle_release(self, listener: KeyboardListener):
        super().handle_release(listener)
        self.total_presses = 0


class ShiftToMacro(KeyController):
    def __init__(self, keycode: int, macro_text: str):
        super().__init__(keycode)
        self.macro_text = macro_text

    def handle_release(self, listener: KeyboardListener):
        super().handle_press(listener)
        if 'SHIFT' in listener.control_keys_pressed:
            keyboard_controller.type(self.macro_text)


class ControlShiftToProgram(KeyController):
    def __init__(self, keycode: int, program: str,
                 minimize_not_kill=False, wayland=False):
        super().__init__(keycode)
        self.program = program
        self.minimize_not_kill = minimize_not_kill
        self.wayland = wayland

    def handle_release(self, listener: KeyboardListener):
        super().handle_press(listener)
        control_keys = 'CONTROL', 'SHIFT'
        if all(k in listener.control_keys_pressed for k in control_keys):
            KeyController.toggle_program(self.program, self.minimize_not_kill,
                                         wayland=self.wayland)


class ControlAltToProgram(KeyController):
    def __init__(self, keycode: int, program: str,
                 minimize_not_kill=False, wayland=False):
        super().__init__(keycode)
        self.program = program
        self.minimize_not_kill = minimize_not_kill
        self.wayland = wayland

    def handle_release(self, listener: KeyboardListener):
        super().handle_press(listener)
        control_keys = 'CONTROL', 'ALT'
        if all(k in listener.control_keys_pressed for k in control_keys):
            KeyController.toggle_program(self.program, self.minimize_not_kill,
                                         wayland=self.wayland)


class KeyToProgram(KeyController):
    def __init__(self, keycode: int, program: str,
                 minimize_not_kill=False, wayland=False):
        super().__init__(keycode)
        self.program = program
        self.minimize_not_kill = minimize_not_kill
        self.wayland = wayland

    def handle_release(self, listener: KeyboardListener):
        super().handle_press(listener)
        KeyController.toggle_program(self.program, self.minimize_not_kill,
                                     wayland=self.wayland)
