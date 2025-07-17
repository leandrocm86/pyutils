# tests/test_cliparse.py
from __future__ import annotations
import pytest
from mods.cliparse import CliParser, Arg, FlagArg, OptArg, VarArgs
import sys


class TestCliParser:
    def test_optional_arg(self):
        class MyCLI(CliParser):
            foo = OptArg("--foo", type=str, help="Foo value", validation=lambda x: len(x) == 3)

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.value is None

        sys.argv = ["myapp", "--foo", "bar"]
        cli = MyCLI()
        assert cli.foo.value == "bar"

    def test_positional_arg(self):
        class MyCLI(CliParser):
            foo = Arg("foo", type=str, help="Foo value")

        assert MyCLI.foo.is_positional is True

        sys.argv = ["myapp", "bar"]
        cli = MyCLI()
        assert cli.foo.value == "bar"

        sys.argv = ["myapp"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_required_non_positional_arg(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, help="Foo value")

        assert MyCLI.foo.is_positional is False

        sys.argv = ["myapp"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_default_value_non_positional_arg(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, default="baz", help="Foo value")

        assert MyCLI.foo.is_positional is False

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.value == "baz"

    def test_choices(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, choices=["bar", "baz"], help="Foo value")

        sys.argv = ["myapp", "--foo", "bar"]
        cli = MyCLI()
        assert cli.foo.value == "bar"

        sys.argv = ["myapp", "--foo", "qux"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_validate(self):
        """ Arg is invalid if the validation function returns False or raises an exception """

        class MyCLI(CliParser):

            @staticmethod
            def validate_bar(bar: str) -> bool:
                assert bar != "foo", 'Bar cant be foo'
                return True

            foo = Arg("--foo", type=int, validation=lambda x: x > 0)
            bar = Arg("--bar", type=str, validation=lambda x: MyCLI.validate_bar(x))

        sys.argv = ["myapp", "--foo", "-1"]
        with pytest.raises(SystemExit):
            MyCLI()

        sys.argv = ["myapp", "--bar", "foo"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_post_validate(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, help="Foo value")
            bar = Arg("--bar", type=str, help="Bar value")

            def _post_validate(self):
                assert self.foo.value != self.bar.value

        sys.argv = ["myapp", "--foo", "bar", "--bar", "bar"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_bool_arg_error(self):
        with pytest.raises(AssertionError):
            foo = Arg("--foo", type=bool, help="Foo value")  # noqa  # type: ignore  # NOSONAR

        with pytest.raises(AssertionError):
            foo = Arg("--foo", type=bool, default=False, help="Foo value")  # noqa  # type: ignore  # NOSONAR

    def test_bool_optarg_error(self):
        with pytest.raises(AssertionError):
            foo = OptArg("--foo", type=bool, help="Foo value")  # noqa  # type: ignore  # NOSONAR

    def test_flagarg(self):
        class MyCLI(CliParser):
            foo = FlagArg("--foo", help="Foo value")

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.value is False

        sys.argv = ["myapp", "--foo"]
        cli = MyCLI()
        assert cli.foo.value is True

    def test_varargs(self):
        class MyCLI(CliParser):
            foo = VarArgs("foo", type=int, nargs="+", help="Foo values")

        sys.argv = ["myapp", "1", "2", "3"]
        cli = MyCLI()
        assert cli.foo.values == (1, 2, 3)

        sys.argv = ["myapp"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_varargs_empty(self):
        class MyCLI(CliParser):
            foo = VarArgs("foo", type=str, nargs="*", help="Foo values")

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.values == ()

    def test_varargs_default(self):
        class MyCLI(CliParser):
            foo = VarArgs("foo", type=str, nargs="*", help="Foo values", default=["default"])

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.values == ("default",)
