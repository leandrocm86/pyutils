# Common modules bundle for CLI scripts.
import sys
import os   # type: ignore  # noqa
from utils import log, style
from utils.pstr import pstr, ppstr  # type: ignore  # noqa
from utils.cliparse import CliParser, Arg, OptArg, FlagArg, VarArgs  # type: ignore  # noqa
from types import FrameType, TracebackType
from typing import TypeVar, Mapping, Sequence, Any


def pdb_exception_handler(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None):
    import pdb
    if exc_type is KeyboardInterrupt:
        print("KEYBOARD INTERRUPTED!")
        return

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
        log.warn("Bpython not available: %s", e)
        bpython = None  # Handle case where bpython is not installed

    try:
        # Import the frame inspector (adjust the import path as needed)
        from utils.frame_inspector import inspect_frames  # type: ignore

        options.append("i: inspect frames")
    except ImportError as e:
        log.warn("Frame inspector not available: %s", e)

    options.append("q: quit (default)")

    prompt = f"Enter debug mode? ({', '.join(options)}) : "
    choice = input(prompt).lower()

    if choice == "i":
        assert "inspect_frames" in locals(), "Frame inspector not available"
        print("Starting interactive frame inspector...")
        try:
            inspect_frames(exc_traceback, exc_type, exc_value)  # type: ignore
        except Exception as inspector_error:
            print(f"Error starting frame inspector: {inspector_error}")
            print("Falling back to pdb...")
            pdb.post_mortem(exc_traceback)
    elif choice == "p":
        print("Starting post-mortem debugging session with pdb...")
        pdb.post_mortem(exc_traceback)
    elif choice == "b" and bpython:
        print("Starting bpython REPL session...")

        # Traverse from outermost to innermost frame,
        # collecting locals from all frames, innermost last (so it overwrites)
        all_locals: dict[str, Any] = {}

        frames: list[FrameType] = []
        var_current_tb = exc_traceback
        while var_current_tb:
            frames.append(var_current_tb.tb_frame)
            var_current_tb = var_current_tb.tb_next

        # Merge locals from outermost to innermost (innermost overwrites)
        for frame in frames:
            all_locals.update(frame.f_locals)

        # Inject additional util modules
        all_locals["pstr"] = pstr

        # Start bpython with all variables available
        bpython.embed(locals_=all_locals)  # type: ignore

    else:
        print("Skipping debug mode.")


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
    # Register the custom exception hook, only if we're not in interactive mode
    if not hasattr(sys, "ps1") or sys.stderr.isatty():
        log.info("Setting up postmortem hook...")
        sys.excepthook = pdb_exception_handler


T = TypeVar("T")


def int_input(prompt: str, domain: set[int] | None = None) -> int:
    """
    Prompts the user for an integer input, retrying until a valid integer is provided.
    If a domain is specified, the input must be within that set of integers.
    """
    while True:
        try:
            num = int(input(prompt))
            if domain is None or num in domain:
                return num
            else:
                print("Input not in the allowed domain.")
        except ValueError:
            print("Invalid input, please enter an integer.")


def bool_input(prompt: str = "Enter a boolean value", true_value: str = "y", false_value: str = "n", default: bool = False) -> bool:
    """
    Prompts the user for a boolean input, retrying until a valid boolean is provided.
    """
    while True:
        true_value = true_value.upper() if default is True else true_value.lower()
        false_value = false_value.upper() if default is False else false_value.lower()
        prompt = f'{prompt} ({true_value}/{false_value}): '
        response = input(prompt).strip()
        if response.lower() == true_value.lower():
            return True
        elif response.lower() == false_value.lower():
            return False
        elif response == "":
            return default
        else:
            print(f"Invalid input, please enter '{true_value}' or '{false_value}'.")


def input_option(options: Mapping[str, T] | Sequence[T], prompt: str = "Select option: ") -> T:
    """
    Displays a list of options with indices, and prompts the user to select one.

    Args:
        options: A mapping of description strings to option values, or a sequence of options.
        prompt: The prompt text to display to the user.

    Returns:
        The single option value chosen by the user.
    """
    var_chosen_options = input_options(options, prompt)
    while len(var_chosen_options) != 1:
        print("Please select only one option.")
        var_chosen_options = input_options(options, prompt=prompt)
    return var_chosen_options[0]


def input_options(options: Mapping[str, T] | Sequence[T], prompt: str = "Select option(s): ") -> tuple[T, ...]:
    """
    Displays a list of options with indices, and prompts the user to select one or more.

    Args:
        options: A mapping of description strings to option values, or a sequence of options.
        prompt: The prompt text to display to the user.

    Returns:
        A tuple containing the option values chosen by the user.
    """
    indexed_options = list(options) if isinstance(options, Sequence) else list(options.values())
    descriptions = (
        {i: str(opt) for i, opt in enumerate(indexed_options)}
        if isinstance(options, Sequence)
        else {i: desc for i, desc in enumerate(options.keys())}
    )

    opts: list[str] = []
    for i, desc in descriptions.items():
        opts.append(f"{style.bold(str(i))} - {desc}")
    print(style.create_panel("\n".join(opts), expand=False, padding=0))

    valid_indices = set(range(len(indexed_options)))
    while True:
        try:
            raw_input = input(prompt)
            chosen_indices_str = raw_input.split()
            if not chosen_indices_str:
                print("Please enter at least one index.")
                continue
            chosen_indices = {int(s) for s in chosen_indices_str}
            if chosen_indices.issubset(valid_indices):
                print()  # One empty line for spacing
                return tuple(indexed_options[i] for i in sorted(list(chosen_indices)))
            else:
                invalid = chosen_indices - valid_indices
                print(f"Invalid index/indices: {', '.join(map(str, invalid))}")
        except ValueError:
            print("Invalid input, please enter space-separated integers.")
