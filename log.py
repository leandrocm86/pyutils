from dataclasses import dataclass
import logging
import sys
from types import FrameType, TracebackType
from os import environ
from typing import Any
import re
from .pstr import pstr
from . import style

LOG_FILENAME = environ.get('LOG_FILE')
LOG_LEVEL_NAME = environ.get('LOG_LEVEL', '').upper() or ('DEBUG' if sys.stdout.isatty() else 'INFO')
SYSTEMD = environ.get('SYSTEMD')

LOG_LEVEL_NUMBER: int = getattr(logging, LOG_LEVEL_NAME, -1)
if LOG_LEVEL_NUMBER == -1:
    raise ValueError(f'Nível de log inválido: {LOG_LEVEL_NAME}')

LOG = logging.getLogger()
LOG.setLevel(LOG_LEVEL_NUMBER)


class CustomFormatter(logging.Formatter):
    COLORS_BY_LEVEL: dict[str, tuple[style.Painter, style.Painter]] = {
        'DEBUG': (style.get_painter(background=style.BGCOLOR.GRAY),
                  style.get_painter(style.Color.LOW_WHITE)),
        'INFO': (style.get_painter(background=style.BGCOLOR.CYAN),
                 style.get_painter(style.Color.CYAN)),
        'WARNING': (style.get_painter(background=style.BGCOLOR.BRIGHT_YELLOW),
                    style.get_painter(style.Color.YELLOW)),
        'ERROR': (style.get_painter(background=style.BGCOLOR.RED),
                  style.get_painter(style.Color.RED))
    }
    PRIMITIVES = (int, str, bool, float)
    PARAM_COLOR_START = style.Color.ORANGE.value
    PARAM_COLOR_RESET = '\033[0m'

    # def __init__(self, fmt: str = f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
    def __init__(self, fmt: str = '%(asctime)s [%(levelname)s] %(message)s',
                 datefmt: str = '%d %b %H:%M:%S', colored: bool = False):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.colored = colored

    def format(self, record: logging.LogRecord):
        if self.colored and record.args:
            # Wrap the placeholders with a highlight color
            record.msg = re.sub(
                r'(%[-#0 +]?(?:\*|\d+)?(?:\.(?:\*|\d+))?[hlL]?[diouxXeEfFgGcrs])',
                self.PARAM_COLOR_START + r'\1' + self.PARAM_COLOR_RESET,
                record.msg
            )

        # Let super().format() do the actual formatting
        formatted_msg = super().format(record)

        # Apply header and message coloring
        header_painter, message_painter = self.COLORS_BY_LEVEL.get(record.levelname, (None, None)) if self.colored else (None, None)
        if message_painter and header_painter:
            index_message = 11 + len(record.levelname)
            return header_painter(formatted_msg[:index_message]) + message_painter(formatted_msg[index_message:])
        else:
            return formatted_msg

handlers_msgs: list[str] = []

if LOG_FILENAME:
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(CustomFormatter())
    LOG.addHandler(file_handler)
    handlers_msgs.append(f'Added file handler for logger with level {LOG_LEVEL_NAME} on file {LOG_FILENAME}')
if SYSTEMD:
    # sudo apt install libsystemd-dev pkg-config; pip install systemd-python
    from .system import install_external_libs
    install_external_libs({'systemd': 'systemd-python'})
    from systemd import journal
    from types import MappingProxyType
    # Override mapping: INFO (6 on journald) to 5 (notice),
    # to distinguish from the default level 6 for stdout messages.
    # Also remap ERROR (3) to CRITICAL (2) to highlight user errors better.
    LEVELS = MappingProxyType({
        logging.CRITICAL: 2,
        logging.DEBUG: 7,
        logging.FATAL: 0,
        logging.ERROR: 2,  # 👈 remap ERROR(3) → CRITICAL (2)
        logging.INFO: 5,  # 👈 remap INFO(6) → NOTICE (5)
        logging.NOTSET: 16,
        logging.WARNING: 4,
    })
    try:
        journal.JournalHandler.LEVELS = LEVELS
        LOG.addHandler(journal.JournalHandler(SYSLOG_IDENTIFIER=SYSTEMD))
        handlers_msgs.append(f'Added JournalHandler for logger {SYSTEMD} with level {LOG_LEVEL_NAME}')
    except Exception:
        journal.JournaldLogHandler.LEVELS = LEVELS
        LOG.addHandler(journal.JournaldLogHandler(SYSTEMD))
        handlers_msgs.append(f'Added JournaldLogHandler for logger {SYSTEMD} with level {LOG_LEVEL_NAME}')

if not (LOG_FILENAME or SYSTEMD) or sys.stdout.isatty():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter(colored=True, datefmt='%H:%M:%S'))
    LOG.addHandler(stream_handler)
    handlers_msgs.append(f'Added stream handler for logger with level {LOG_LEVEL_NAME}')


print('. '.join(handlers_msgs))
LOG.debug('. '.join(handlers_msgs))


def debug(*args: Any):
    LOG.debug(*args)


def info(*args: Any):
    LOG.info(*args)


def warn(*args: Any):
    LOG.warning(*args)


def error(*args: Any, exception: bool = False):
    LOG.error(*args, exc_info=exception, stack_info=exception)


@dataclass
class ExceptionsConfig:
    max_frames: int = 1 if sys.stdout.isatty() else 3
    colored_print: bool = sys.stdout.isatty()
    suppress_default_stacktrace: bool = False


def __get_source_line(filename: str, line_number: int) -> str:
    import linecache
    """Get the source code line using linecache (same as done by traceback module)."""
    return linecache.getline(filename, line_number).strip()


def __print_frame_info(frame: FrameType, line_number: int, frame_number: int, max_frames: int):
    filename = frame.f_code.co_filename
    function_name = frame.f_code.co_name

    file_and_line = f"{filename}:{line_number}"
    if max_frames == frame_number + 1 and '.py:' in file_and_line:
        file_and_line = f"\033[31m{file_and_line}\033[0m"

    source_line = __get_source_line(filename, line_number)

    print(f"{function_name}() in {file_and_line} => {source_line}")

    locals_dict = frame.f_locals
    if frame_number == 0:
        # Em __main__ e repl, ignora o que nao foi usado na linha do erro
        locals_dict = {name: value for name, value in locals_dict.items() if name in source_line}
    if locals_dict:
        name_padding = max(len(name) for name in locals_dict.keys())
        for name, value in sorted(locals_dict.items()):
            try:
                # Use pstr for better formatting of complex objects
                maxlen = 50 if isinstance(value, str) else 10
                value_str = pstr(value, colored=ExceptionsConfig.colored_print, maxlen=maxlen, maxdepth=3)
                # Truncate very long values
                print(f"  {name:>{name_padding}} = {value_str}")
            except Exception as e:
                print(f"  {name:>{name_padding}} = <Error: {e}>")
    else:
        print("  (no local variables)")

    print("-" * 60)


def _inspect_exception_hook(exc_type: type,
                            exc_value: BaseException,
                            exc_traceback: TracebackType):
    """ Advanced exception handler that prints variables from stack frames """

    MAX_FRAMES: int = ExceptionsConfig.max_frames

    LOG.error(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}")
    print("=" * 64)

    # Print the normal traceback first
    if not ExceptionsConfig.suppress_default_stacktrace:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        # traceback.print_exception(exc_type, exc_value, exc_traceback)

    # Collect all frames first
    frames: list[tuple[FrameType, int]] = []
    tb = exc_traceback
    while tb is not None:
        frames.append((tb.tb_frame, tb.tb_lineno))
        tb = tb.tb_next

    # Remove frame 0 (__main__)
    frames.pop(0)

    if not frames:
        print("No frames to inspect in traceback")
        return

    print("=" * 25 + " STACK DETAILS " + "=" * 25)

    # Limit to last max_frames if specified
    if len(frames) > MAX_FRAMES:
        frames = frames[-MAX_FRAMES:]
        # print(f"(Showing last {MAX_FRAMES} frames out of {len(frames) + (len(frames) - MAX_FRAMES)} total)")

    # Print each frame
    for frame_number, (frame, line_number) in enumerate(frames):
        __print_frame_info(frame, line_number, frame_number, min(ExceptionsConfig.max_frames, len(frames)))


sys.excepthook = _inspect_exception_hook
