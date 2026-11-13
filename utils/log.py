import logging
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from os import environ
from types import FrameType, TracebackType
from typing import Any
from . import style
lazy from utils.pstr import pstr


RE_PLACEHOLDER = re.compile(r"(%p(?:\.(\d+))?(?:\.(\d+))?)|(%%)|(%[-#0 +]?(?:\*|\d+)?(?:\.(?:\*|\d+))?[hlL]?[diouxXeEfFgGcrs])")  # noqa: B950
LOG_FILENAME = environ.get("LOG_FILE")
LOG_LEVEL_NAME = environ.get("LOG_LEVEL", "").upper() or (
    "DEBUG" if sys.stdout.isatty() else "INFO"
)
SYSTEMD = environ.get("JOURNAL_STREAM")  # environ.get('SYSTEMD')

LOG_LEVEL_NUMBER: int = getattr(logging, LOG_LEVEL_NAME, -1)
if LOG_LEVEL_NUMBER == -1:
    raise ValueError(f"Nível de log inválido: {LOG_LEVEL_NAME}")

LOG = logging.getLogger()
LOG.setLevel(LOG_LEVEL_NUMBER)


handlers_msgs: list[str] = []

if LOG_FILENAME:
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(logging.Formatter())  # Default formatter for log files.
    LOG.addHandler(file_handler)
    handlers_msgs.append(f"Added file handler for logger with level {LOG_LEVEL_NAME} on file {LOG_FILENAME}")


if SYSTEMD:
    class JournalFormatter(logging.Formatter):
        JOURNALD_PRIORITY_BY_LEVEL: Mapping[str, int] = {"DEBUG": 7, "INFO": 5, "WARNING": 4, "ERROR": 2}

        def __init__(self):
            super().__init__(fmt="[%(levelname)s] %(message)s", datefmt=None)

        def format(self, record: logging.LogRecord) -> str:
            msg_priority = self.JOURNALD_PRIORITY_BY_LEVEL.get(record.levelname, 6)
            return f"<{msg_priority}>{super().format(record)}"

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JournalFormatter())
    LOG.addHandler(stream_handler)
    handlers_msgs.append(f"Added JournalHandler for logger {SYSTEMD} with level {LOG_LEVEL_NAME}")


if not (LOG_FILENAME or SYSTEMD) or sys.stdout.isatty():
    class ColorFormatter(logging.Formatter):
        def __init__(self):
            super().__init__(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
            self.COLORS_BY_LEVEL: Mapping[str, tuple[style.Painter, style.Painter]] = {
                "DEBUG": (
                    style.get_painter(background=style.BGCOLOR.GRAY),
                    style.get_painter(style.Color.LOW_WHITE),
                ),
                "INFO": (
                    style.get_painter(background=style.BGCOLOR.CYAN),
                    style.get_painter(style.Color.CYAN),
                ),
                "WARNING": (
                    style.get_painter(background=style.BGCOLOR.BRIGHT_YELLOW),
                    style.get_painter(style.Color.YELLOW),
                ),
                "ERROR": (
                    style.get_painter(background=style.BGCOLOR.RED),
                    style.get_painter(style.Color.RED),
                ),
            }
            self.PARAM_COLOR_START = style.Color.ORANGE.value
            self.PARAM_COLOR_RESET = "\033[0m"

            def format(self, record: logging.LogRecord):
                if record.args:
                    args = list(record.args) if isinstance(record.args, tuple) else [record.args]
                    new_args: list[Any] = []
                    arg_index = 0

                    def replace_placeholder(match):
                        nonlocal arg_index
                        if match.group(1):  # %p
                            maxlen = int(match.group(2)) if match.group(2) else 50
                            maxdepth = int(match.group(3)) if match.group(3) else 3
                            pretty = pstr(
                                args[arg_index],
                                colored=True,
                                maxlen=maxlen,
                                maxdepth=maxdepth,
                            )
                            new_args.append(pretty)
                            arg_index += 1
                            return "%s"  # no color wrapping — intentionally plain
                        elif match.group(4):  # %%
                            return "%%"
                        else:  # standard placeholder
                            new_args.append(args[arg_index])
                            arg_index += 1
                            return self.PARAM_COLOR_START + match.group(5) + self.PARAM_COLOR_RESET
                    record.msg = RE_PLACEHOLDER.sub(replace_placeholder, record.msg)
                    record.args = tuple(new_args)

                var_formatted_msg = super().format(record)

                header_painter, message_painter = self.COLORS_BY_LEVEL.get(record.levelname, (None, None))
                if message_painter and header_painter:
                    index_message = 11 + len(record.levelname)
                    var_formatted_msg = (
                        header_painter(var_formatted_msg[:index_message])
                        + message_painter(var_formatted_msg[index_message:])
                    )

                return var_formatted_msg

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(ColorFormatter())
    LOG.addHandler(stream_handler)
    handlers_msgs.append(f"Added stream handler for logger with level {LOG_LEVEL_NAME}")


# print(". ".join(handlers_msgs), flush=True)
LOG.debug(". ".join(handlers_msgs))


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
    max_frames: int = 3 if sys.stdout.isatty() else 5
    colored_print: bool = sys.stdout.isatty()
    suppress_default_stacktrace: bool = False


def __get_source_line(filename: str, line_number: int) -> str:
    import linecache

    """Get the source code line using linecache (same as done by traceback module)."""
    return linecache.getline(filename, line_number).strip()


def __print_frame_info(frame: FrameType, line_number: int, frame_number: int, max_frames: int):
    filename = frame.f_code.co_filename
    function_name = frame.f_code.co_name

    var_file_and_line = f"{filename}:{line_number}"
    if max_frames == frame_number + 1 and ".py:" in var_file_and_line:
        var_file_and_line = f"\033[31m{var_file_and_line}\033[0m"

    source_line = __get_source_line(filename, line_number)

    print(f"{function_name}() in {var_file_and_line} => {source_line}")

    var_locals_dict = frame.f_locals
    if frame_number == 0:
        # Em __main__ e repl, ignora o que nao foi usado na linha do erro
        var_locals_dict = {
            name: value for name, value in var_locals_dict.items() if name in source_line
        }
    if var_locals_dict:
        # name_padding = max(len(name) for name in locals_dict.keys())
        for name, value in sorted(var_locals_dict.items()):
            try:
                # Use pstr for better formatting of complex objects
                maxlen = 50 if isinstance(value, str) else 4
                value_str = pstr(
                    value,
                    colored=ExceptionsConfig.colored_print,
                    maxlen=maxlen,
                    maxdepth=3,
                )
                # Truncate very long values
                # print(f"  {name:>{name_padding}} = {value_str}")
                if sys.stdout.isatty():
                    print(f"\x1b[1m{name}\x1b[0m = {value_str}\n")
                else:
                    print(f"{name} = {value_str}")
            except Exception as e:
                print(f"{name} = <Error: {e}>")
    else:
        print("  (no local variables)")

    print("-" * 50)


def _inspect_exception_hook(exc_type: type[BaseException],
                            exc_value: BaseException,
                            exc_traceback: TracebackType | None) -> Any:
    """Advanced exception handler that prints variables from stack frames"""

    MAX_FRAMES: int = ExceptionsConfig.max_frames

    LOG.error(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}")
    print("=" * 62)

    # Print the normal traceback first
    if not ExceptionsConfig.suppress_default_stacktrace:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        # traceback.print_exception(exc_type, exc_value, exc_traceback)

    # Collect all frames first
    frames: list[tuple[FrameType, int]] = []
    var_tb = exc_traceback
    while var_tb is not None:
        frames.append((var_tb.tb_frame, var_tb.tb_lineno))
        var_tb = var_tb.tb_next

    # Remove frame 0 (__main__)
    frames.pop(0)

    if not frames:
        print("No frames to inspect in traceback")
        return

    print("=" * 20 + " STACK DETAILS " + "=" * 20)

    # Limit to last max_frames if specified
    if len(frames) > MAX_FRAMES:
        frames = frames[-MAX_FRAMES:]
        # print(f"(Showing last {MAX_FRAMES} frames out of {len(frames) + (len(frames) - MAX_FRAMES)} total)")

    # Print each frame
    for frame_number, (frame, line_number) in enumerate(frames):
        __print_frame_info(
            frame,
            line_number,
            frame_number,
            min(ExceptionsConfig.max_frames, len(frames)),
        )


sys.excepthook = _inspect_exception_hook
