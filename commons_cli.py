# Common modules bundle for CLI scripts.
import sys  # type: ignore  # noqa
import os  # type: ignore  # noqa
import time  # type: ignore  # noqa
from pathlib import Path  # type: ignore  # noqa
from types import TracebackType
from typing import Type  # type: ignore  # noqa
from mods import log  # type: ignore  # noqa
from mods import style  # type: ignore  # noqa
from mods.pstr import pstr, ppstr  # type: ignore  # noqa
from mods.cliparse import CliParser, Arg, OptArg, FlagArg, VarArgs  # type: ignore  # noqa
from mods import system # type: ignore # noqa


def setpostmortem():
    """
    Set up a custom exception handler that will drop into either pdb.post_mortem()
    or a bpython REPL on an unhandled exception, based on user choice.

    If the exception occurred in interactive mode (i.e., inside a REPL like
    IPython), or if there is no tty available, the default exception handler
    is used instead.

    This is meant to be used as a way to debug unexpected exceptions that
    occur in scripts, by allowing the user to drop into a debugging session.
    """
    import pdb
    try:
        import bpython  # type: ignore
    except ImportError:
        bpython = None  # Handle case where bpython is not installed

    def exception_handler(exc_type: type[BaseException],
                          exc_value: BaseException,
                          exc_traceback: TracebackType):

        # The mods.log module has an exception handler too, so we should use it
        log._inspect_exception_hook(exc_type=exc_type, exc_value=exc_value, exc_traceback=exc_traceback)  # type: ignore
        print(f"Exception of type {exc_type.__name__} occurred: {style.red(str(exc_value))}")

        # Prompt user to choose debugging mode
        if bpython:
            prompt = "Enter debug mode? (y: pdb, b: bpython, n: none) : "
        else:
            prompt = "Enter debug mode? (y: pdb, n: none) : "

        choice = input(prompt).lower()

        if choice == 'y':
            print("Starting post-mortem debugging session with pdb...")
            pdb.post_mortem(exc_traceback)
        elif choice == 'b' and bpython:
            print("Starting bpython REPL session...")
            # Get the innermost frame from the traceback
            tb = exc_traceback
            while tb.tb_next:  # Traverse to the last (innermost) frame
                tb = tb.tb_next
            frame = tb.tb_frame
            # Pass the frame's locals to bpython
            bpython.embed(locals_=frame.f_locals)  # type: ignore
        else:
            print("Skipping debug mode.")

    # Register the custom exception hook, only if we're not in interactive mode
    if not hasattr(sys, 'ps1') or sys.stderr.isatty():
        log.info('Setting up postmortem hook...')
        sys.excepthook = exception_handler
