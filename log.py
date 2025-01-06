import logging
import sys
from os import environ
from mods.colors import green, cyan, yellow, red

LOG_FILENAME = environ.get('LOG_FILE')
LOG_LEVEL_NAME = environ.get('LOG_LEVEL', '').upper()
if not LOG_LEVEL_NAME:
    LOG_LEVEL_NAME = 'DEBUG' if sys.stdout.isatty() else 'INFO'

LOG_LEVEL_NUMBER = getattr(logging, LOG_LEVEL_NAME, None)
if not isinstance(LOG_LEVEL_NUMBER, int):
    raise ValueError(f'Nível de log inválido: {LOG_LEVEL_NAME}')

LOG = logging.getLogger()


class CustomFormatter(logging.Formatter):
    COLOR_BY_LEVEL = {
        'DEBUG': green,
        'INFO': cyan,
        'WARNING': yellow,
        'ERROR': red
    }

    def __init__(self, fmt=f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
                 datefmt='%d %b %H:%M:%S'):
        super().__init__(fmt)

    def format(self, record):
        color = self.COLOR_BY_LEVEL.get(record.levelname)
        formatted_record = super().format(record)
        return color(formatted_record) if color else formatted_record


# default_formatter = logging.Formatter(
#    f'%(asctime)s [{sys.argv[0]}] [%(levelname)s] %(message)s',
#    datefmt='%d %b %H:%M:%S')

LOG.setLevel(LOG_LEVEL_NUMBER)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomFormatter())
LOG.addHandler(stream_handler)

LOG.info(f'Log file: "{LOG_FILENAME}". Log level: {LOG_LEVEL_NAME} ({LOG_LEVEL_NUMBER})')

if LOG_FILENAME:
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(CustomFormatter())
    LOG.addHandler(file_handler)


def _concat(*args) -> str:
    out = ''
    for arg in args:
        out += arg if isinstance(arg, str) else str(arg)
    return out


def debug(*args):
    if LOG_LEVEL_NUMBER == logging.DEBUG:
        msg = _concat(*args)
        LOG.debug(msg)


def info(*args):
    if LOG_LEVEL_NUMBER <= logging.INFO:
        msg = _concat(*args)
        LOG.info(msg)


def warn(*args):
    if LOG_LEVEL_NUMBER <= logging.WARNING:
        msg = _concat(*args)
        LOG.warning(msg)


def error(*args, exception: bool = False):
    msg = _concat(*args)
    LOG.error(msg, exc_info=exception, stack_info=exception)
