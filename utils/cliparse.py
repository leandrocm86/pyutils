# basedpyright: reportPrivateUsage=false
"""A lightweight, type-safe wrapper around argparse.
Requires Python 3.12+ (uses PEP 695 generic class syntax: `class Foo[T]:`).
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast, Literal, override


class BaseArg[T](ABC):
    """Abstract argument base for wrapping argparse args.

    The following implementations are used based on the argument's requirements and its output type:
    Arg: for arguments that must be supplied or that have default values.
    OptArg: for optional arguments that may be None.
    FlagArg: for boolean flags that will be true if and only if they are present.
    VarArgs: for multi-value arguments, which are parsed as tuples.
    """

    @abstractmethod
    def __init__(
        self,
        *names: str,
        argtype: type[T],
        required: bool | None = None,
        default: T | Sequence[T] | None = None,
        choices: list[T] | None = None,
        validation: Callable[[T], object] | None = None,
        help: str = "",
    ) -> None:
        self._names: tuple[str, ...] = names
        self._type: type[T] = argtype
        self._required = required
        self._default = default
        self._choices = choices
        self._validation = validation
        self._help = help

        self._parsed_value: T | Sequence[T] | None = default

        # After parsing, the value is stored under the first long option name provided,
        # or the short option name if no long option is given.
        main_name = next((name for name in names if name.startswith("--")), names[0])

        self.is_positional = not main_name.startswith('--')

        if self.is_positional:
            self._required = None  # Argparse does not accept "required" attribute for positional arguments.

        self._parsed_name = main_name.removeprefix('--').replace('-', '_')

    def _check_value_already_parsed(self) -> None:
        if not hasattr(self, "_parsed_value"):
            raise ValueError(f"Value for argument '{self._parsed_name}' has not been parsed yet.")

    @override
    def __str__(self) -> str:
        return str(self._parsed_value)


class Arg[T](BaseArg[T]):
    """Wraps the definitions for an argparse argument that is required or has a default value.

    An additional "validation" property enables custom validation for each argument.
    Its value gets parsed and validated as soon as the parent CliParser is instantiated.
    For multi-value arguments, use VarArgs instead. For optional arguments without default value, use OptArg.
    """

    def __init__(
        self,
        *names: str,
        argtype: type[T],
        default: T | None = None,
        choices: list[T] | None = None,
        validation: Callable[[T], object] | None = None,
        help: str = "",
    ) -> None:
        required = default is None
        super().__init__(
            *names, argtype=argtype, required=required, default=default,
            choices=choices, validation=validation, help=help,
        )

        assert argtype is not bool, "Arg cannot be used with type bool. Use FlagArg for boolean flags instead."

    @property
    def value(self) -> T:
        self._check_value_already_parsed()
        return cast(T, self._parsed_value)


class OptArg[T](BaseArg[T]):
    """Wraps the definitions for an argparse argument that is not required nor has a default value.

    An additional "validation" property enables custom validation for each argument, when exists.
    Its value gets parsed and validated as soon as the parent CliParser is instantiated, when there is a value.
    For multi-value arguments, use VarArgs instead. For required arguments or with default value, use Arg.
    """

    def __init__(
        self,
        *names: str,
        argtype: type[T],
        choices: list[T] | None = None,
        validation: Callable[[T], object] | None = None,
        help: str = "",
    ) -> None:
        super().__init__(*names, argtype=argtype, required=False, default=None,
                         choices=choices, validation=validation, help=help)

        assert argtype is not bool, "OptArg cannot be used with type bool. Use FlagArg for boolean flags instead."

    @property
    def value(self) -> T | None:
        self._check_value_already_parsed()
        return cast("T | None", self._parsed_value)


class FlagArg(BaseArg[bool]):
    """Wraps the definitions for an argparse argument that is a boolean flag.

    It does not require a value, and its presence indicates True, while its absence indicates False.
    """

    def __init__(self, *names: str, help: str = "") -> None:
        assert names and all(name.startswith('-') for name in names), "FlagArg names must start with '--' or '-'."
        super().__init__(*names, argtype=bool, required=False, default=False, help=help)
        assert not self.is_positional, \
            "FlagArg cannot be positional, it must be optional and have a default value of False."

    @property
    def value(self) -> bool:
        self._check_value_already_parsed()
        return cast(bool, self._parsed_value)


class VarArgs[T](BaseArg[T]):
    """Wraps the definitions for an argparse argument that is multi-value.

    The nargs value determinates if values are required, and how many.
    The default value is only used when nargs is '*' or '?', meaning it can be empty.
    An additional "validation" property enables custom validation for each argument.
    Its values get parsed and validated as soon as the parent CliParser is instantiated.
    For single-value arguments, use Arg, OptArg or FlagArg instead.
    """

    def __init__(
        self,
        *names: str,
        argtype: type[T],
        default: Sequence[T] | None = None,
        nargs: Literal["*", "+", "?"] | int | None = None,
        choices: list[T] | None = None,
        validation: Callable[[T], object] | None = None,
        help: str = "",
    ) -> None:
        super().__init__(
            *names, argtype=argtype, default=default,
            choices=choices, validation=validation, help=help,
        )
        self._nargs = nargs

        assert default is None or nargs in ('*', '?'), 'VarArgs default value can only be used when nargs is "*" or "?"'

    @property
    def values(self) -> tuple[T, ...]:
        self._check_value_already_parsed()
        return cast("tuple[T, ...]", self._parsed_value)


class CliParser:
    """A class that simplifies the use of argparse, wrapping it to parse cli arguments.

    Each argument's definitions and parsed value are bound together
    in the same Arg/VarArgs object and with the same type.
    CliParser looks for all its containing Arg/Varargs upon its instantiation,
    and promptly parses and validates their values with their given definitions.
    A "post_validate" method can be overridden to perform additional validation after all arguments have been parsed.
    Currently, subgroups/commands are not supported yet.
    """

    def __init__(self, prog: str = "", description: str = "", epilog: str = "") -> None:
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
        if prog:
            parser.prog = prog
        if description:
            parser.description = description
        if epilog:
            parser.epilog = epilog

        attrs: list[BaseArg[Any]] = [
            att for att in self.__class__.__dict__.values() if isinstance(att, BaseArg)
        ]

        def resolve_validation(value: Any, validation_func: Callable[[Any], object]) -> bool:
            """Validation functions can raise exceptions, but they're handled internally.

            The internal result must always be a bool. If the validation raises, we consider it False (invalid).
            If the validation returns a value, we convert it to bool. Otherwise, we return True (valid).
            """
            try:
                out = validation_func(value)
            except Exception:
                return False
            return True if out is None else bool(out)

        # Prepare argparse from each declared Arg/VarArgs.
        for att in attrs:
            nargs = att._nargs if isinstance(att, VarArgs) else None

            params: dict[str, Any] = {
                'default': att._default,
                'help': att._help
            }

            if att._required is not None:
                params['required'] = att._required

            if isinstance(att, FlagArg):
                params['action'] = 'store_true'
            else:
                params['type'] = att._type
                params['nargs'] = nargs
                if att._choices:
                    params['choices'] = att._choices

            parser.add_argument(*att._names, **params)

        # Parse each argument, validate them and store their values.
        args = parser.parse_args()
        for att in attrs:
            if isinstance(att, FlagArg) and not hasattr(args, att._parsed_name):
                # FlagArg is not present, so its value remains False
                att._parsed_value = False
                continue

            var_parsed_value = getattr(args, att._parsed_name)
            if isinstance(att, VarArgs):
                var_parsed_value = tuple(var_parsed_value) if var_parsed_value else ()

            if att._validation and var_parsed_value:
                try:
                    if isinstance(att, VarArgs):
                        for value in var_parsed_value:
                            if not resolve_validation(value, att._validation):
                                raise ValueError(f"Invalid value for argument {att._parsed_name}: {str(value)[:50]}")
                    elif not resolve_validation(var_parsed_value, att._validation):
                        parser.error(f"Invalid value for argument {att._parsed_name}")
                except Exception as e:
                    parser.error(str(e))

            att._parsed_value = var_parsed_value

        try:  # Finally, make the post-validation (if overridden)
            self._post_validate()
        except Exception as e:
            parser.error(str(e))

    def _post_validate(self) -> None:
        """Method to be overwritten by subclasses, performing additional validations after all arguments are parsed."""


# Example of usage
if __name__ == "__main__":

    def validate_email(e: str):
        assert '@' in e

    class MyCLI(CliParser):
        host = Arg("--host", argtype=str, help='Host server')
        port = Arg("-p", "--port", argtype=int, default=0, help='Connection port', validation=lambda p: p < 9999)
        email = OptArg("--email", argtype=str, help='Email address', validation=validate_email)
        paths = VarArgs("input_files", argtype=Path, default=[Path('.')], nargs="*", help='Files to process')
        print_colored = FlagArg("--print-colored", help='Display colors [default: false]')
        print_black = FlagArg("--print-black", help='Black&White')

        def __init__(self):
            super().__init__(description="This is an example of app using ParserCLI")

        @override
        def _post_validate(self):
            assert not (self.print_colored.value and self.print_black.value), \
                'Cannot print both colored and black'

    args = MyCLI()
    host = args.host.value
    port = args.port.value
    email = args.email.value
    paths = args.paths.values
    print_colored = args.print_colored.value
    print_black = args.print_black.value
    print(f"host: {host}, port: {port}, email: {email}, paths: {paths},"
          + f"print_colored: {print_colored}, print_black: {print_black}")
