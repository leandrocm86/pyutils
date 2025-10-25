import pytest
from utils.mut import Mut


def test_mut_init_with_mutable():
    mutable_obj = [1, 2, 3]
    with Mut(mutable_obj) as m:
        assert m.unwrap() is mutable_obj


def test_mut_init_with_immutable():
    immutable_objects = [1, 1.0, "hello", True, None, (1, 2), frozenset([1, 2])]
    for immutable_obj in immutable_objects:
        with pytest.raises(AssertionError):
            Mut(immutable_obj)


def test_mut_copy():
    mutable_obj = [1, 2, 3]
    with Mut(mutable_obj, copy=True) as m:
        assert m.unwrap() is mutable_obj
        assert m.copy == mutable_obj
        assert m.copy is not mutable_obj
        m.unwrap().append(4)
        assert m.unwrap() == [1, 2, 3, 4]
        assert m.copy == [1, 2, 3]


def test_mut_deepcopy():
    mutable_obj = [1, [2, 3]]
    with Mut(mutable_obj, deepcopy=True) as m:
        assert m.unwrap() is mutable_obj
        assert m.deepcopy == mutable_obj
        assert m.deepcopy is not mutable_obj
        m.unwrap()[1].append(4)
        assert m.unwrap() == [1, [2, 3, 4]]
        assert m.deepcopy == [1, [2, 3]]


def test_mut_copy_and_deepcopy():
    mutable_obj = [1, [2, 3]]
    with Mut(mutable_obj, copy=True, deepcopy=True) as m:
        assert m.copy is not None
        assert m.deepcopy is not None
        m.unwrap()[1].append(4)
        assert m.copy == [1, [2, 3, 4]]
        assert m.deepcopy == [1, [2, 3]]


def test_mut_no_copy_no_deepcopy():
    mutable_obj = [1, 2, 3]
    with Mut(mutable_obj) as m:
        with pytest.raises(AssertionError):
            m.copy
        with pytest.raises(AssertionError):
            m.deepcopy


def test_mut_context_exit():
    mutable_obj = [1, 2, 3]
    m = Mut(mutable_obj, copy=True, deepcopy=True)
    with m:
        pass
    with pytest.raises(AssertionError):
        m.unwrap()
    with pytest.raises(AssertionError):
        m.copy
    with pytest.raises(AssertionError):
        m.deepcopy
