from typing import Any, Optional, Mapping, Sequence, Iterable, Set, Generator
import sys


def __iter_wrappers(iterable: Iterable[Any]) -> tuple[str, str]:
    if isinstance(iterable, (Mapping, Set)):
        return '{', '}'
    elif isinstance(iterable, (tuple, Generator)):
        return '(', ')'
    elif isinstance(iterable, Sequence):
        return '[', ']'
    else:
        raise Exception(f"Unexpected iterable type: {type(iterable)}")


def __color(depth: int) -> str:
    if depth == 0:
        return '\033[36m'  # CYAN
    elif depth == 1:
        return '\033[33m'  # YELLOW
    else:
        return '\033[35m'  # MAGENTA


__COLOR_END: str = '\033[0m'


def ppstr(obj: object, maxlen: int = 50, maxdepth: int = 3,
          colored: bool = sys.stdout.isatty()) -> None:
    """Prints a pretty string representation of an object.
    For details about the parameters, see pstr()."""

    print(pstr(obj, maxlen=maxlen, maxdepth=maxdepth, colored=colored))


def pstr(obj: object, maxlen: int = 50, maxdepth: int = 3,
         colored: bool = sys.stdout.isatty()) -> str:
    """Creates a pretty string representation of an object.
    It respects the given constraints (maxlen and maxdepth) to truncate the output when needed.
    Args:
        obj (object): The object to be represented.
        maxlen (int, optional): The maximum number of (inner) items to be included in the output, for each object. Defaults to 50.
        maxdepth (int, optional): The maximum depth of nested objects to be included in the output. Defaults to 3.
        colored (bool, optional): Whether to use colors in the output. Defaults to True if stdout is a terminal.
    Returns:
        str: The pretty string representation of the object.
    """

    HALF_INDEX = maxlen // 2

    def primitive_str(val: Any) -> Optional[Any]:
        if val is None or isinstance(val, (int, float, bool)):
            return str(val)
        elif isinstance(val, str):
            return val if len(val) < maxlen + 11 \
                else val[:HALF_INDEX] + f'(...len={len(val)})' + val[-HALF_INDEX:]
        return None

    def concat_inners(inners: Sequence[Any], dict_tuples: bool,
                      depth: int, color: Optional[str]) -> list[str]:
        printed_inners: list[str] = []
        for i in inners:
            if (primstr := primitive_str(i)):
                istr = primstr
            elif dict_tuples:
                assert isinstance(i, tuple) and len(i) == 2  # type: ignore
                key = primitive_str(i[0])
                if not key:
                    key = __COLOR_END + __str(i[0], depth + 1) + color if color else __str(i[0], depth + 1)
                value = primitive_str(i[1])
                if not value:
                    value = __COLOR_END + __str(i[1], depth + 1) + color if color else __str(i[1], depth + 1)
                istr = key + ': ' + value
            else:
                istr = __str(i, depth + 1)
                if color:
                    istr = __COLOR_END + istr + color

            printed_inners.append(istr)
        return printed_inners

    def __str(item: Any, depth: int) -> str:
        if (primstr := primitive_str(item)):
            return primstr
        if maxlen and depth < maxdepth:
            if not isinstance(item, Iterable):
                if hasattr(item, '__dict__'):
                    its = item.__dict__
                else:
                    return str(item)
            else:
                its = item  # type: ignore

            color = __color(depth) if colored else None
            dict_tuples = isinstance(its, Mapping)
            inners: Sequence[Any] = its if isinstance(its, Sequence) \
                else list(its.items() if isinstance(its, Mapping) else its)  # type: ignore
            if len(inners) > maxlen + 1:
                first_half = ', '.join(concat_inners(inners[:HALF_INDEX], dict_tuples, depth, color))
                second_half = ', '.join(concat_inners(inners[-HALF_INDEX:], dict_tuples, depth, color))
                items_str = first_half + ', ... , ' + second_half
            else:
                items_str = ', '.join(concat_inners(inners, dict_tuples, depth, color))

            start, end = __iter_wrappers(its)  # type: ignore
            items_str = start + items_str + end
            if len(inners) > maxlen + 1:
                items_str += f'(len={len(inners)})'
            if color:
                return color + items_str + __COLOR_END
            else:
                return items_str
        else:
            return f"{item.__class__.__name__}(...)"

    return __str(obj, 0)
