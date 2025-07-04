# mods/test_checker/test_checker_map.py

from collections.abc import Mapping
from typing import Optional
import pytest
import mods.type_checker as ck


def test_ismap_valid():
    ck.valmap({'a': 1, 'b': 2}, str, int)
    ck.valmap({'x': 'hello', 'y': 'world'}, str, str)
    ck.valmap({1: True, 2: False}, int, bool)
    ck.valmap({}, str, str)
    ck.valmap({'a': 1, None: 2}, Optional[str], int)
    ck.valmap({'a': 1, 'b': None}, str, Optional[int])
    ck.valmap({'a': [1, 2], 'b': [3, 4], 'c': []}, str, list[int])


def test_ismap_invalid_type():
    with pytest.raises(TypeError):
        ck.valmap('123', str, int)  # type: ignore
    with pytest.raises(TypeError):
        ck.valmap({'a', 'b', 'c'}, str, int)  # type: ignore


def test_ismap_invalid_key_type():
    with pytest.raises(TypeError):
        ck.valmap({'2': [2], 'a': [1], None: []}, str, list[int])
    with pytest.raises(TypeError):
        ck.valmap({'a': '1', None: '2'}, str, str)
    with pytest.raises(TypeError):
        ck.valmap({None: 1, 'b': 2}, str, int)


def test_ismap_invalid_value_type():
    with pytest.raises(TypeError):
        ck.valmap({'a': 'hello', 'b': 2}, str, int)
    with pytest.raises(TypeError):
        ck.valmap({'a': None, 'b': 2}, str, int)
    with pytest.raises(TypeError):
        ck.valmap({'a': 1, 'b': None}, str, int)


def test_ismap_length():
    ck.valmap({'a': 1, 'b': 2}, str, int, length=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'b': 2, 'c': 3}, str, int, length=2)


def test_ismap_minlen():
    ck.valmap({'a': 1, 'b': 2}, str, int, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1}, str, int, minlen=2)


def test_ismap_maxlen():
    ck.valmap({'a': 1, 'b': 2}, str, int, maxlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'b': 2, 'c': 3, 'd': 4}, str, int, maxlen=3)


def test_ismap_minkey():
    ck.valmap({'a': 1, 'b': 2}, str, int, minkey='a')
    ck.valmap({'b': 1, 'c': 2}, str, int, minkey='a')
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'b': 1, 'c': 2}, str, int, minkey='c')


def test_ismap_maxkey():
    ck.valmap({'a': 1, 'b': 2}, str, int, maxkey='b')
    ck.valmap({'a': 1, 'b': 2}, str, int, maxkey='c')
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'c': 2}, str, int, maxkey='b')


def test_ismap_custom():
    def custom_check(map: Mapping[str, int]):
        return sum(map.values()) > 5

    ck.valmap({'a': 1, 'b': 2, 'c': 3}, str, int, custom=custom_check)
    with pytest.raises(ck.InvalidContractError):
        ck.valmap({'a': 1, 'b': 2}, str, int, custom=custom_check)
