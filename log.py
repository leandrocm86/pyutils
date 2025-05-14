import logging
import sys
from os import environ
from typing import Any
from .color import green, cyan, yellow, red

LOG_FILENAME = environ.get('LOG_FILE')
LOG_LEVEL_NAME = environ.get('LOG_LEVEL', '').upper() or ('DEBUG' if sys.stdout.isatty() else 'INFO')

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
                 datefmt: str = '%d %b %H:%M:%S'):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord):
        color = self.COLOR_BY_LEVEL.get(record.levelname)
        formatted_record = super().format(record)
        return color(formatted_record) if color else formatted_record


# default_formatter = logging.Formatter(
#    f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
#    datefmt='%d %b %H:%M:%S')

LOG.setLevel(LOG_LEVEL_NUMBER)

if LOG_FILENAME:
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(CustomFormatter())
    LOG.addHandler(file_handler)
else:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    LOG.addHandler(stream_handler)

LOG.debug(f'Log file: "{LOG_FILENAME}". Log level: {LOG_LEVEL_NAME} ({LOG_LEVEL_NUMBER})')


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
