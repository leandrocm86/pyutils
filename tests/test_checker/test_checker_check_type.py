from tabnanny import check
import pytest
from types import SimpleNamespace
from typing import Union, Optional, List, Dict, Set, Tuple, Literal, Sequence as Seq, Mapping as Map
from typing import Mapping, Sequence
from pathlib import Path
from utils.type_checker import check as check_type

# mods/test_checker.py


def test_check_type_simple_types():
    check_type(1, int)
    check_type(1.1, float)
    check_type(True, int)  # bool is a subclass of int in Python
    check_type(True, bool)
    check_type("abc", str)
    check_type(None, type(None))
    check_type(None, None)


def test_ismap_valid():
    check_type({'a': 1, 'b': 2}, dict[str, int])
    check_type({'x': 'hello', 'y': 'world'}, Map[str, str])
    check_type(frozendict({1: True, 2: False}), frozendict[int, bool])
    check_type({}, dict[str, str])
    check_type(dict(), dict[str, str])
    check_type({'a': 1, None: 2}, dict[Optional[str], int])
    check_type({'a': 1, 'b': None}, Map[str, int | None])
    check_type({'a': [1, 2], 'b': [3, 4], 'c': []}, dict[str, list[int]])


def test_check_type_simple_type_fail():
    with pytest.raises(TypeError):
        check_type(1, str)
    with pytest.raises(TypeError):
        check_type("abc", int)
    with pytest.raises(TypeError):
        check_type(3.14, int)
    with pytest.raises(TypeError):
        check_type({123}, dict[str, int])
    with pytest.raises(TypeError):
        check_type('/nfs/scripts/', Path)


    # In python, bool is a subclass of int, so this will not raise TypeError
    # with pytest.raises(TypeError):
    #     check_type(True, int)
    with pytest.raises(TypeError):
        check_type(1, type(None))


def test_ismap_invalid_key_type():
    with pytest.raises(TypeError):
        check_type({'2': [2], 'a': [1], None: []}, dict[str, list[int]])
    with pytest.raises(TypeError):
        check_type({'a': '1', None: '2'}, dict[str, str])
    with pytest.raises(TypeError):
        check_type({None: 1, 'b': 2}, Map[str, int])


def test_ismap_invalid_value_type():
    with pytest.raises(TypeError):
        check_type({'a': 'hello', 'b': 2}, dict[str, int])
    with pytest.raises(TypeError):
        check_type({'a': None, 'b': 2}, dict[str, int])
    with pytest.raises(TypeError):
        check_type({'a': 1, 'b': None}, Map[str, int])


class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


def test_isseq_invalid_type():
    with pytest.raises(TypeError):
        check_type(123, list[int])
    with pytest.raises(TypeError):
        check_type({1, 2, 3}, Seq[int])
    with pytest.raises(TypeError):
        check_type([123], tuple[int])
    with pytest.raises(TypeError):
        check_type(tuple((1,2,3)), list[int])


def test_isseq_invalid_element_type():
    with pytest.raises(TypeError):
        check_type(['1', '2', '3'], list[int])
    with pytest.raises(TypeError):
        check_type([None], Seq[str])
    with pytest.raises(TypeError):
        check_type(tuple((1, 2)), tuple[str])
    with pytest.raises(TypeError):
        check_type(tuple((1, 2)), tuple[str, ...])
    with pytest.raises(TypeError):
        obj = SimpleNamespace(name='John', age=30)
        check_type([obj], list[Person])


def test_isseq_valid():
    check_type([1, 2, 3], list[int])
    check_type(['a', 'b', 'c'], Seq[str])
    check_type((True, False, True), tuple[bool, bool, bool])
    check_type((1, 2, 3), tuple[int, ...])
    check_type('hello', Seq[str])
    check_type([None], list[str | None])
    tup = Person('John', 30), Person('Jane', 25)
    check_type(tup, Seq[Person])


def test_isset_valid():
    check_type({1, 2, 3}, set[int])
    check_type(set(['a', 'b', 'c']), Set[str])
    check_type(frozenset((True, False)), frozenset[bool])


def test_isset_invalid_type():
    with pytest.raises(TypeError):
        check_type([1, 2, 3], set[int])
    with pytest.raises(TypeError):
        check_type('hello', Set[str])
    with pytest.raises(TypeError):
        check_type(frozenset((True, False)), set[bool])


def test_isset_invalid_element_type():
    with pytest.raises(TypeError):
        check_type({1, 2, 3}, set[str])


def test_check_type_union():
    check_type(1, Union[int, str])
    check_type("abc", int | str)
    check_type(None, Optional[int])
    check_type(7, int | None)


def test_check_type_union_fail():
    with pytest.raises(TypeError):
        check_type(3.14, Union[int, str])
    with pytest.raises(TypeError):
        check_type([], int | str)
    with pytest.raises(TypeError):
        check_type(None, Union[int, str])


def test_check_type_list():
    check_type([1, 2, 3], list[int])
    check_type([], list[int])
    check_type([1, 2, 3], List[int])


def test_check_type_list_fail():
    with pytest.raises(TypeError):
        check_type([1, "a", 3], list[int])
    with pytest.raises(TypeError):
        check_type([1, 2, 3.0], list[int])
    with pytest.raises(TypeError):
        check_type("notalist", list[int])


def test_check_type_dict():
    check_type({"a": 1, "b": 2}, dict[str, int])
    check_type({}, dict[str, int])
    check_type({"a": 1}, Dict[str, int])


def test_check_type_dict_fail():
    with pytest.raises(TypeError):
        check_type({1: "a"}, dict[str, int])
    with pytest.raises(TypeError):
        check_type({"a": "b"}, dict[str, int])
    with pytest.raises(TypeError):
        check_type([], dict[str, int])
    with pytest.raises(TypeError):
        check_type({'a', 'b'}, Map[str, int])
    with pytest.raises(TypeError):
        check_type(frozendict({'a': 1, 'b': 2}), dict[str, int])


def test_check_type_set():
    check_type({"a", "b"}, set[str])
    check_type(set(), set[str])
    check_type({"a"}, Set[str])


def test_check_type_set_fail():
    with pytest.raises(TypeError):
        check_type({1, 2, "a"}, set[int])
    with pytest.raises(TypeError):
        check_type([], set[int])
    with pytest.raises(TypeError):
        check_type(frozenset({1, 2}), set[int])


def test_check_type_tuple():
    check_type((1, 2, 3), tuple[int, ...])
    check_type((), tuple[int, ...])
    check_type((1, 2), Tuple[int, int])


def test_check_type_tuple_fail():
    with pytest.raises(TypeError):
        check_type((1, "a"), tuple[int, ...])
    with pytest.raises(TypeError):
        check_type([1, 2], tuple[int, ...])


def test_check_type_sequence_mapping_abc():
    check_type([1, 2, 3], Sequence[int])
    check_type((1, 2), Sequence[int])
    check_type({"a": 1}, Mapping[str, int])
    check_type({}, Mapping[str, int])


def test_check_type_sequence_mapping_abc_fail():
    with pytest.raises(TypeError):
        check_type([1, "a"], Sequence[int])
    with pytest.raises(TypeError):
        check_type({1: "a"}, Mapping[str, int])


def test_check_type_literal():
    check_type("a", Literal["a", "b"])
    check_type("b", Literal["a", "b"])
    with pytest.raises(TypeError):
        check_type("c", Literal["a", "b"])


def test_check_type_literal_int_and_mixed():
    check_type(1, Literal[1, 2, 3])
    with pytest.raises(TypeError):
        check_type(4, Literal[1, 2, 3])
    with pytest.raises(TypeError):
        check_type("1", Literal[1, 2, 3])
    # Mixed value types in one Literal
    check_type(1, Literal[1, "a", None])
    check_type("a", Literal[1, "a", None])
    check_type(None, Literal[1, "a", None])
    with pytest.raises(TypeError):
        check_type("b", Literal[1, "a", None])
    with pytest.raises(TypeError):
        check_type(2, Literal[1, "a", None])


def test_check_type_literal_nested():
    check_type(["a", "b"], list[Literal["a", "b"]])
    with pytest.raises(TypeError):
        check_type(["a", "c"], list[Literal["a", "b"]])
    check_type({"k": "a"}, dict[str, Literal["a", "b"]])
    with pytest.raises(TypeError):
        check_type({"k": "c"}, dict[str, Literal["a", "b"]])
    check_type(("a", 1), tuple[Literal["a", "b"], Literal[1, 2]])
    with pytest.raises(TypeError):
        check_type(("c", 1), tuple[Literal["a", "b"], Literal[1, 2]])
    # Literal combined with Union / Optional
    check_type("a", Union[Literal["a"], int])
    check_type(5, Union[Literal["a"], int])
    with pytest.raises(TypeError):
        check_type("b", Union[Literal["a"], int])
    check_type(None, Optional[Literal["a"]])
    check_type("a", Optional[Literal["a"]])
    with pytest.raises(TypeError):
        check_type("b", Optional[Literal["a"]])


def test_check_type_literal_returns_value():
    assert check_type("a", Literal["a", "b"]) == "a"
    assert check_type(1, Literal[1, 2]) == 1
    assert check_type(None, Literal[None, "a"]) is None


def test_check_type_path():
    check_type(Path("/tmp"), Path)
    with pytest.raises(TypeError):
        check_type("/tmp", Path)


def test_tuple_max_checks():
    # This checks that we honor max_checks in homogeneous tuples.
    # Must fail validation for a tuple if we provide an invalid element at index 1.
    val = (1, 'invalid', 3, 4)
    check_type(val, tuple[int, ...], max_checks=1)
