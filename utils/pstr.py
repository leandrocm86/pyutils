from collections.abc import Iterable, Generator, Mapping, Sequence
from typing import Any, Final
import sys

ATTY: Final[bool] = sys.stdout.isatty()


def __iter_wrappers(iterable: Iterable[Any]) -> tuple[str, str]:
    if isinstance(iterable, (Mapping, set)):
        return '{', '}'
    elif isinstance(iterable, (tuple, Generator)):
        return '(', ')'
    elif isinstance(iterable, Sequence):
        return '[', ']'
    else:
        raise TypeError(f"Unexpected iterable type: {type(iterable)}")


def __color(depth: int) -> str:
    if depth == 0:
        return '\033[36m'  # CYAN
    elif depth == 1:
        return '\033[33m'  # YELLOW
    else:
        return '\033[35m'  # MAGENTA


__COLOR_END: str = '\033[0m'


def ppstr(obj: object, maxlen: int = 50, maxdepth: int = 3,
          colored: bool = ATTY) -> None:
    """Prints a pretty string representation of an object.
    For details about the parameters, see pstr()."""

    print(pstr(obj, maxlen=maxlen, maxdepth=maxdepth, colored=colored))


def pstr(obj: object, maxlen: int = 50, maxdepth: int = 3,
         colored: bool = ATTY) -> str:
    """Creates a pretty string representation of an object.
    It respects the given constraints (maxlen and maxdepth) to truncate the output when needed.
    Args:
        obj (object):
            The object to be represented.
        maxlen (int, optional):
            The maximum number of (inner) items to be included in the output, for each object. Defaults to 50.
        maxdepth (int, optional):
            The maximum depth of nested objects to be included in the output. Defaults to 3.
        colored (bool, optional):
            Whether to use colors in the output. Defaults to True if stdout is a terminal.
    Returns:
        str: The pretty string representation of the object.
    """

    HALF_INDEX = maxlen // 2

    def primitive_str(val: Any) -> str | None:
        if val is None or isinstance(val, (int, float, bool)):
            return str(val)
        elif isinstance(val, str):
            return val if len(val) < maxlen + 11 \
                else val[:HALF_INDEX] + f'(...len={len(val)})' + val[-HALF_INDEX:]
        return None

    def concat_inners(inners: Sequence[Any], dict_tuples: bool,
                      depth: int, color: str | None) -> list[str]:
        printed_inners: list[str] = []
        for i in inners:
            if (primstr := primitive_str(i)):
                var_istr = primstr
            elif dict_tuples:
                assert isinstance(i, tuple) and len(i) == 2
                var_key = primitive_str(i[0])
                if not var_key:
                    var_key = __COLOR_END + __str(i[0], depth + 1) + color if color else __str(i[0], depth + 1)
                var_value = primitive_str(i[1])
                if not var_value:
                    var_value = __COLOR_END + __str(i[1], depth + 1) + color if color else __str(i[1], depth + 1)
                var_istr = var_key + ': ' + var_value
            else:
                var_istr = __str(i, depth + 1)
                if color:
                    var_istr = __COLOR_END + var_istr + color

            printed_inners.append(var_istr)
        return printed_inners

    def __str(item: Any, depth: int) -> str:
        if (primstr := primitive_str(item)):
            return primstr
        if maxlen and depth < maxdepth:
            if not isinstance(item, Iterable):
                # Non-primitive and non-collection objects may have custom __str__.
                # If so, we use it and format it as a primitive string.
                if (type(item).__str__ is not object.__str__  # type: ignore[comparison-overlap]
                        and (primstr := primitive_str(str(item)))):
                    return primstr
                elif hasattr(item, '__dict__'):
                    var_its = item.__dict__
                else:
                    return str(item)
            else:
                var_its = item

            color = __color(depth) if colored else None
            dict_tuples = isinstance(var_its, Mapping)
            inners: Sequence[Any] = var_its if isinstance(var_its, Sequence) \
                else list(var_its.items() if isinstance(var_its, Mapping) else var_its)
            if len(inners) > maxlen + 1:
                first_half = ', '.join(concat_inners(inners[:HALF_INDEX], dict_tuples, depth, color))
                second_half = ', '.join(concat_inners(inners[-HALF_INDEX:], dict_tuples, depth, color))
                var_items_str = first_half + ', ... , ' + second_half
            else:
                var_items_str = ', '.join(concat_inners(inners, dict_tuples, depth, color))

            start, end = __iter_wrappers(var_its)
            var_items_str = start + var_items_str + end
            if len(inners) > maxlen + 1:
                var_items_str += f'(len={len(inners)})'
            if color:
                return color + var_items_str + __COLOR_END
            else:
                return var_items_str
        else:
            return f"{item.__class__.__name__}(...)"

    return __str(obj, 0)
