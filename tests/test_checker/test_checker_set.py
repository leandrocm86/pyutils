from collections.abc import Set
import pytest
import mods.type_checker as ck


def test_iscoll_valid():
    ck.valset({1, 2, 3}, int)
    ck.valset(set(['a', 'b', 'c']), str)
    ck.valset(frozenset((True, False)), bool)


def test_iscoll_invalid_type():
    with pytest.raises(TypeError):
        ck.valset([1, 2, 3], int)  # type: ignore

    with pytest.raises(TypeError):
        ck.valset('hello', str)  # type: ignore


def test_iscoll_invalid_element_type():
    with pytest.raises(TypeError):
        ck.valset({1, 2, 3}, str)  # type: ignore


def test_iscoll_length():
    ck.valset({1, 2, 3}, int, length=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 3}, int, length=4)


def test_iscoll_minlen():
    ck.valset({1, 2, 3}, int, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1}, int, minlen=2)


def test_iscoll_maxlen():
    ck.valset({1, 2, 3}, int, maxlen=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 3, 4, 5}, int, maxlen=4)


def test_iscoll_minelem():
    ck.valset({1, 2, 3}, int, minelem=1)
    ck.valset({1, 2, 3}, int, minelem=0)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({0, 2, 3}, int, minelem=1)


def test_iscoll_maxelem():
    ck.valset({1, 2, 3}, int, maxelem=3)
    ck.valset({1, 2, 3}, int, maxelem=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 4}, int, maxelem=3)


def test_iscoll_custom():
    def custom_check(seq: Set[int]):
        return sum(seq) > 5

    ck.valset({1, 2, 3}, int, custom=custom_check)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2}, int, custom=custom_check)
