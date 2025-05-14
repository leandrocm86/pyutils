# Common modules bundle for CLI scripts.
import sys  # type: ignore  # noqa
import os  # type: ignore  # noqa
import time  # type: ignore  # noqa
import argparse  # type: ignore  # noqa
import typer
from typing_extensions import Annotated
from pathlib import Path  # type: ignore  # noqa
from types import TracebackType
from typing import Type  # type: ignore  # noqa
from loguru import logger
from mods import color  # type: ignore  # noqa
from mods.pstr import pstr  # type: ignore  # noqa


catch = logger.catch


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

        if hasattr(sys, 'ps1') or not sys.stderr.isatty():
            # We're in interactive mode or don't have a tty-like
            # device, so call the default hook
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            print(f"Exception of type {exc_type.__name__} occurred: {color.red(str(exc_value))}")
            if input('Enter debug mode? (y/n) : ') in ('y', 'Y'):
                print("Starting post-mortem debugging session...")
                pdb.post_mortem(exc_traceback)

    # Register the custom exception hook
    sys.excepthook = exception_handler
