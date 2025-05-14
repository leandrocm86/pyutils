from collections.abc import Collection, Iterable, Mapping as Map, Sequence as Seq, Set
from pathlib import Path
from typing import Any, Callable, Optional, Type, TypeVar, Union
from typeguard import CollectionCheckStrategy, check_type
from re import Pattern, compile
from mods.pstr import pstr
import os


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class InvalidContractError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def _error(msg: str):
    raise InvalidContractError(msg)


def _check_collection_type(value: Collection[Any], typ: Type[T]):
    if value and hasattr(value, '__len__') and len(value) > 100:
        strategy = CollectionCheckStrategy.FIRST_ITEM
    else:
        strategy = CollectionCheckStrategy.ALL_ITEMS
    check_type(value, typ, collection_check_strategy=strategy)


def _handle_custom_validation(value: T, custom: Optional[Callable[[T], bool]]):
    if custom:
        try:
            if not custom(value):
                _error(f'Invalid {type(value)}: custom validation failed for {pstr(value)}.')
        except Exception as e:
            _error(f'Error when trying custom validation for {pstr(value)} of type {type(value)}: {e}')


def strok(value: str,
          length: Optional[int] = None,
          minlen: int = 0,
          maxlen: Optional[int] = None,
          upper: bool = False,
          lower: bool = False,
          regex: Union[str, Pattern[str], None] = None,
          domain: Optional[Iterable[str]] = None,
          custom: Optional[Callable[[str], bool]] = None):

    """ Runtime validation for strings.
    Checks type and optionally given constraints, possibly raising
    typeguard.TypeCheckError and InvalidContractError, respectively.
    """

    check_type(value, str)

    if length is not None and len(value) != length:
        _error(f'Invalid str: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid str: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid str: expected maximum length {maxlen}, got {len(value)}.')

    if upper and not value.isupper():
        _error(f'Invalid str: expected upper, got "{next(c for c in value if not c.isupper())}" in {pstr(value, maxlen=50)}.')

    if lower and not value.islower():
        _error(f'Invalid str: expected lower, got "{next(c for c in value if not c.islower())}" in "{pstr(value, maxlen=50)}".')

    if regex:
        if isinstance(regex, str):
            regex = compile(regex)
        if not regex.match(value):
            _error(f'Invalid str: expected regex {regex}, but it didn\'t match with string "{pstr(value, maxlen=50)}".')

    if domain and value not in domain:
        _error(f'Invalid str: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value "{pstr(value, maxlen=50)}".')

    _handle_custom_validation(value, custom)


def intok(value: int,
          min: Optional[int] = None,
          max: Optional[int] = None,
          domain: Optional[Iterable[int]] = None,
          custom: Optional[Callable[[int], bool]] = None):

    check_type(value, int)

    if min is not None and value < min:
        _error(f'Invalid int: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid int: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid int: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    _handle_custom_validation(value, custom)


def floatok(value: float,
            min: Optional[float] = None,
            max: Optional[float] = None,
            domain: Optional[Iterable[float]] = None,
            custom: Optional[Callable[[float], bool]] = None):

    check_type(value, float)

    if min is not None and value < min:
        _error(f'Invalid float: expected minimum {min}, got {value}.')

    if max is not None and value > max:
        _error(f'Invalid float: expected maximum {max}, got {value}.')

    if domain and value not in domain:
        _error(f'Invalid float: expected domain {pstr(domain, maxlen=50)} doesn\'t contain value {value}.')

    _handle_custom_validation(value, custom)


def boolok(value: bool):
    check_type(value, bool)


# Embora Collection sirva tanto para seqs quanto sets, ela nao functiona bem com check_type.
def seqok(value: Seq[T],
          elemtype: Type[T],
          length: Optional[int] = None,
          minlen: int = 0,
          maxlen: Optional[int] = None,
          minelem: Optional[T] = None,
          maxelem: Optional[T] = None,
          custom: Optional[Callable[[Seq[T]], bool]] = None):

    _check_collection_type(value, Seq[elemtype])

    if length is not None and len(value) != length:
        _error(f'Invalid sequence: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid sequence: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid sequence: expected maximum length {maxlen}, got {len(value)}.')

    if minelem and value:
        if not hasattr(minelem, '__lt__'):
            _error(f'Impossible validation: the minimum element\'s type is not comparable: {type(minelem)}.')
        elif not isinstance(minelem, elemtype):
            _error(f'Impossible validation of minimum element: expected minimum element of type {elemtype}, got {type(minelem)}.')
        elif (minv := min(value)) < minelem:  # type: ignore
            _error(f'Invalid sequence: expected minimum element {pstr(minelem)}, got {pstr(minv)}.')  # type: ignore

    if maxelem and value:
        if not hasattr(maxelem, '__lt__'):
            _error(f'Impossible validation: the maximum element\'s type is not comparable: {type(maxelem)}.')
        elif not isinstance(maxelem, elemtype):
            _error(f'Impossible validation of maximum element: expected maximum element of type {elemtype}, got {type(maxelem)}.')
        elif (maxv := max(value)) > maxelem:  # type: ignore
            _error(f'Invalid sequence: expected maximum element {pstr(maxelem)}, got {pstr(maxv)}.')  # type: ignore

    _handle_custom_validation(value, custom)


# Embora Collection sirva tanto para seqs quanto sets, ela nao functiona bem com check_type.
def setok(value: Set[T],
          elemtype: Type[T],
          length: Optional[int] = None,
          minlen: int = 0,
          maxlen: Optional[int] = None,
          minelem: Optional[T] = None,
          maxelem: Optional[T] = None,
          custom: Optional[Callable[[Set[T]], bool]] = None):

    _check_collection_type(value, Set[elemtype])

    if length is not None and len(value) != length:
        _error(f'Invalid set: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid set: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid set: expected maximum length {maxlen}, got {len(value)}.')

    if minelem and value:
        if not hasattr(minelem, '__lt__'):
            _error(f'Impossible validation: the minimum element\'s type is not comparable: {type(minelem)}.')
        elif not isinstance(minelem, elemtype):
            _error(f'Impossible validation of minimum element: expected minimum element of type {elemtype}, got {type(minelem)}.')
        elif (minv := min(value)) < minelem:  # type: ignore
            _error(f'Invalid set: expected minimum element {pstr(minelem)}, got {pstr(minv)}.')  # type: ignore

    if maxelem and value:
        if not hasattr(maxelem, '__lt__'):
            _error(f'Impossible validation: the maximum element\'s type is not comparable: {type(maxelem)}.')
        elif not isinstance(maxelem, elemtype):
            _error(f'Impossible validation of maximum element: expected maximum element of type {elemtype}, got {type(maxelem)}.')
        elif (maxv := max(value)) > maxelem:  # type: ignore
            _error(f'Invalid set: expected maximum element {pstr(maxelem)}, got {pstr(maxv)}.')  # type: ignore

    _handle_custom_validation(value, custom)


def mapok(value: Map[K, V],
          keytype: Type[K],
          valtype: Type[V],
          length: Optional[int] = None,
          minlen: int = 0,
          maxlen: Optional[int] = None,
          minkey: Optional[K] = None,
          maxkey: Optional[K] = None,
          custom: Optional[Callable[[Map[K, V]], bool]] = None):

    _check_collection_type(value, Map[keytype, valtype])

    if length is not None and len(value) != length:
        _error(f'Invalid map: expected length {length}, got {len(value)}.')

    if minlen and len(value) < minlen:
        _error(f'Invalid map: expected minimum length {minlen}, got {len(value)}.')

    if maxlen is not None and len(value) > maxlen:
        _error(f'Invalid map: expected maximum length {maxlen}, got {len(value)}.')

    if minkey and value:
        if not hasattr(minkey, '__lt__'):
            _error(f'Impossible validation: the minimum key\'s type is not comparable: {type(minkey)}.')
        elif not isinstance(minkey, keytype):
            _error(f'Impossible validation of minimum key: expected minimum key of type {keytype}, got {type(minkey)}.')
        elif (minv := min(value)) < minkey:  # type: ignore
            _error(f'Invalid map: expected minimum key {pstr(minkey)}, got {pstr(minv)}.')  # type: ignore

    if maxkey and value:
        if not hasattr(maxkey, '__lt__'):
            _error(f'Impossible validation: the maximum key\'s type is not comparable: {type(maxkey)}.')
        elif not isinstance(maxkey, keytype):
            _error(f'Impossible validation of maximum key: expected maximum key of type {keytype}, got {type(maxkey)}.')
        elif (maxv := max(value)) > maxkey:  # type: ignore
            _error(f'Invalid map: expected maximum key {pstr(maxkey)}, got {pstr(maxv)}.')  # type: ignore

    _handle_custom_validation(value, custom)


def pathok(value: Path,
           exists: Optional[bool] = None,
           is_dir: Optional[bool] = None,
           match: Optional[str] = None,
           full_match: Optional[str] = None,
           can_read_if_exists: Optional[bool] = None,
           can_create_if_not_exists: Optional[bool] = None,
           can_modify_if_exists: Optional[bool] = None,
           can_execute_if_exists: Optional[bool] = None,
           custom: Optional[Callable[[Path], bool]] = None):

    check_type(value, Path)

    def __verify_parents_permissions() -> str:
        unexec_parents: list[Path] = []
        current = value
        while current != current.parent:  # Stop at root directory
            current = current.parent
            if not os.access(current, os.X_OK):   # Check if parent is traversable (has execute permission)
                unexec_parents.append(current)
        if unexec_parents:
            return "\nThe following parent folders seem to miss execute permission (or don't exist): " \
                + ', '.join(str(p) for p in unexec_parents)
        return ''

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

    if is_dir is not None:
        expected = 'directory' if is_dir else 'file'
        try:
            is_actually_dir = value.is_dir()
            is_actually_file = value.is_file()
            if is_actually_dir == is_actually_file:
                _error(f"Impossible to check if path {value} is a {expected}. Maybe it doesn't exist." + __verify_path_exists())
            elif is_actually_dir != is_dir:
                actually = 'directory' if is_actually_dir else 'file'
                _error(f'Invalid path: expected {expected}, got {actually}.')
        except PermissionError:
            _error(f'Permission error when trying to check if path {value} is a {expected}.' + __verify_parents_permissions())

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

    if full_match and not value.full_match(full_match):
        _error(f'Invalid path: expected full match {full_match}, got {value}.')

    _handle_custom_validation(value, custom)


def objok(value: T, expected_type: Type[T], custom: Optional[Callable[[T], bool]] = None):
    check_type(value, expected_type)
    if custom:
        _handle_custom_validation(value, custom)

    # props = {k: v for k, v in vars(value) if not k.startswith('_')}
    # noneprops = {k: v for k, v in props.items() if v is None}
