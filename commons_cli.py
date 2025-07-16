# Common modules bundle for CLI scripts.
import sys  # type: ignore  # noqa
import os  # type: ignore  # noqa
import time  # type: ignore  # noqa
from pathlib import Path  # type: ignore  # noqa
from types import TracebackType
from typing import Type  # type: ignore  # noqa
from mods.log import LOG, _inspect_exception_hook  # type: ignore  # noqa
from mods import color  # type: ignore  # noqa
from mods.pstr import pstr  # type: ignore  # noqa
from mods.cliparse import CliParser, Arg, OptArg, FlagArg, VarArgs  # type: ignore  # noqa
import mods.system # type: ignore # noqa


def setpostmortem():
    """
    Set up a custom exception handler that will drop into pdb.post_mortem()
    on an unhandled exception, if the user chooses to do so.

    If the exception occurred in interactive mode (i.e. inside a REPL like
    IPython), or if there is no tty available, the default exception handler
    is used instead.

    This is meant to be used as a way to debug unexpected exceptions that
    occur in scripts, by allowing the user to drop into a pdb post-mortem
    session.
    """
    import pdb

    def exception_handler(exc_type: Type[BaseException],
                          exc_value: BaseException,
                          exc_traceback: TracebackType):

        _inspect_exception_hook(exc_type=exc_type, exc_value=exc_value, exc_traceback=exc_traceback)
        print(f"Exception of type {exc_type.__name__} occurred: {color.red(str(exc_value))}")
        if input('Enter debug mode? (y/n) : ') in ('y', 'Y'):
            print("Starting post-mortem debugging session...")
            pdb.post_mortem(exc_traceback)

    # Register the custom exception hook, only if we're not in interactive mode
    if not hasattr(sys, 'ps1') or sys.stderr.isatty():
        sys.excepthook = exception_handler
