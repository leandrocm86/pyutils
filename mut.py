import copy as cp
from types import NoneType
from typing import Generic, TypeVar


# Immutable types
IMMUTABLE_TYPES = (int, float, str, bool, NoneType, tuple, frozenset)

T_Object = TypeVar('T_Object', bound=object)


class InvalidMutationError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class Mut(Generic[T_Object]):
    """
    Context manager that wraps a given mutable object that is expected to suffer change.
    Optionally, it may make a copy (or deepcopy) of the object, so a comparison or rollback can be done later.

    Args:
        mutable_object: The object that is about to get modified in this context.
        copy: Whether to make a copy of the mutable object.
        deepcopy: Whether to make a deepcopy of the mutable object.
    """
    def __init__(
            self,
            mutable_object: T_Object,
            copy: bool = False,
            deepcopy: bool = False):

        assert not isinstance(mutable_object, IMMUTABLE_TYPES), \
            f"Object expected to be mutable is actually from immutable type: {type(mutable_object)}"  # type: ignore
        self._mutable_object = mutable_object
        self._copy = cp.copy(mutable_object) if copy else None
        self._deepcopy = cp.deepcopy(mutable_object) if deepcopy else None

    def __enter__(self) -> 'Mut[T_Object]':
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._mutable_object = None
        self._copy = None
        self._deepcopy = None

    def unwrap(self) -> T_Object:
        assert self._mutable_object, "Mutable object not available. Make sure that it's not being accessed after cleanup of the context manager"
        return self._mutable_object

    @property
    def copy(self) -> T_Object:
        assert self._copy, "Copy not available. Make sure it was requested in Mut's creation and that it's not being accessed after cleanup of the context manager"
        return self._copy

    @property
    def deepcopy(self) -> T_Object:
        assert self._deepcopy, "Deepcopy not available. Make sure it was requested in Mut's creation and that it's not being accessed after cleanup of the context manager"
        return self._deepcopy
