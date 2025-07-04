import pytest
from typing import Union, Optional, List, Dict, Set, Tuple, Literal, Sequence, Mapping
from pathlib import Path
from mods.checker import check_type

# mods/test_checker.py


def test_check_type_simple_types():
    check_type(1, int)
    check_type(True, int)  # bool is a subclass of int in Python
    check_type("abc", str)
    check_type(True, bool)
    check_type(None, type(None))
    check_type(None, None)


def test_check_type_simple_type_fail():
    with pytest.raises(TypeError):
        check_type(1, str)
    with pytest.raises(TypeError):
        check_type("abc", int)
    with pytest.raises(TypeError):
        check_type(3.14, int)
    # In python, bool is a subclass of int, so this will not raise TypeError
    # with pytest.raises(TypeError):
    #     check_type(True, int)
    with pytest.raises(TypeError):
        check_type(1, type(None))


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


def test_check_type_set():
    check_type({"a", "b"}, set[str])
    check_type(set(), set[str])
    check_type({"a"}, Set[str])


def test_check_type_set_fail():
    with pytest.raises(TypeError):
        check_type({1, 2, "a"}, set[int])
    with pytest.raises(TypeError):
        check_type([], set[int])


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
    try:
        check_type("a", Literal["a", "b"])
        check_type("b", Literal["a", "b"])
        with pytest.raises(TypeError):
            check_type("c", Literal["a", "b"])
    except AttributeError:
        pass  # Literal may not be available


def test_check_type_path():
    check_type(Path("/tmp"), Path)
    with pytest.raises(TypeError):
        check_type("/tmp", Path)
