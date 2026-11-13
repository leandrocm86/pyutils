# Common modules bundle for CLI scripts.
lazy import sys
lazy import pdb  # noqa
lazy from types import FrameType, TracebackType
lazy from collections.abc import Callable, Mapping, Sequence
lazy from typing import Any
lazy from utils.log import info, warn, _inspect_exception_hook
lazy from utils.style import bold, create_panel, red
lazy from utils.pstr import pstr


def pdb_exception_handler(exc_type: type[BaseException],
                          exc_value: BaseException,
                          exc_traceback: TracebackType | None):
    if exc_type is KeyboardInterrupt:
        print("KEYBOARD INTERRUPTED!")
        return

    _inspect_exception_hook(exc_type=exc_type, exc_value=exc_value, exc_traceback=exc_traceback)
    print(f"Exception of type {exc_type.__name__} occurred: {red(str(exc_value))}")

    options: list[str] = ["p: pdb"]

    bpython_module: Any = None
    try:
        import bpython  # type: ignore

        bpython_module = bpython
        options.append("b: bpython")
    except ImportError as e:
        warn("Bpython not available: %s", e)

    inspect_frames_fn: Callable[..., Any] | None = None
    try:
        from utils.frame_inspector import inspect_frames

        inspect_frames_fn = inspect_frames
        options.append("i: inspect frames")
    except ImportError as e:
        warn("Frame inspector not available: %s", e)

    options.append("q: quit (default)")

    prompt = f"Enter debug mode? ({', '.join(options)}) : "
    choice = input(prompt).lower()

    if choice == "i" and inspect_frames_fn is not None:
        print("Starting interactive frame inspector...")
        try:
            inspect_frames_fn(exc_traceback, exc_type, exc_value)
        except Exception as inspector_error:
            print(f"Error starting frame inspector: {inspector_error}")
            print("Falling back to pdb...")
            pdb.post_mortem(exc_traceback)
    elif choice == "p":
        print("Starting post-mortem debugging session with pdb...")
        pdb.post_mortem(exc_traceback)
    elif choice == "b" and bpython_module is not None:
        print("Starting bpython REPL session...")

        all_locals: dict[str, Any] = {}
        var_tb = exc_traceback
        frames: list[FrameType] = []
        while var_tb:
            frames.append(var_tb.tb_frame)
            var_tb = var_tb.tb_next

        for frame in frames:
            all_locals.update(frame.f_locals)

        all_locals["pstr"] = pstr
        bpython_module.embed(locals_=all_locals)
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
        info("Setting up postmortem hook...")
        sys.excepthook = pdb_exception_handler


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


def bool_input(prompt: str = "Enter a boolean value",
               true_value: str = "y",
               false_value: str = "n",
               default: bool = False) -> bool:
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


def input_option[T](options: Mapping[str, T] | Sequence[T],
                    prompt: str = "Select option: ") -> T:
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


def input_options[T](options: Mapping[str, T] | Sequence[T],
                     prompt: str = "Select option(s): ") -> tuple[T, ...]:
    """
    Displays a list of options with indices, and prompts the user to select one or more.

    Args:
        options: A mapping of description strings to option values, or a sequence of options.
        prompt: The prompt text to display to the user.

    Returns:
        A tuple containing the option values chosen by the user.
    """
    if isinstance(options, Mapping):
        var_indexed_options = list(options.values())
        var_descriptions = list(options.keys())
    else:
        var_indexed_options = list(options)
        var_descriptions = [str(opt) for opt in var_indexed_options]

    opts = [f"{bold(str(i))} - {desc}" for i, desc in enumerate(var_descriptions)]
    print(create_panel("\n".join(opts), expand=False, padding=0))

    valid_indices = set(range(len(var_indexed_options)))
    while True:
        try:
            chosen_indices_str = input(prompt).split()
            if not chosen_indices_str:
                print("Please enter at least one index.")
                continue
            chosen_indices = {int(s) for s in chosen_indices_str}
            if chosen_indices.issubset(valid_indices):
                print()
                return tuple(var_indexed_options[i] for i in sorted(chosen_indices))
            invalid = chosen_indices - valid_indices
            print(f"Invalid index/indices: {', '.join(map(str, invalid))}")
        except ValueError:
            print("Invalid input, please enter space-separated integers.")
