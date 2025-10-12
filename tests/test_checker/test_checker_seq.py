from collections.abc import Sequence
from types import SimpleNamespace
from typing import Union
import pytest
import utils.type_checker as ck


class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


def test_iscoll_valid():
    ck.valseq([1, 2, 3], int)
    ck.valseq(['a', 'b', 'c'], str)
    ck.valseq([True, False, True], bool)
    ck.valseq('hello', str)
    ck.valseq([None], Union[str, None])  # type: ignore
    tup = Person('John', 30), Person('Jane', 25)
    ck.valseq(tup, Person)


def test_iscoll_invalid_type():
    with pytest.raises(TypeError):
        ck.valseq(123, int)  # type: ignore
    with pytest.raises(TypeError):
        ck.valseq({1, 2, 3}, int)  # type: ignore


def test_iscoll_invalid_element_type():
    with pytest.raises(TypeError):
        ck.valseq(['1', '2', '3'], int)
        with pytest.raises(TypeError):
            ck.valseq([None], str)
    with pytest.raises(TypeError):
        obj = SimpleNamespace(name='John', age=30)
        ck.valseq([obj], Person)


def test_iscoll_length():
    ck.valseq([1, 2, 3], int, length=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 3], int, length=4)


def test_iscoll_minlen():
    ck.valseq([1, 2, 3], int, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1], int, minlen=2)


def test_iscoll_maxlen():
    ck.valseq([1, 2, 3], int, maxlen=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 3, 4, 5], int, maxlen=4)


def test_iscoll_minelem():
    ck.valseq([1, 2, 3], int, minelem=1)
    ck.valseq([1, 2, 3], int, minelem=0)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 2, 3], int, minelem=1)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 2, 3], int, minelem='0')


def test_iscoll_maxelem():
    ck.valseq([1, 2, 3], int, maxelem=3)
    ck.valseq([1, 2, 3], int, maxelem=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 4], int, maxelem=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 4], int, maxelem=['4'])


def test_iscoll_custom():
    def custom_check(seq: Sequence[int]):
        return sum(seq) > 5

    ck.valseq([1, 2, 3], int, custom=custom_check)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2], int, custom=custom_check)

    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 1, 2], int, custom=lambda s: s[1] / s[0] > 1)
