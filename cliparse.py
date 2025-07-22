from abc import ABC
from pathlib import Path
from typing import Any, Optional, Callable, Sequence, TypeVar, Generic, Type
import argparse

# Type variable for generic typing
T = TypeVar('T')


class BaseArg(Generic[T], ABC):
    """ Abstract argument base for wrapping argparse args.
    The following implementations are used based on the argument's requirements and its output type:
    Arg: for arguments that must be supplied or that have default values.
    OptArg: for optional arguments that may be None.
    FlagArg: for boolean flags that will be true if and only if they are present.
    VarArgs: for multi-value arguments, which are parsed as tuples.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        required: Optional[bool] = None,
        default: T | Optional[T] | Sequence[T] = None,
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        self._names = names
        self._type = type
        self._required = required
        self._default = default
        self._choices = choices
        self._validation = validation
        self._help = help

        self._parsed_value = default

        main_name = max(names, key=len)
        self.is_positional = not main_name.startswith('--')

        if self.is_positional:
            self._required = None  # Argparse does not accept "required" attribute for positional arguments.

        self._parsed_name = main_name.removeprefix('--').replace('-', '_')

    def _check_value_already_parsed(self):
        if not hasattr(self, "_parsed_value"):
            raise ValueError(f"Value for argument '{self._parsed_name}' has not been parsed yet.")

    def __str__(self) -> str:
        return str(self._parsed_value)


class Arg(BaseArg[T]):
    """ Wraps the definitions for an argparse argument that is required or has a default value.
    An additional "validation" property enables custom validation for each argument.
    Its value gets parsed and validated as soon as the parent CliParser is instantiated.
    For multi-value arguments, use VarArgs instead. For optional arguments without default value, use OptArg.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        default: Optional[T] = None,
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        required = True if default is None else False
        super().__init__(*names, type=type, required=required, default=default,
                         choices=choices, validation=validation, help=help)

        assert type is not bool, "Arg cannot be used with type bool. Use FlagArg for boolean flags instead."

    @property
    def value(self) -> T:
        super()._check_value_already_parsed()
        return self._parsed_value  # type: ignore


class OptArg(BaseArg[T]):
    """ Wraps the definitions for an argparse argument that is not required nor has a default value.
    An additional "validation" property enables custom validation for each argument, when exists.
    Its value gets parsed and validated as soon as the parent CliParser is instantiated, when there is a value.
    For multi-value arguments, use VarArgs instead. For required arguments or with default value, use Arg.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        super().__init__(*names, type=type, required=False, default=None, choices=choices, validation=validation, help=help)

        assert type is not bool, "OptArg cannot be used with type bool. Use FlagArg for boolean flags instead."

    @property
    def value(self) -> Optional[T]:
        super()._check_value_already_parsed()
        return self._parsed_value  # type: ignore


class FlagArg(BaseArg[bool]):
    """ Wraps the definitions for an argparse argument that is a boolean flag.
    It does not require a value, and its presence indicates True, while its absence indicates False.
    """

    def __init__(self, *names: str, help: str = ""):
        assert names and all(name.startswith('-') for name in names), "FlagArg names must start with '--' or '-'."
        super().__init__(*names, type=bool, required=False, default=False, help=help)
        assert not self.is_positional, "FlagArg cannot be positional, it must be optional and have a default value of False."

    @property
    def value(self) -> bool:
        super()._check_value_already_parsed()
        return self._parsed_value  # type: ignore


class VarArgs(BaseArg[T]):
    """ Wraps the definitions for an argparse argument that is multi-value.
    The nargs value determinates if values are required, and how many.
    The default value is only used when nargs is '*' or '?', meaning it can be empty.
    An additional "validation" property enables custom validation for each argument.
    Its values get parsed and validated as soon as the parent CliParser is instantiated.
    For single-value arguments, use Arg, OptArg or FlagArg instead.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        default: Optional[Sequence[T]] = None,
        nargs: Optional[str] = None,
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        super().__init__(*names, type=type, default=default,
                         choices=choices, validation=validation, help=help)
        self._nargs = nargs

        assert default is None or nargs in ('*', '?'), 'VarArgs default value can only be used when nargs is "*" or "?"'

    @property
    def values(self) -> tuple[T, ...]:
        super()._check_value_already_parsed()
        return self._parsed_value  # type: ignore


class CliParser:
    """ A class that simplifies the use of argparse, wrapping it to parse cli arguments.
    Each argument's definitions and parsed value are bound together in the same Arg/VarArgs object and with the same type.
    CliParser looks for all its containing Arg/Varargs upon its instantiation, and promptly parses and validates their values with their given definitions.
    A "post_validate" method can be overridden to perform additional validation after all arguments have been parsed.
    Currently, subgroups/commands are not supported yet.
    """

    def __init__(self, prog: str = "", description: str = "", epilog: str = ""):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
        if prog:
            parser.prog = prog
        if description:
            parser.description = description
        if epilog:
            parser.epilog = epilog

        attrs = self.__class__.__dict__.values()

        # Get all the Arg and VarArgs properties declared in the subclass,
        # then prepare argparse accordingly
        for att in attrs:
            if isinstance(att, BaseArg):
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

        # Parse each argument, validate them and store their values
        args = parser.parse_args()
        for att in attrs:
            if isinstance(att, BaseArg):
                if isinstance(att, FlagArg) and not hasattr(args, att._parsed_name):
                    # FlagArg is not present, so its value remains False
                    att._parsed_value = False
                    continue
                parsed_value = args.__dict__[att._parsed_name]
                if isinstance(att, VarArgs):
                    parsed_value = tuple(parsed_value) if parsed_value else ()
                # if parsed_value is None and att._type is bool:
                #     parsed_value = False
                if att._validation and parsed_value:
                    try:
                        if isinstance(att, VarArgs):
                            for value in parsed_value:
                                if not att._validation(value):
                                    raise ValueError(f"Invalid value for argument {att._parsed_name}: {str(value)[:50]}")
                        elif not att._validation(parsed_value):
                            parser.error(f"Invalid value for argument {att._parsed_name}")
                    except Exception as e:
                        parser.error(str(e))
                att._parsed_value = parsed_value

        try:  # Finally, make the post-validation (if overridden)
            self._post_validate()
        except Exception as e:
            parser.error(str(e))

    def _post_validate(self):
        """ Method to be overwritten by subclasses, performing additional validations after all arguments are parsed. """
        pass


# Example of usage
if __name__ == "__main__":

    class MyCLI(CliParser):
        host = Arg("--host", type=str, help='Host server')
        port = Arg("-p", "--port", type=int, default=0, help='Connection port')
        email = OptArg("--email", type=str, help='Email address')
        paths = VarArgs("input_files", type=Path, default=[Path('.')],
                        nargs="*", help='Files to process')
        print_colored = FlagArg("--print-colored", help='Display colors [default: false]')
        print_black = FlagArg("--print-black", help='Black&White')

        def __init__(self):
            super().__init__(description="This is an example of app using ParserCLI")

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
    print(f'host: {host}, port: {port}, email: {email}, paths: {paths}, print_colored: {print_colored}, print_black: {print_black}')
