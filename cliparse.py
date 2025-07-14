from abc import ABC
from pathlib import Path
from typing import Any, Optional, Callable, TypeVar, Generic, Type
import argparse

# Type variable for generic typing
T = TypeVar('T')


class BaseArg(Generic[T], ABC):
    """Argument descriptor with generic type parameter."""

    def __init__(
        self,
        *names: str,
        type: Type[T],
        required: Optional[bool] = None,
        default: Optional[T] | list[T] = None,
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

        self._parsed_name = max(names, key=len).removeprefix('--').replace('-', '_')


class Arg(BaseArg[T]):
    """ Wraps the definitions for an argparse argument.
    An additional "validation" property enables custom validation for each argument.
    Its value gets parsed and validated as soon as the parent CliParser is instantiated.
    For multi-value arguments, use VarArgs instead.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        required: Optional[bool] = None,
        default: Optional[T] = None,
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        super().__init__(*names, type=type, required=required, default=default,
                         choices=choices, validation=validation, help=help)

    @property
    def value(self) -> T:
        if hasattr(self, "_parsed_value"):
            return self._parsed_value  # type: ignore
        raise Exception('Argument value not parsed yet')


class VarArgs(BaseArg[T]):
    """ Wraps the definitions for an argparse argument that is multi-value.
    An additional "validation" property enables custom validation for each argument.
    Its values get parsed and validated as soon as the parent CliParser is instantiated.
    For single-value arguments, use Arg instead.
    """

    def __init__(
        self,
        *names: str,
        type: Type[T],
        required: Optional[bool] = None,
        default: Optional[list[T]] = None,
        nargs: Optional[str] = None,
        choices: Optional[list[T]] = None,
        validation: Optional[Callable[[T], bool]] = None,
        help: str = "",
    ):
        super().__init__(*names, type=type, required=required, default=default,
                         choices=choices, validation=validation, help=help)
        self._nargs = nargs

    @property
    def values(self) -> tuple[T]:
        if hasattr(self, "_parsed_value"):
            return tuple(self._parsed_value)  # type: ignore
        raise Exception('Argument value not parsed yet')


class CliParser:
    """ A class that simplifies the use of argparse, wrapping it to parse cli arguments.
    Each argument's definitions and parsed value are bound together in the same Arg/VarArgs object and with the same type.
    CliParser looks for all its containing Arg/Varargs upon its instantiation, and promptly parses and validates their values with their given definitions.
    A "post_validate" method can be overridden to perform additional validation after all arguments have been parsed.
    Currently, subgroups/commands are not supported yet.
    """

    def __init__(self, prog: str = "", description: str = ""):
        parser = argparse.ArgumentParser()
        if prog:
            parser.prog = prog
        if description:
            parser.description = description

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

                if att._type == bool or att._type == Optional[bool]:
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
                parsed_value = args.__dict__[att._parsed_name]
                if parsed_value is None and att._type is bool:
                    parsed_value = False
                if att._validation:
                    try:
                        valid_input = att._validation(parsed_value)
                        if not valid_input:
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
        paths = VarArgs("input_files", type=Path,
                        nargs="+", default=[Path('.')], help='Files to process')
        print_colored = Arg("--print-colored", type=bool,
                            default=False, help='Display colors [default: false]')
        print_black = Arg("--print-black", type=bool,
                          default=False, help='Black&White')

        def __init__(self):
            super().__init__(description="This is an example of app using ParserCLI")

        def _post_validate(self):
            assert not (self.print_colored.value and self.print_black.value), \
                'Cannot print both colored and black'

    args = MyCLI()
    host = args.host.value
    port = args.port.value
    paths = args.paths.values
    print_colored = args.print_colored.value
    print_black = args.print_black.value
    print(f'host: {host}, port: {port}, paths: {paths}, print_colored: {print_colored}, print_black: {print_black}')
