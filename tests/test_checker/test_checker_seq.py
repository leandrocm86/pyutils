from collections.abc import Sequence
from types import SimpleNamespace
from typing import Union
import pytest
import utils.type_checker as ck


def test_iscoll_length():
    ck.valseq([1, 2, 3], length=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 3], length=4)


def test_iscoll_minlen():
    ck.valseq([1, 2, 3], minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1], minlen=2)


def test_iscoll_maxlen():
    ck.valseq([1, 2, 3], maxlen=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 3, 4, 5], maxlen=4)


def test_iscoll_minelem():
    ck.valseq([1, 2, 3], minelem=1)
    ck.valseq([1, 2, 3], minelem=0)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 2, 3], minelem=1)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 2, 3], minelem='0')


def test_iscoll_maxelem():
    ck.valseq([1, 2, 3], maxelem=3)
    ck.valseq([1, 2, 3], maxelem=4)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 4], maxelem=3)
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([1, 2, 4], maxelem=['4'])


def test_iscoll_minelem_with_zero():
    # This should fail, but currently might be bypassed if minelem=0
    # because 'if minelem:' evaluates to False.
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, -1, -2], minelem=0)


def test_iscoll_maxelem_with_zero():
    # This should fail, but might be bypassed if maxelem=0
    # because 'if maxelem:' evaluates to False.
    with pytest.raises(ck.InvalidContractError):
        ck.valseq([0, 1, 2], maxelem=0)
