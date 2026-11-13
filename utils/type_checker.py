from collections.abc import Collection, Iterable, Mapping as Map, Sequence as Seq
from typing import get_origin, get_args, Any, Literal, Union
lazy from pathlib import Path
lazy from re import Pattern, compile
lazy from utils.pstr import pstr
lazy import functools
lazy import os
lazy import types


class InvalidContractError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def hide_internal_frames(exc_types=(TypeError, ValueError, InvalidContractError)):
    """Decorator: collapses any internal call chain down to a single frame."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exc_types as e:
                raise type(e)(str(e)) from None
        return wrapper
    return decorator


def _error(msg: str):
    raise InvalidContractError(msg)


@hide_internal_frames()
def check[T](value: Any, expected_type: T, max_checks: int = 100) -> T:
    """
    Validate that a value matches the expected type at runtime.

    Supports both regular types and generic type annotations.
    For collections, checks only up to the first 100 elements (by default).

    Args:
        value: The value to check
        expected_type: The expected type or generic type annotation
        max_checks: Maximum number of elements to check in collections (default is 100)

    Raises:
        TypeError: If the value doesn't match the expected type
    """
    # Handle None/NoneType specially
    if expected_type is type(None) or expected_type is None:
        if value is not None:
            raise TypeError(f"Expected None, got {type(value).__name__}")
        return None  # type: ignore

    # Handle Union types (including Optional and | syntax)
    origin = get_origin(expected_type)
    if _is_union_type(expected_type, origin):
        var_args = get_args(expected_type)
        for arg in var_args:
            try:
                check(value, arg, max_checks)
                return value  # If any type matches, we're good
            except TypeError:
                continue
        # If none matched, raise error
        type_names = [_get_type_name(arg) for arg in var_args]
        raise TypeError(f"Expected one of {type_names}, got {type(value).__name__}")

    # Handle Literal types first (before checking origin)
    if _is_literal_type(expected_type):
        var_args = get_args(expected_type)
        if value not in var_args:
            raise TypeError(f"Expected one of {var_args}, got {value!r}")
        return value

    # Handle generic types
    if origin is not None:
        # Check the base type first
        if not isinstance(value, origin):
            raise TypeError(f"Expected {_get_type_name(expected_type)}, got {type(value).__name__}")

        # Check generic arguments
        var_args = get_args(expected_type)
        if var_args:
            __check_generic_args(value, origin, var_args, max_checks)
    else:
        # Handle regular types
        if not isinstance(value, expected_type):  # type: ignore
            raise TypeError(f"Expected {_get_type_name(expected_type)}, got {type(value).__name__}")
    return value


def _is_literal_type(type_obj: Any) -> bool:
    """Check if a type is a Literal type."""
    origin = get_origin(type_obj)
    return origin is Literal


def _is_union_type(type_obj: Any, origin: Any) -> bool:
    """Check if a type is a Union type (including | syntax)."""
    if origin is Union:
        return True
    return isinstance(type_obj, types.UnionType)


def __check_generic_args(value: Any, origin: Any, args: tuple[Any, ...], max_checks: int) -> None:
    """Check generic type arguments for collections."""

    if origin in (list, set, frozenset, Seq):
        # For homogeneous collections, check element type
        if len(args) == 1:
            var_element_type = args[0]
            var_items = list(value)[:max_checks] if hasattr(value, '__iter__') else []
            for i, item in enumerate(var_items):
                try:
                    check(item, var_element_type, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Element at index {i}: {e}")

    elif origin in (tuple, tuple):
        # Handle tuple types specially
        if len(args) == 2 and args[1] is ...:
            # tuple[int, ...] - homogeneous tuple of any length
            var_element_type = args[0]
            # Check up to max_checks elements
            var_items = list(value)[:max_checks]
            for i, item in enumerate(var_items):
                try:
                    check(item, var_element_type, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Element at index {i}: {e}")
        else:
            # tuple[int, str, bool] - fixed-length tuple with specific types
            if len(value) != len(args):
                raise TypeError(f"Expected tuple of length {len(args)}, got length {len(value)}")
            for i, (item, expected_type) in enumerate(zip(value, args)):
                try:
                    check(item, expected_type, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Element at index {i}: {e}")

    elif origin in (dict, Map):
        if max_checks:
            var_items = list(value.items())[:max_checks]
        else:
            var_items = list(value.items())

        # For dictionaries, check key and value types
        keytype = valtype = None
        if len(args) == 2:
            keytype, valtype = args

        if keytype:
            for key, _ in var_items:
                try:
                    check(key, keytype, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Dictionary key {key!r}: {e}")

        if valtype:
            for key, val in var_items:
                try:
                    check(val, valtype, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Dictionary value for key {key!r}: {e}")

    # Note: Literal types are handled eagerly in check() via _is_literal_type(),
    # so they never reach here. No `origin is Literal` branch is needed
    # (and `is`-comparing against the Literal special form trips mypy
    # strict-equality: "Non-overlapping identity check").

    # Add more generic type handlers as needed
    # For now, other generic types will just check the base type


def _get_type_name(type_obj: Any) -> str:
    """Get a readable name for a type annotation."""
    if hasattr(type_obj, '__name__'):
        return type_obj.__name__
    elif hasattr(type_obj, '_name') and type_obj._name:
        return type_obj._name
    else:
        return str(type_obj)


@hide_internal_frames()
def valstr(value: str,
           length: int | None = None,
           minlen: int = 0,
           maxlen: int | None = None,
           upper: bool = False,
           lower: bool = False,
           regex: str | Pattern[str] | None = None,
           domain: Iterable[str] | None = None) -> str:
    """ Runtime validation for strings.
    Checks optionally given constraints on a string, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (str):
            The string to validate.
        length (Optional[int]):
            The expected length of the string. Defaults to None (no validation).
        minlen (int):
            The minimum length of the string. Defaults to 0.
        maxlen (Optional[int]):
            The maximum length of the string. Defaults to None (no validation).
        upper (bool):
            Whether the string should be upper case. Defaults to False (no validation).
        lower (bool):
            Whether the string should be lower case. Defaults to False (no validation).
        regex (Union[str, Pattern[str], None]):
            A regular expression to match against the string. Defaults to None (no validation).
        domain (Optional[Iterable[str]]):
            A collection of valid values for the string. Defaults to None (no validation).
    """

    if length is not None and len(value) != length:
        _error(f'Invalid str: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid str: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid str: expected maximum length {maxlen}, got {len(value)}.')

    if upper and not value.isupper():
        offending_lower = next((c for c in value if not c.isupper()), None)
        if offending_lower is not None:
            _error(f'Invalid str: expected upper, got "{offending_lower}" in {pstr(value, maxlen=50)}.')
        else:
            # This case should ideally not be reached if value.isupper() is False, but included for safety.
            _error(f'Invalid str: expected upper, but no non-uppercase character found in {pstr(value, maxlen=50)}.')

    if lower and not value.islower():
        offending_upper = next((c for c in value if not c.islower()), None)
        if offending_upper is not None:
            _error(f'Invalid str: expected lower, got "{offending_upper}" in "{pstr(value, maxlen=50)}".')
        else:
            # This case should ideally not be reached if value.islower() is False, but included for safety.
            _error(f'Invalid str: expected lower, but no non-lowercase character found in "{pstr(value, maxlen=50)}".')

    if regex:
        if isinstance(regex, str):
            regex = compile(regex)
        if not regex.match(value):
            _error(f'Invalid str: expected regex "{regex.pattern}", '
                   + f'but it didn\'t match with string "{pstr(value, maxlen=50)}".')

    if domain and value not in domain:
        _error(f'Invalid str: expected domain {pstr(domain, maxlen=50)} '
               + f'doesn\'t contain value "{pstr(value, maxlen=50)}".')

    return value


@hide_internal_frames()
def valint(value: int,
           min: int | None = None,
           max: int | None = None,
           domain: Iterable[int] | None = None) -> int:
    """ Runtime validation for integers.
    Checks optionally given constraints on an integer, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (int): The integer to validate.
        min (Optional[int]): The minimum value of the integer. Defaults to None (no validation).
        max (Optional[int]): The maximum value of the integer. Defaults to None (no validation).
        domain (Optional[Iterable[int]]): A collection of valid values for the integer. Defaults to None (no validation).
    """

    if min is not None and value < min:
        _error(f'Invalid int: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid int: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid int: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    return value


@hide_internal_frames()
def valfloat(value: float,
             min: float | None = None,
             max: float | None = None,
             domain: Iterable[float] | None = None) -> float:
    """ Runtime validation for floats.
    Checks optionally given constraints on a float, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (float):
            The float to validate.
        min (Optional[float]):
            The minimum value of the float. Defaults to None (no validation).
        max (Optional[float]):
            The maximum value of the float. Defaults to None (no validation).
        domain (Optional[Iterable[float]]):
            A collection of valid values for the float. Defaults to None (no validation).
    """

    if min is not None and value < min:
        _error(f'Invalid float: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid float: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid float: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    return value


def __collectionok(value: Collection[Any],
                   length: int | None = None,
                   minlen: int = 0,
                   maxlen: int | None = None,
                   minelem: Any = None,
                   maxelem: Any = None):

    if length is not None and len(value) != length:
        _error(f'Invalid sequence: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid sequence: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid sequence: expected maximum length {maxlen}, got {len(value)}.')

    if minelem is not None and value:
        if not hasattr(minelem, '__lt__'):
            _error(f'Impossible validation: the minimum element\'s type is not comparable: {type(minelem)}.')
        else:
            minv = min(value)
            if not isinstance(minv, type(minelem)):
                _error('Impossible validation of minimum element: expected minimum element'
                       + f' of type {type(minelem)}, got {type(minv)}.')
            elif minv < minelem:
                _error(f'Invalid sequence: expected minimum element {pstr(minelem)}, got {pstr(minv)}.')

    if maxelem is not None and value:
        if not hasattr(maxelem, '__lt__'):
            _error(f'Impossible validation: the maximum element\'s type is not comparable: {type(maxelem)}.')
        else:
            maxv = max(value)
            if not isinstance(maxv, type(maxelem)):
                _error('Impossible validation of maximum element: expected maximum element'
                       + f' of type {type(maxelem)}, got {type(maxv)}.')
            elif maxv > maxelem:
                _error(f'Invalid sequence: expected maximum element {pstr(maxelem)}, got {pstr(maxv)}.')


@hide_internal_frames()
def valseq[T](value: Seq[T],
              length: int | None = None,
              minlen: int = 0,
              maxlen: int | None = None,
              minelem: T | None = None,
              maxelem: T | None = None) -> Seq[T]:  # Added max_checks here
    """ Runtime validation for sequences (lists and tuples).
    Checks optionally given constraints on a list/tuple/Sequence object,
    possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (Seq[T]):
            The sequence to validate.
        length (Optional[int]):
            The length of the sequence. Defaults to None (no validation).
        minlen (int):
            The minimum length of the sequence. Defaults to 0.
        maxlen (Optional[int]):
            The maximum length of the sequence. Defaults to None (no validation).
        minelem (Optional[T]):
            The minimum element of the sequence. Defaults to None (no validation).
            The element type must be comparable.
        maxelem (Optional[T]):
            The maximum element of the sequence. Defaults to None (no validation).
            The element type must be comparable.
    """

    __collectionok(value, length, minlen, maxlen, minelem, maxelem)

    return value


@hide_internal_frames()
def valset[T](value: set[T],
              length: int | None = None,
              minlen: int = 0,
              maxlen: int | None = None,
              minelem: T | None = None,
              maxelem: T | None = None) -> set[T]:
    """ Runtime validation for sets.
    Checks optionally given constraints on a set object, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (Set[T]):
            The set to validate.
        length (Optional[int]):
            The length of the set. Defaults to None (no validation).
        minlen (int):
            The minimum length of the set. Defaults to 0.
        maxlen (Optional[int]):
            The maximum length of the set. Defaults to None (no validation).
        minelem (Optional[T]):
            The minimum element of the set. Defaults to None (no validation).
            The element type must be comparable.
        maxelem (Optional[T]):
            The maximum element of the set. Defaults to None (no validation).
            The element type must be comparable.
    """

    __collectionok(value, length, minlen, maxlen, minelem, maxelem)

    return value


@hide_internal_frames()
def valmap[K, V](value: Map[K, V],
                 length: int | None = None,
                 minlen: int = 0,
                 maxlen: int | None = None,
                 minkey: K | None = None,
                 maxkey: K | None = None) -> Map[K, V]:  # Added max_checks here
    """ Runtime validation for maps (dictionaries).
    Checks optionally given constraints on a dict/Mapping object, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.

    Args:
        value (Map[K, V]):
            The dict/Mapping to validate.
        length (Optional[int]):
            The length of the map. Defaults to None (no validation).
        minlen (int):
            The minimum length of the map. Defaults to 0.
        maxlen (Optional[int]):
            The maximum length of the map. Defaults to None (no validation).
        minkey (Optional[K]):
            The minimum key of the map. Defaults to None (no validation).
            The key type must be comparable.
        maxkey (Optional[K]):
            The maximum key of the map. Defaults to None (no validation).
            The key type must be comparable.
    """

    if length is not None and len(value) != length:
        _error(f'Invalid map: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid map: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid map: expected maximum length {maxlen}, got {len(value)}.')

    if minkey is not None and value:
        if not hasattr(minkey, '__lt__'):
            _error(f'Impossible validation: the minimum key\'s type is not comparable: {type(minkey)}.')
        elif (minv := min(value)) < minkey:  # type: ignore
            _error(f'Invalid map: expected minimum key {pstr(minkey)}, got {pstr(minv)}.')

    if maxkey is not None and value:
        if not hasattr(maxkey, '__lt__'):
            _error(f'Impossible validation: the maximum key\'s type is not comparable: {type(maxkey)}.')
        elif (maxv := max(value)) > maxkey:  # type: ignore
            _error(f'Invalid map: expected maximum key {pstr(maxkey)}, got {pstr(maxv)}.')

    return value


@hide_internal_frames()
def valpath(value: Path,
            exists: bool | None = None,
            is_dir_if_exists: bool | None = None,
            match: str | None = None,
            full_match: str | None = None,
            can_create_if_not_exists: bool | None = None,
            can_read_if_exists: bool | None = None,
            can_modify_if_exists: bool | None = None,
            can_execute_if_exists: bool | None = None) -> Path:
    """ Runtime validation for paths.
    Checks optionally given constraints on a Path object, possibly raising InvalidContractError.
    If no error is raised, the original value is returned.
    The most important argument "exists" may imply a validation on its own and on many other arguments.

    Args:
        value (Path):
            The path to validate.
        exists (Optional[bool]):
            If True, the path must exist.
            If False, I must not exist.
            If None, the existence is not validated.
        is_dir_if_exists (Optional[bool]):
            If True, it must be a directory.
            If False, it must be a file.
            If None, or if the path does not exist, there's no validation.
        match (Optional[str]):
            If not None, the path must match this glob (see Path's match method).
        full_match (Optional[str]):
            If not None, the path must fully match this glob (see Path's fullmatch method).
        can_create_if_not_exists (Optional[bool]):
            If True, it must be creatable.
            If False, it must not be creatable.
            If None, or if the path already exists, there's no validation.
        can_read_if_exists (Optional[bool]):
            If True, it must be readable.
            If False, it must not be readable.
            If None, or if the path does not exist, there's no validation.
        can_modify_if_exists (Optional[bool]):
            If True, it must be modifiable.
            If False, it must not be modifiable.
            If None, or if the path does not exist, there's no validation.
        can_execute_if_exists (Optional[bool]):
            If True, it must be executable.
            If False, it must not be executable.
            If None, or if the path does not exist, there's no validation.
    """

    def __verify_parents_permissions() -> str:
        var_current = value
        while var_current != var_current.parent:  # Stop at root directory
            var_current = var_current.parent
            if var_current.exists() and not os.access(var_current, os.X_OK):   # Check if parent is traversable
                return 'parent folders seem to miss execute permission'
        return ''

    needs_traversal = (
        exists is True or
        is_dir_if_exists is not None or
        can_read_if_exists is not None or
        can_modify_if_exists is not None or
        can_execute_if_exists is not None or
        can_create_if_not_exists is True
    )

    if needs_traversal:
        try:
            if not value.exists():
                permission_error = __verify_parents_permissions()
                if permission_error:
                    _error(permission_error)
        except PermissionError:
            # This can happen if the user running the script can't even access the parent directory
            _error('parent folders seem to miss execute permission')

    def __verify_path_exists() -> str:
        try:
            if not value.exists():
                return f'\nPath {value} doesn\'t exist.'
            else:
                return ''
        except PermissionError:
            return f"PermissionError when trying to check if path {value} exists. " \
                    + "Maybe it misses read permission, or its parents aren't traversable (miss execute permission)."

    # def __verify_readable_path() -> str:
    #     if not os.access(value, os.R_OK):
    #         return (f"\nPath {value} is not readable.
    #                "Maybe it doesn't exist, miss read permission,
    #                "or its parents aren't traversable (no execute permission).")
    #     return ''

    def __check_permission_if_exists(permission_code: int, permission_desc: str, expected: bool | None):
        if expected is not None:
            try:
                if value.exists() and expected != (actual := os.access(value, permission_code)):
                    _error(f'Invalid {permission_desc} path permissions for {value}.'
                           f' Expected {expected}, got {actual}.')
            except PermissionError:
                _error(f'Permission error when trying to check existence of path {value}.'
                       + __verify_parents_permissions())

    if is_dir_if_exists is not None:
        expected = 'directory' if is_dir_if_exists else 'file'
        try:
            if value.exists():
                try:
                    is_actually_dir = value.is_dir()
                    is_actually_file = value.is_file()
                    if is_actually_dir == is_actually_file:
                        _error(f"Impossible to check if path {value} is a {expected}. Maybe it doesn't exist."
                               + __verify_path_exists())
                    elif is_actually_dir != is_dir_if_exists:
                        actually = 'directory' if is_actually_dir else 'file'
                        _error(f'Invalid path: expected {expected}, got {actually}.')
                except PermissionError:
                    _error(f'Permission error when trying to check '
                           f'if path {value} is a {expected}.' + __verify_parents_permissions())
        except PermissionError:
            _error(f'Permission error when trying to check existence of path {value}.'
                   + __verify_parents_permissions())

    if exists is not None:
        try:
            if exists != value.exists():
                _error(f"Path {value} doesn't exist." if exists else f'Path {value} exists.')
        except PermissionError:
            _error(f'Permission error when trying to check if path {value} exists.' + __verify_parents_permissions())

    __check_permission_if_exists(os.R_OK, 'read', can_read_if_exists)
    __check_permission_if_exists(os.W_OK, 'write', can_modify_if_exists)
    __check_permission_if_exists(os.X_OK, 'execute', can_execute_if_exists)

    if can_create_if_not_exists is not None:
        try:
            if not value.exists():
                if not value.parent.exists():
                    _error(f"Parent {value.parent} doesn't even exist, "
                           + f"so it won't be possible to create {value}")
                if can_create_if_not_exists != (actual := os.access(value.parent, os.W_OK)):
                    _error(f'Invalid write path permissions for parent {value.parent}. '
                           + f'Expected {can_create_if_not_exists}, got {actual}.')
        except PermissionError:
            _error(f'Permission error when trying to check '
                   f'if path {value} exists.' + __verify_parents_permissions())

    if match and not value.match(match):
        _error(f'Invalid path: expected match {match}, got {value}.')

    if full_match:
        if not hasattr(value, 'full_match'):
            _error('Path does not support full_match method. Check your Python version.')
        elif not value.full_match(full_match):
            _error(f'Invalid path: expected full match {full_match}, got {value}.')

    return value
