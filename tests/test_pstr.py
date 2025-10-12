from typing import Any
from utils.pstr import pstr, __color, __COLOR_END  # type: ignore


def test_pstr_lists():
    assert pstr([1, 2, 3]) == "[1, 2, 3]"
    assert pstr([]) == "[]"


def test_pstr_sets():
    assert pstr({1, 2, 3}) == "{1, 2, 3}"
    assert pstr(set()) == "{}"  # type: ignore


def test_pstr_dicts():
    assert pstr({"a": 1, "b": 2}) == "{a: 1, b: 2}"
    assert pstr({}) == "{}"


def test_pstr_tuples():
    assert pstr((1, 2, 3)) == "(1, 2, 3)"
    assert pstr(()) == "()"


def test_pstr_complex_objects():
    class TestObject:
        def __init__(self, x: int, y: int):
            self.x = x
            self.y = y

    obj = TestObject(1, 2)
    assert pstr(obj) == '{x: 1, y: 2}'


def test_pstr_maxlen():
    long_list = list(range(100))
    assert pstr(long_list, maxlen=10) == "[0, 1, 2, 3, 4, ... , 95, 96, 97, 98, 99](len=100)"
    assert pstr(long_list, maxlen=4) == "[0, 1, ... , 98, 99](len=100)"
    long_string = 'abcdefghijklmnopqrstuvwyxz'
    assert pstr(long_string, maxlen=10) == 'abcde(...len=26)vwyxz'


def test_pstr_maxdepth():
    nested_list: list[Any] = [1, [2, [3, [4, 5]]], 6]
    assert pstr(nested_list, maxdepth=2) == "[1, [2, list(...)], 6]"
    assert pstr(nested_list, maxdepth=3) == "[1, [2, [3, list(...)]], 6]"


def test_pstr_maxlen_and_maxdepth():
    long_nested_list: list[Any] = [1, [2, [3, [4, 5]]], '', '', 6, [7, tuple((8, [9, [10, 11]]))], None]
    assert pstr(long_nested_list, maxlen=5, maxdepth=2) == "[1, [2, list(...)], ... , [7, tuple(...)], None](len=7)"


def test_pstr_edge_cases():
    assert pstr([], maxlen=0) == "list(...)"
    assert pstr(tuple(()), maxdepth=0) == "tuple(...)"
    assert pstr({1, 2, 3}, maxlen=0) == "set(...)"
    assert pstr({1: 2, 3: 4}, maxdepth=0) == "dict(...)"


def test_pstr_recursive():
    weird_list: list[Any] = [1, [2, tuple(('a', 'b', {'c': True, 'd': False, 'e': {1.2, 3.4}})), 3, ('ge', 'ne', 'ra', 'tor')], 4]
    assert pstr(weird_list, maxdepth=5) == "[1, [2, (a, b, {c: True, d: False, e: {1.2, 3.4}}), 3, (ge, ne, ra, tor)], 4]"


def test_pstr_colored():
    x: list[Any] = [[1, 2, tuple(('abcdefghijklm', 'b'))], {True: 0, False: 0}, {None}]
    assert pstr(x, maxlen=6, colored=True) == \
        __color(0) + '[' + \
        __COLOR_END + __color(1) + '[1, 2, ' + \
        __COLOR_END + __color(2) + '(abcdefghijklm, b)' + \
        __COLOR_END + __color(1) + ']' + \
        __COLOR_END + __color(0) + ', ' + \
        __COLOR_END + __color(1) + '{True: 0, False: 0}' + \
        __COLOR_END + __color(0) + ', ' + \
        __COLOR_END + __color(1) + '{None}' + \
        __COLOR_END + __color(0) + ']' + __COLOR_END


def test_pstr_nested_objects_colored():
    class Person:
        def __init__(self, name: str, friend: 'Person'):
            self.name = name
            self.friend = friend
   
    john = Person('John', Person('Peter', None))
    assert pstr(john, colored=True) == \
        __color(0) + '{' + \
        'name: John, friend: ' + \
        __COLOR_END + __color(1) + '{' + \
        'name: Peter, friend: None}' + \
        __COLOR_END + __color(0) + '}' + __COLOR_END