# Common modules bundle for CLI scripts.
import sys  # type: ignore  # noqa
import os  # type: ignore  # noqa
import time  # type: ignore  # noqa
from pathlib import Path  # type: ignore  # noqa
from types import TracebackType
from typing import Type  # type: ignore  # noqa
from utils import log
from utils.log import LOG  # type: ignore  # noqa
from utils import style  # type: ignore  # noqa
from utils.pstr import pstr, ppstr  # type: ignore  # noqa
from utils.cliparse import CliParser, Arg, OptArg, FlagArg, VarArgs  # type: ignore  # noqa
from utils import system # type: ignore # noqa


def setpostmortem():
    """
    Set up a custom exception handler that will drop into either pdb.post_mortem(),
    a bpython REPL, or the interactive frame inspector on an unhandled exception,
    based on user choice.

    If the exception occurred in interactive mode (i.e., inside a REPL like
    IPython), or if there is no tty available, the default exception handler
    is used instead.

    This is meant to be used as a way to debug unexpected exceptions that
    occur in scripts, by allowing the user to drop into a debugging session.
    """
    import pdb

    def exception_handler(exc_type: type[BaseException],
                          exc_value: BaseException,
                          exc_traceback: TracebackType):

        # The mods.log module has an exception handler too, so we should use it
        log._inspect_exception_hook(exc_type=exc_type, exc_value=exc_value, exc_traceback=exc_traceback)  # type: ignore
        print(f"Exception of type {exc_type.__name__} occurred: {style.red(str(exc_value))}")

        # Build the prompt based on available options
        options: list[str] = []
        options.append("p: pdb")
        try:
            import bpython  # type: ignore
            options.append("b: bpython")
        except ImportError as e:
            LOG.warning("Bpython not available: %s", e)
            bpython = None  # Handle case where bpython is not installed

        try:
            # Import the frame inspector (adjust the import path as needed)
            from utils.frame_inspector import inspect_frames  # type: ignore
            options.append("i: inspect frames")
        except ImportError as e:
            LOG.warning("Frame inspector not available: %s", e)

        options.append("q: quit (default)")

        prompt = f"Enter debug mode? ({', '.join(options)}) : "
        choice = input(prompt).lower()

        if choice == 'i' and inspect_frames:
            print("Starting interactive frame inspector...")
            try:
                inspect_frames(exc_traceback, exc_type, exc_value)  # type: ignore
            except Exception as inspector_error:
                print(f"Error starting frame inspector: {inspector_error}")
                print("Falling back to pdb...")
                pdb.post_mortem(exc_traceback)
        elif choice == 'p':
            print("Starting post-mortem debugging session with pdb...")
            pdb.post_mortem(exc_traceback)
        elif choice == 'b' and bpython:
            print("Starting bpython REPL session...")

            # Traverse from outermost to innermost frame,
            # collecting locals from all frames, innermost last (so it overwrites)
            all_locals = {}

            frames = []
            current_tb = exc_traceback
            while current_tb:
                frames.append(current_tb.tb_frame)
                current_tb = current_tb.tb_next

            # Merge locals from outermost to innermost (innermost overwrites)
            for frame in frames:
                all_locals.update(frame.f_locals)

            # Inject additional util modules
            from utils.pstr import pstr
            all_locals['pstr'] = pstr

            # Start bpython with all variables available
            bpython.embed(locals_=all_locals)
        else:
            print("Skipping debug mode.")

    # Register the custom exception hook, only if we're not in interactive mode
    if not hasattr(sys, 'ps1') or sys.stderr.isatty():
        log.info('Setting up postmortem hook...')
        sys.excepthook = exception_handler
