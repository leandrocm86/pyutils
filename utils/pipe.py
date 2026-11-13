from collections.abc import Callable


class Pipeable[T, R]:
    def __init__(self, func: Callable[[T], R]):
        self.func = func

    def __ror__(self, other: T) -> R:
        return self.func(other)

    def __call__(self, arg: T) -> R:
        return self.func(arg)


if __name__ == "__main__":
    # Usage with type hints
    @Pipeable
    def add_one(x: int) -> int:
        return x + 1

    @Pipeable
    def to_string(x: int) -> str:
        return str(x)

    # This works and type checkers understand it
    result = 5 | add_one | to_string  # Type: str ✓
    print(result)

    # This would be caught by mypy/pyright
    # result: str = "hello" | add_one  # Type error! ✓


@Pipeable
def str_(x):
    return str(x)


@Pipeable
def int_(x):
    return int(x)


@Pipeable
def float_(x):
    return float(x)


@Pipeable
def bool_(x):
    return bool(x)


@Pipeable
def set_(x):
    return set(x)


@Pipeable
def tuple_(x):
    return tuple(x)


@Pipeable
def len_(x):
    return len(x)


@Pipeable
def strip_(x: str):
    return x.strip()


@Pipeable
def upper_(x: str):
    return x.upper()


@Pipeable
def lower_(x: str):
    return x.lower()
