# mods/test_checker/test_checker_map.py

from collections.abc import Mapping
from typing import Optional
import pytest
import utils.type_checker as ck


def test_ismap_length():
    ck.valmap({'a': 1, 'b': 2}, length=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'b': 2, 'c': 3}, length=2)


def test_ismap_minlen():
    ck.valmap({'a': 1, 'b': 2}, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1}, minlen=2)


def test_ismap_maxlen():
    ck.valmap({'a': 1, 'b': 2}, maxlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'b': 2, 'c': 3, 'd': 4}, maxlen=3)


def test_ismap_minkey():
    ck.valmap({'a': 1, 'b': 2}, minkey='a')
    ck.valmap({'b': 1, 'c': 2}, minkey='a')
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'b': 1, 'c': 2}, minkey='c')


def test_ismap_maxkey():
    ck.valmap({'a': 1, 'b': 2}, maxkey='b')
    ck.valmap({'a': 1, 'b': 2}, maxkey='c')
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'c': 2}, maxkey='b')
