from collections.abc import Set
import pytest
import utils.type_checker as ck


def test_iscoll_length():
    ck.valset({1, 2, 3}, length=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 3}, length=4)


def test_iscoll_minlen():
    ck.valset({1, 2, 3}, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1}, minlen=2)


def test_iscoll_maxlen():
    ck.valset({1, 2, 3}, maxlen=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 3, 4, 5}, maxlen=4)


def test_iscoll_minelem():
    ck.valset({1, 2, 3}, minelem=1)
    ck.valset({1, 2, 3}, minelem=0)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({0, 2, 3}, minelem=1)


def test_iscoll_maxelem():
    ck.valset({1, 2, 3}, maxelem=3)
    ck.valset({1, 2, 3}, maxelem=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valset({1, 2, 4}, maxelem=3)
