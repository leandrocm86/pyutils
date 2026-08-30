from collections.abc import Collection, Iterable, Mapping as Map, Sequence as Seq, Set
from pathlib import Path
from typing import get_origin, get_args, Any, Callable, Optional, Type, TypeVar, Union, Tuple
import typing
from re import Pattern, compile
from utils.pstr import pstr
import os
import sys
import functools

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
C = TypeVar('C', bound=Collection[Any])


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


def check_type(value: Any, expected_type: Any, max_checks: int = 100) -> None:
    """
    Validate that a value matches the expected type at runtime.

    Supports both regular types and generic type annotations.
    For collections, checks only up to the first 100 elements.

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
        return

    # Handle Union types (including Optional and | syntax)
    origin = get_origin(expected_type)
    if _is_union_type(expected_type, origin):
        var_args = get_args(expected_type)
        for arg in var_args:
            try:
                check_type(value, arg)
                return  # If any type matches, we're good
            except TypeError:
                continue
        # If none matched, raise error
        type_names = [_get_type_name(arg) for arg in var_args]
        raise TypeError(f"Expected one of {type_names}, got {type(value).__name__}")

    # Handle Literal types first (before checking origin)
    if _is_literal_type(expected_type):
        var_args = get_args(expected_type)
        if value not in var_args:
            raise TypeError(f"Expected one of {var_args}, got {repr(value)}")
        return

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
        if not isinstance(value, expected_type):
            raise TypeError(f"Expected {_get_type_name(expected_type)}, got {type(value).__name__}")


def _is_literal_type(type_obj: Any) -> bool:
    """Check if a type is a Literal type."""
    try:
        from typing import Literal
        # Check if it's a Literal type
        origin = get_origin(type_obj)
        return origin is Literal
    except ImportError:
        # Literal not available in older Python versions
        return False


def _is_union_type(type_obj: Any, origin: Any) -> bool:
    """Check if a type is a Union type (including | syntax)."""
    if origin is Union:
        return True
    if sys.version_info >= (3, 10):  # Handle Python 3.10+ | syntax
        import types  # In Python 3.10+, A | B creates a types.UnionType
        if isinstance(type_obj, types.UnionType):
            return True
    return False


def __check_generic_args(value: Any, origin: type, args: tuple[Any, ...], max_checks: int) -> None:
    """Check generic type arguments for collections."""

    if origin in (list, set, frozenset, Seq, Set):
        # For homogeneous collections, check element type
        if len(args) == 1:
            var_element_type = args[0]
            var_items = list(value)[:max_checks] if hasattr(value, '__iter__') else []
            for i, item in enumerate(var_items):
                try:
                    check_type(item, var_element_type, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Element at index {i}: {e}")

    elif origin in (tuple, Tuple):
        # Handle tuple types specially
        if len(args) == 2 and args[1] is ...:
            # tuple[int, ...] - homogeneous tuple of any length
            var_element_type = args[0]
            # Check up to max_checks elements
            var_items = list(value)[:max_checks]
            for i, item in enumerate(var_items):
                try:
                    check_type(item, var_element_type, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Element at index {i}: {e}")
        else:
            # tuple[int, str, bool] - fixed-length tuple with specific types
            if len(value) != len(args):
                raise TypeError(f"Expected tuple of length {len(args)}, got length {len(value)}")
            for i, (item, expected_type) in enumerate(zip(value, args)):
                try:
                    check_type(item, expected_type, max_checks=max_checks)
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
                    check_type(key, keytype, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Dictionary key {repr(key)}: {e}")

        if valtype:
            for key, val in var_items:
                try:
                    check_type(val, valtype, max_checks=max_checks)
                except TypeError as e:
                    raise TypeError(f"Dictionary value for key {repr(key)}: {e}")

    elif hasattr(typing, 'Literal') and origin is typing.Literal:
        # Handle Literal types (Python 3.8+)
        if value not in args:
            raise TypeError(f"Expected one of {args}, got {repr(value)}")

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


def __handle_custom_validation(value: T, custom: Optional[Callable[[T], bool]]):
    if custom:
        try:
            if not custom(value):
                _error(f'Invalid {type(value)}: custom validation failed for {pstr(value)}.')
        except Exception as e:
            _error(f'Error when trying custom validation for {pstr(value)} of type {type(value)}: {e}')


@hide_internal_frames()
def valstr(value: str,
           length: Optional[int] = None,
           minlen: int = 0,
           maxlen: Optional[int] = None,
           upper: bool = False,
           lower: bool = False,
           regex: Union[str, Pattern[str], None] = None,
           domain: Optional[Iterable[str]] = None,
           custom: Optional[Callable[[str], bool]] = None) -> str:
    """ Runtime validation for strings.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, str)

    if length is not None and len(value) != length:
        _error(f'Invalid str: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid str: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid str: expected maximum length {maxlen}, got {len(value)}.')

    if upper and not value.isupper():
        offending = next((c for c in value if not c.isupper()), None)
        if offending is not None:
            _error(f'Invalid str: expected upper, got "{offending}" in {pstr(value, maxlen=50)}.')
        else:
            # This case should ideally not be reached if value.isupper() is False, but included for safety.
            _error(f'Invalid str: expected upper, but no non-uppercase character found in {pstr(value, maxlen=50)}.')

    if lower and not value.islower():
        offending = next((c for c in value if not c.islower()), None)
        if offending is not None:
            _error(f'Invalid str: expected lower, got "{offending}" in "{pstr(value, maxlen=50)}".')
        else:
            # This case should ideally not be reached if value.islower() is False, but included for safety.
            _error(f'Invalid str: expected lower, but no non-lowercase character found in "{pstr(value, maxlen=50)}".')

    if regex:
        if isinstance(regex, str):
            regex = compile(regex)
        if not regex.match(value):
            _error(f'Invalid str: expected regex "{regex.pattern}", but it didn\'t match with string "{pstr(value, maxlen=50)}".')

    if domain and value not in domain:
        _error(f'Invalid str: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value "{pstr(value, maxlen=50)}".')

    __handle_custom_validation(value, custom)

    return value


@hide_internal_frames()
def valint(value: int,
           min: Optional[int] = None,
           max: Optional[int] = None,
           domain: Optional[Iterable[int]] = None,
           custom: Optional[Callable[[int], bool]] = None) -> int:
    """ Runtime validation for integers.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, int)

    if min is not None and value < min:
        _error(f'Invalid int: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid int: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid int: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    __handle_custom_validation(value, custom)

    return value


@hide_internal_frames()
def valfloat(value: float,
             min: Optional[float] = None,
             max: Optional[float] = None,
             domain: Optional[Iterable[float]] = None,
             custom: Optional[Callable[[float], bool]] = None) -> float:
    """ Runtime validation for floats.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, float)

    if min is not None and value < min:
        _error(f'Invalid float: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid float: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid float: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    __handle_custom_validation(value, custom)

    return value


@hide_internal_frames()
def valbool(value: bool) -> bool:
    check_type(value, bool)
    return value


def __collectionok(value: C,
                   length: Optional[int] = None,
                   minlen: int = 0,
                   maxlen: Optional[int] = None,
                   minelem: Optional[T] = None,
                   maxelem: Optional[T] = None,
                   custom: Optional[Callable[[C], bool]] = None):

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
                _error(f'Impossible validation of minimum element: expected minimum element of type {type(minelem)}, got {type(minv)}.')
            elif minv < minelem:  # type: ignore
                _error(f'Invalid sequence: expected minimum element {pstr(minelem)}, got {pstr(minv)}.')  # type: ignore

    if maxelem is not None and value:
        if maxelem is not None and value:
            if not hasattr(maxelem, '__lt__'):
                _error(f'Impossible validation: the maximum element\'s type is not comparable: {type(maxelem)}.')
            else:
                maxv = max(value)
                if not isinstance(maxv, type(maxelem)):
                    _error(f'Impossible validation of maximum element: expected maximum element of type {type(maxelem)}, got {type(maxv)}.')
                elif maxv > maxelem:  # type: ignore
                    _error(f'Invalid sequence: expected maximum element {pstr(maxelem)}, got {pstr(maxv)}.')  # type: ignore

    __handle_custom_validation(value, custom)


@hide_internal_frames()
def valseq(value: Seq[T],
           elemtype: Type[T],
           length: Optional[int] = None,
           minlen: int = 0,
           maxlen: Optional[int] = None,
           minelem: Optional[T] = None,
           maxelem: Optional[T] = None,
           custom: Optional[Callable[[Seq[T]], bool]] = None,
           max_checks: int = 100) -> Seq[T]:  # Added max_checks here
    """ Runtime validation for sequences (lists and tuples).
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, Seq[elemtype], max_checks=max_checks)

    __collectionok(value, length, minlen, maxlen, minelem, maxelem, custom)

    return value


@hide_internal_frames()
def valset(value: Set[T],
           elemtype: Type[T],
           length: Optional[int] = None,
           minlen: int = 0,
           maxlen: Optional[int] = None,
           minelem: Optional[T] = None,
           maxelem: Optional[T] = None,
           custom: Optional[Callable[[Set[T]], bool]] = None,
           max_checks: int = 100) -> Set[T]:
    """ Runtime validation for sets.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, Set[elemtype], max_checks=max_checks)

    __collectionok(value, length, minlen, maxlen, minelem, maxelem, custom)

    return value


@hide_internal_frames()
def valmap(value: Map[K, V],
           keytype: Type[K],
           valtype: Type[V],
           length: Optional[int] = None,
           minlen: int = 0,
           maxlen: Optional[int] = None,
           minkey: Optional[K] = None,
           maxkey: Optional[K] = None,
           custom: Optional[Callable[[Map[K, V]], bool]] = None,
           max_checks: int = 100) -> Map[K, V]:  # Added max_checks here
    """ Runtime validation for maps (dictionaries).
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, Map[keytype, valtype], max_checks=max_checks)

    if length is not None and len(value) != length:
        _error(f'Invalid map: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid map: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid map: expected maximum length {maxlen}, got {len(value)}.')

    if minkey is not None and value:
        if not hasattr(minkey, '__lt__'):
            _error(f'Impossible validation: the minimum key\'s type is not comparable: {type(minkey)}.')
        elif not isinstance(minkey, keytype):
            _error(f'Impossible validation of minimum key: expected minimum key of type {keytype}, got {type(minkey)}.')
        elif (minv := min(value)) < minkey:  # type: ignore
            _error(f'Invalid map: expected minimum key {pstr(minkey)}, got {pstr(minv)}.')  # type: ignore

    if maxkey is not None and value:
        if not hasattr(maxkey, '__lt__'):
            _error(f'Impossible validation: the maximum key\'s type is not comparable: {type(maxkey)}.')
        elif not isinstance(maxkey, keytype):
            _error(f'Impossible validation of maximum key: expected minimum key of type {keytype}, got {type(maxkey)}.')
        elif (maxv := max(value)) > maxkey:  # type: ignore
            _error(f'Invalid map: expected maximum key {pstr(maxkey)}, got {pstr(maxv)}.')  # type: ignore

    __handle_custom_validation(value, custom)

    return value


@hide_internal_frames()
def valpath(value: Path,
            exists: Optional[bool] = None,
            is_dir_if_exists: Optional[bool] = None,
            match: Optional[str] = None,
            full_match: Optional[str] = None,
            can_read_if_exists: Optional[bool] = None,
            can_create_if_not_exists: Optional[bool] = None,
            can_modify_if_exists: Optional[bool] = None,
            can_execute_if_exists: Optional[bool] = None,
            custom: Optional[Callable[[Path], bool]] = None) -> Path:
    """ Runtime validation for paths.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, Path)

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
            return f"PermissionError when trying to check if path {value} exists. Maybe it misses read permission, or its parents aren't traversable (miss execute permission)."

    # def __verify_readable_path() -> str:
    #     if not os.access(value, os.R_OK):
    #         return f"\nPath {value} is not readable. Maybe it doesn't exist, miss read permission, or its parents aren't traversable (miss execute permission)."
    #     return ''

    def __check_permission_if_exists(permission_code: int, permission_desc: str, expected: Optional[bool]):
        if expected is not None:
            try:
                if value.exists():
                    if expected != (actual := os.access(value, permission_code)):
                        _error(f'Invalid {permission_desc} path permissions for {value}. Expected {expected}, got {actual}.')
            except PermissionError:
                _error(f'Permission error when trying to check existence of path {value}.' + __verify_parents_permissions())

    if is_dir_if_exists is not None:
        expected = 'directory' if is_dir_if_exists else 'file'
        try:
            if value.exists():
                try:
                    is_actually_dir = value.is_dir()
                    is_actually_file = value.is_file()
                    if is_actually_dir == is_actually_file:
                        _error(f"Impossible to check if path {value} is a {expected}. Maybe it doesn't exist." + __verify_path_exists())
                    elif is_actually_dir != is_dir_if_exists:
                        actually = 'directory' if is_actually_dir else 'file'
                        _error(f'Invalid path: expected {expected}, got {actually}.')
                except PermissionError:
                    _error(f'Permission error when trying to check if path {value} is a {expected}.' + __verify_parents_permissions())
        except PermissionError:
            _error(f'Permission error when trying to check existence of path {value}.' + __verify_parents_permissions())

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
                    _error(f"Parent {value.parent} doesn't even exist, so it won't be possible to create {value}")
                if can_create_if_not_exists != (actual := os.access(value.parent, os.W_OK)):
                    _error(f'Invalid write path permissions for parent {value.parent}. Expected {can_create_if_not_exists}, got {actual}.')
        except PermissionError:
            _error(f'Permission error when trying to check if path {value} exists.' + __verify_parents_permissions())

    if match and not value.match(match):
        _error(f'Invalid path: expected match {match}, got {value}.')

    if full_match:
        if not hasattr(value, 'full_match'):
            _error('Path does not support full_match method. Check your Python version.')
        elif value.full_match(full_match):  # type: ignore
            _error(f'Invalid path: expected full match {full_match}, got {value}.')

    __handle_custom_validation(value, custom)

    return value


@hide_internal_frames()
def valobj(value: T, expected_type: Type[T], custom: Optional[Callable[[T], bool]] = None) -> T:
    """ Generic runtime validation for objects.
    Checks type and optionally given constraints, possibly raising
    TypeError or InvalidContractError, respectively. If no error is raised, the original value is returned.
    """

    check_type(value, expected_type)
    if custom:
        __handle_custom_validation(value, custom)
    return value

    # props = {k: v for k, v in vars(value) if not k.startswith('_')}
    # noneprops = {k: v for k, v in props.items() if v is None}
