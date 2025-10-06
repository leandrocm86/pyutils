from dataclasses import dataclass
import logging
import sys
from types import FrameType, TracebackType
from os import environ
from typing import Any
from .pstr import pstr
from .style import green, cyan, yellow, red

LOG_FILENAME = environ.get('LOG_FILE')
LOG_LEVEL_NAME = environ.get('LOG_LEVEL', '').upper() or ('DEBUG' if sys.stdout.isatty() else 'INFO')
SYSTEMD = environ.get('SYSTEMD')

LOG_LEVEL_NUMBER: int = getattr(logging, LOG_LEVEL_NAME, -1)
if LOG_LEVEL_NUMBER == -1:
    raise ValueError(f'Nível de log inválido: {LOG_LEVEL_NAME}')

LOG = logging.getLogger()


class CustomFormatter(logging.Formatter):
    COLOR_BY_LEVEL = {
        'DEBUG': green,
        'INFO': cyan,
        'WARNING': yellow,
        'ERROR': red
    }

    def __init__(self, fmt: str = f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
                 datefmt: str = '%d %b %H:%M:%S', colored: bool = False):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.colored = colored

    def format(self, record: logging.LogRecord):
        color = self.COLOR_BY_LEVEL.get(record.levelname) if self.colored else None
        formatted_record = super().format(record)
        return color(formatted_record) if color else formatted_record


# default_formatter = logging.Formatter(
#    f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
#    datefmt='%d %b %H:%M:%S')


if LOG_FILENAME:
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(CustomFormatter())
    LOG.addHandler(file_handler)
    LOG.debug(f'Added file handler for logger with level {LOG_LEVEL_NAME} on file {LOG_FILENAME}')
elif SYSTEMD:
    from systemd import journal
    from types import MappingProxyType
    # Override mapping: INFO (6 on journald) to 5 (notice),
    # to distinguish from the default level 6 for stdout messages.
    # Also remap ERROR (3) to CRITICAL (2) to highlight user errors better.
    journal.JournalHandler.LEVELS = MappingProxyType({
        logging.CRITICAL: 2,
        logging.DEBUG: 7,
        logging.FATAL: 0,
        logging.ERROR: 2,  # 👈 remap ERROR(3) → CRITICAL (2)
        logging.INFO: 5,  # 👈 remap INFO(6) → NOTICE (5)
        logging.NOTSET: 16,
        logging.WARNING: 4,
    })

if not (LOG_FILENAME or SYSTEMD) or sys.stdout.isatty():
    LOG.addHandler(journal.JournalHandler(SYSLOG_IDENTIFIER=SYSTEMD))
    LOG.debug(f'Added journald handler for logger {SYSTEMD} with level {LOG_LEVEL_NAME}')
else:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter(colored=True))
    LOG.addHandler(stream_handler)
    LOG.debug(f'Added stream handler for logger with level {LOG_LEVEL_NAME}')

LOG.setLevel(LOG_LEVEL_NUMBER)


def _concat(*args: tuple[Any, ...]) -> str:
    out = ''
    for arg in args:
        out += arg if isinstance(arg, str) else str(arg)
    return out


def debug(*args: Any):
    if LOG_LEVEL_NUMBER == logging.DEBUG:
        msg = _concat(*args)
        LOG.debug(msg)


def info(*args: Any):
    if LOG_LEVEL_NUMBER <= logging.INFO:
        msg = _concat(*args)
        LOG.info(msg)


def warn(*args: Any):
    if LOG_LEVEL_NUMBER <= logging.WARNING:
        msg = _concat(*args)
        LOG.warning(msg)


def error(*args: Any, exception: bool = False):
    msg = _concat(*args)
    LOG.error(msg, exc_info=exception, stack_info=exception)


@dataclass
class ExceptionsConfig:
    max_frames: int = 3
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
                value_str = pstr(value, colored=ExceptionsConfig.colored_print, maxlen=20, maxdepth=2)
                # Truncate very long values
                print(f"  {name:>{name_padding}} = {value_str}")
            except Exception as e:
                print(f"  {name:>{name_padding}} = <Error: {e}>")
    else:
        print("  (no local variables)")

    print("-" * 60)

    # Show arguments passed to the function
    # if frame.f_code.co_argcount > 0:
#         print("\nFunction arguments:")
#         arg_names = frame.f_code.co_varnames[:frame.f_code.co_argcount]
#         for arg_name in arg_names:
#             if arg_name in locals_dict:
#                 try:
#                     value_str = pstr(locals_dict[arg_name], colored=ExceptionsConfig.colored_print)
#                     if len(value_str) > 200:
#                         value_str = value_str[:200] + "..."
#                     print(f"  {arg_name:15} = {value_str}")
#                 except Exception as e:
#                     print(f"  {arg_name:15} = <Error: {e}>")


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
