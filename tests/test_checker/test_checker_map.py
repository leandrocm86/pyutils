# mods/test_checker/test_checker_map.py

from collections.abc import Mapping
from typing import Optional
import pytest
from typeguard import TypeCheckError
import mods.checker as ck


def test_ismap_valid():
    ck.mapok({'a': 1, 'b': 2}, str, int)
    ck.mapok({'x': 'hello', 'y': 'world'}, str, str)
    ck.mapok({1: True, 2: False}, int, bool)
    ck.mapok({}, str, str)
    ck.mapok({'a': 1, None: 2}, Optional[str], int)
    ck.mapok({'a': 1, 'b': None}, str, Optional[int])
    ck.mapok({'a': [1, 2], 'b': [3, 4], 'c': []}, str, list[int])


def test_ismap_invalid_type():
    with pytest.raises(TypeCheckError):
        ck.mapok('123', str, int)  # type: ignore
    with pytest.raises(TypeCheckError):
        ck.mapok({'a', 'b', 'c'}, str, int)  # type: ignore


def test_ismap_invalid_key_type():
    with pytest.raises(TypeCheckError):
        ck.mapok({'2': [2], 'a': [1], None: []}, str, list[int])
    with pytest.raises(TypeCheckError):
        ck.mapok({'a': '1', None: '2'}, str, str)
    with pytest.raises(TypeCheckError):
        ck.mapok({None: 1, 'b': 2}, str, int)


def test_ismap_invalid_value_type():
    with pytest.raises(TypeCheckError):
        ck.mapok({'a': 'hello', 'b': 2}, str, int)
    with pytest.raises(TypeCheckError):
        ck.mapok({'a': None, 'b': 2}, str, int)
    with pytest.raises(TypeCheckError):
        ck.mapok({'a': 1, 'b': None}, str, int)


def test_ismap_length():
    ck.mapok({'a': 1, 'b': 2}, str, int, length=2)
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'a': 1, 'b': 2, 'c': 3}, str, int, length=2)


def test_ismap_minlen():
    ck.mapok({'a': 1, 'b': 2}, str, int, minlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'a': 1}, str, int, minlen=2)


def test_ismap_maxlen():
    ck.mapok({'a': 1, 'b': 2}, str, int, maxlen=2)
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'a': 1, 'b': 2, 'c': 3, 'd': 4}, str, int, maxlen=3)


def test_ismap_minkey():
    ck.mapok({'a': 1, 'b': 2}, str, int, minkey='a')
    ck.mapok({'b': 1, 'c': 2}, str, int, minkey='a')
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'b': 1, 'c': 2}, str, int, minkey='c')


def test_ismap_maxkey():
    ck.mapok({'a': 1, 'b': 2}, str, int, maxkey='b')
    ck.mapok({'a': 1, 'b': 2}, str, int, maxkey='c')
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'a': 1, 'c': 2}, str, int, maxkey='b')


def test_ismap_custom():
    def custom_check(map: Mapping[str, int]):
        return sum(map.values()) > 5

    ck.mapok({'a': 1, 'b': 2, 'c': 3}, str, int, custom=custom_check)
    with pytest.raises(ck.InvalidContractError):
        ck.mapok({'a': 1, 'b': 2}, str, int, custom=custom_check)
