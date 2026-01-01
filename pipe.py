from typing import TypeVar, Generic, Callable

T = TypeVar('T')
R = TypeVar('R')

class Pipeable(Generic[T, R]):
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
