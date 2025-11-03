import copy as cp
from contextlib import contextmanager
from types import NoneType
from typing import Generic, Iterator, Tuple, TypeVar

# Immutable types
IMMUTABLE_TYPES = (int, float, str, bool, NoneType, tuple, frozenset)
T_Object = TypeVar('T_Object', bound=object)


class Mut(Generic[T_Object]):
    """
    Wraps a mutable object to make mutations more explicit and to help validate them.

    The class provides context managers to access the wrapped object for mutation,
    and read-only methods to access it before and after mutation.
    """
    def __init__(self, mutable_object: T_Object):
        """
        Initializes the Mut wrapper.

        Args:
            mutable_object: The object that is expected to be mutated.
        """
        assert not isinstance(mutable_object, IMMUTABLE_TYPES), \
            f"Object expected to be mutable is actually from immutable type: {type(mutable_object)}"  # type: ignore
        self._mutable_object = mutable_object
        self._unwrap_count = 0

    def read(self) -> T_Object:
        """
        Returns the wrapped object for read-only purposes before mutation.

        This method is intended to be used for accessing the object's state
        before any mutation has occurred. It asserts that the object has not
        been unwrapped for mutation yet.

        For mutation, use the `unwrap` or `copy_and_unwrap` context managers.

        Returns:
            The wrapped object.
        """
        assert self._unwrap_count == 0, "read() should only be used before the object is mutated."
        return self._mutable_object

    def read_updated(self) -> T_Object:
        """
        Returns the wrapped object for read-only purposes after mutation.

        This method is intended to be used for accessing the object's state
        after a mutation has occurred. It asserts that the object has already
        been unwrapped for mutation.

        For mutation, use the `unwrap` or `copy_and_unwrap` context managers.

        Returns:
            The wrapped object.
        """
        assert self._unwrap_count > 0, "read_updated() should only be used after the object is mutated."
        return self._mutable_object

    @contextmanager
    def unwrap(self) -> Iterator[T_Object]:
        """
        A context manager that yields the wrapped mutable object for mutation.

        This is the primary way to access the object for mutation. It ensures
        that the mutation is explicit. The wrapper can only be unwrapped once.
        """
        try:
            yield self._mutable_object
        finally:
            self._unwrap_count += 1
            assert self._unwrap_count <= 1, "The same Mut wrapper should only get unwrapped once"

    @contextmanager
    def copy_and_unwrap(self, deep: bool = False) -> Iterator[Tuple[T_Object, T_Object]]:
        """
        A context manager that yields a copy of the wrapped object and the object itself for mutation.

        This is useful when you need to compare the object's state before and
        after mutation. The wrapper can only be unwrapped once.

        Args:
            deep: If True, a deep copy of the object is made. Otherwise, a shallow copy is made.

        Yields:
            A tuple containing the copy of the original object and the mutable object itself.
        """
        copy_func = cp.deepcopy if deep else cp.copy
        original_copy = copy_func(self._mutable_object)
        try:
            yield original_copy, self._mutable_object
        finally:
            self._unwrap_count += 1
            assert self._unwrap_count <= 1, "The same Mut wrapper should only get unwrapped once"
