import pytest
from utils.mut import Mut


def test_mut_init_with_mutable():
    mutable_obj = [1, 2, 3]
    mut = Mut(mutable_obj)
    assert mut.read() is mutable_obj


def test_mut_init_with_immutable():
    immutable_objects = [1, 1.0, "hello", True, None, (1, 2), frozenset([1, 2])]
    for immutable_obj in immutable_objects:
        with pytest.raises(AssertionError):
            Mut(immutable_obj)


def test_mut_unwrap():
    mutable_obj = [1, 2, 3]
    mut = Mut(mutable_obj)
    with mut.unwrap() as m:
        assert m is mutable_obj
        m.append(4)
    assert mut.read_updated() == [1, 2, 3, 4]


def test_mut_copy_and_unwrap_shallow():
    mutable_obj: list[int | list[int]] = [1, [2, 3]]
    mut = Mut(mutable_obj)
    with mut.copy_and_unwrap() as (copy, m):
        assert m is mutable_obj
        assert copy == mutable_obj
        assert copy is not mutable_obj
        assert isinstance(m[1], list)
        m[1].append(4)
    assert mut.read_updated() == [1, [2, 3, 4]]
    assert copy == [1, [2, 3, 4]]  # Shallow copy reflects the change


def test_mut_copy_and_unwrap_deep():
    mutable_obj: list[int | list[int]] = [1, [2, 3]]
    mut = Mut(mutable_obj)
    with mut.copy_and_unwrap(deep=True) as (copy, m):
        assert m is mutable_obj
        assert copy == mutable_obj
        assert copy is not mutable_obj
        assert isinstance(m[1], list)
        m[1].append(4)
    assert mut.read_updated() == [1, [2, 3, 4]]
    assert copy == [1, [2, 3]]  # Deep copy does not reflect the change


def test_read_and_read_updated():
    mutable_obj = [1, 2, 3]
    mut = Mut(mutable_obj)
    assert mut.read() == [1, 2, 3]
    with pytest.raises(AssertionError):
        mut.read_updated()

    with mut.unwrap() as m:
        m.append(4)

    assert mut.read_updated() == [1, 2, 3, 4]
    with pytest.raises(AssertionError):
        mut.read()


def test_unwrap_once():
    mutable_obj = [1, 2, 3]
    mut = Mut(mutable_obj)
    with mut.unwrap() as m:
        m.append(4)

    with pytest.raises(AssertionError, match="The same Mut wrapper should only get unwrapped once"):
        with mut.unwrap() as m2:
            m2.append(5)

    # Test with copy_and_unwrap as well
    mut2 = Mut([1, 2, 3])
    with mut2.copy_and_unwrap() as (_, m):
        m.append(4)

    with pytest.raises(AssertionError, match="The same Mut wrapper should only get unwrapped once"):
        with mut2.copy_and_unwrap() as (_, m2):
            m2.append(5)
