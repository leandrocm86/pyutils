# tests/test_cliparse.py
from __future__ import annotations
import pytest
from mods.cliparse import CliParser, Arg, VarArgs
import sys


class TestCliParser:
    def test_simple_cli(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, help="Foo value")

        sys.argv = ["myapp", "--foo", "bar"]
        cli = MyCLI()
        assert cli.foo.value == "bar"

    def test_required_arg(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, required=True, help="Foo value")

        sys.argv = ["myapp"]
        with pytest.raises(SystemExit):
            MyCLI()

    def test_default_value(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=str, default="baz", help="Foo value")

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

    def test_varargs(self):
        class MyCLI(CliParser):
            foo = VarArgs("foo", type=int, nargs="+", help="Foo values")

        sys.argv = ["myapp", "1", "2", "3"]
        cli = MyCLI()
        assert cli.foo.values == (1, 2, 3)

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

    def test_bool_arg(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=bool, help="Foo value")

        sys.argv = ["myapp", "--foo"]
        cli = MyCLI()
        assert cli.foo.value is True

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.value is False

    def test_optional_bool_arg(self):
        class MyCLI(CliParser):
            foo = Arg("--foo", type=bool, default=False, help="Foo value")

        sys.argv = ["myapp", "--foo"]
        cli = MyCLI()
        assert cli.foo.value is True

        sys.argv = ["myapp"]
        cli = MyCLI()
        assert cli.foo.value is False
