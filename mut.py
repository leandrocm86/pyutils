import copy
from contextlib import contextmanager
from types import NoneType
from typing import Callable, Optional, TypeVar


# Immutable types
IMMUTABLE_TYPES = (int, float, str, bool, NoneType, tuple, frozenset)

T_Object = TypeVar('T_Object', bound=object)


class InvalidMutationError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


@contextmanager
def mut(mutable_object: T_Object,
        expect: Optional[Callable[[T_Object], bool]] = None,
        expect_diff: Optional[Callable[[T_Object, T_Object], bool]] = None,
        expect_deepdiff: Optional[Callable[[T_Object, T_Object], bool]] = None):
    """
    Context manager that wraps changes to be made on a given mutable object.
    Optionally, it may perform verifications about the final state of the object (expect parameter),
    or verifications about comparisons between the original and final states of the object (expect_diff and expect_deepdiff parameters).

    Args:
        mutable_object: The object that is about to get modified in this context.
        expect: A function that receives the final state of the object and returns True if the object is in the expected state. If the result is False, an exception is raised.
        expect_diff: A function that receives the original and final states of the object and returns True if the changes are valid. If the result is False, an exception is raised. The original state is preserved by a shallow copy of the object at the beginning of the context.
        expect_deepdiff: A function that receives the original and final states of the object and returns True if the changes are valid. If the result is False, an exception is raised. The original state is preserved by a deep copy of the object at the beginning of the context.
    """

    assert not isinstance(mutable_object, IMMUTABLE_TYPES), f"Object expected to be mutable is actually from immutable type: {type(mutable_object)}"  # type: ignore

    snapshot_obj = None
    if expect_diff or expect_deepdiff:
        copyfunc = copy.deepcopy if expect_deepdiff else copy.copy
        snapshot_obj = copyfunc(mutable_object)

    yield

    if expect:
        expectation_met = False
        try:
            expectation_met = expect(mutable_object)
        except Exception as e:
            raise InvalidMutationError(f"Error raised when evaluating the final state of mutable object: {e}")
        if not expectation_met:
            raise InvalidMutationError("Final state of mutable object was not as expected")

    if expect_deepdiff or expect_diff:
        diff_func = expect_deepdiff if expect_deepdiff else expect_diff
        expectation_met = False
        try:
            expectation_met = diff_func(snapshot_obj, mutable_object)  # type: ignore
        except Exception as e:
            raise InvalidMutationError(f"Error raised when evaluating the comparison function for the mutable object: {e}")
        if not expectation_met:
            raise InvalidMutationError("Changes between the previous and final state of mutable object were not as expected")
