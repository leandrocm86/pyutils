import timeit
import inspect
import gc
import functools
from itertools import cycle
from typing import overload, TypeVar
from collections.abc import Callable, Sequence
from utils.style import yellow, cyan, green


T = TypeVar('T')
colors = cycle((yellow, cyan, green))


def _strip_function_body(func: Callable[[], None]) -> str:
    code = inspect.getsource(func).strip()
    codelines = code.splitlines()
    assert len(codelines) > 1, 'Functions must have at least 2 lines to extract body code'
    assert codelines[0].startswith('def '), "Function definition doesn't seem suitable to convert to inline code."
    return '\n'.join(_remove_indentation(codelines[1:]))


def _remove_indentation(lines: Sequence[str]) -> list[str]:
    var_indentation = ''
    for char in lines[0]:
        if char.isspace():
            var_indentation += char
        else:
            break
    return [line.removeprefix(var_indentation) for line in lines]


def benchmark_inline(function: Callable[[], None],
                     loops: int = 1,
                     setup: Callable[[], None] | None = None,
                     enable_gc: bool = False,
                     logfunction: Callable[[str], None] = print) -> float:
    """
    Measures the time spent executing the code from the given function's body as if it was inline code.
    That ensures there's no overhead time from function calls to interfere on the measurements.
    Parameters:
        function: the function to benchmark. Its signature (first line) is ignored, and it can't have a return statement.
        loops: how many times to repeatedly execute the function's body.
        setup: function from which body to run once before executing the benchmark.
        enable_gc: if True, garbage collection won't be turned off, and it will affect measurements.
        logfunction: The function to receive outputs as strings (print by default).
    Returns: the total time spent executing the function's body.
    """
    var_setup_str = _strip_function_body(setup) + ';' if setup else ''
    var_setup_str += 'gc.enable()' if enable_gc else ''
    assert hasattr(function, "__name__") and (function_name := function.__name__), 'The given function must have a name'
    time = timeit.timeit(stmt=_strip_function_body(function), setup=var_setup_str, number=loops)
    if logfunction is not None:
        logfunction(f'{function_name}: {time}s')
    return time


def benchmark[T](function: Callable[[], T],
                 loops: int = 1,
                 setup: Callable[[], None] | None = None,
                 enable_gc: bool = False,
                 logfunction: Callable[[str], None] = print) -> tuple[float, list[T]]:
    """
    Measures the time spent executing the given function.
    If the overhead of function calls shouldn't be measured, consider using `benchmark_inline`.
    Parameters:
        function: the function to benchmark.
        loops: how many times to repeatedly execute the function.
        setup: function to run once before executing the benchmark.
        enable_gc: if True, garbage collection won't be turned off, and it will affect measurements.
        logfunction: The function to receive outputs as strings (print by default).
    Returns: a tuple with the time spent and a list of the outputs of the function executions.
    """

    if setup:
        setup()
    if not enable_gc:
        gc.disable()
    assert hasattr(function, "__name__") and (function_name := function.__name__), 'The given function must have a name'
    var_time = 0.0
    outputs: list[T] = []
    for _ in range(loops):
        start_time = timeit.default_timer()
        output = function()
        var_time += timeit.default_timer() - start_time
        outputs.append(output)
    if logfunction is not None:
        logfunction(f'{function_name}: {var_time}s')
    if not enable_gc:
        gc.enable()  # reativando gc
    return var_time, outputs


def compare_inline[T](functions: Sequence[Callable[[], None]],
                      loops: int = 1,
                      setup: Callable[[], None] | None = None,
                      enable_gc: bool = False,
                      logfunction: Callable[[str], None] = print) -> list[float]:
    """
    Measures the time spent executing the code from the given functions' bodies as they were inline code.
    That ensures there's no overhead time from function calls to interfere on the measurements.
    Parameters:
        functions: the functions to benchmark. Their signatures (first line) are ignored,
        and they can't have return statements.
        loops: how many times to repeatedly execute each function body.
        setup: function from which body to run once before executing each function's benchmark.
        enable_gc: if True, garbage collection won't be turned off, and it will affect measurements.
        logfunction: The function to receive outputs as strings (print by default).
    Returns: a list with the times spent in each function.
    """

    times: list[float] = []
    for function in functions:
        times.append(benchmark_inline(function, loops, setup, enable_gc, logfunction))
    return times


def compare[T](functions: Sequence[Callable[[], T]],
               loops: int = 1,
               setup: Callable[[], None] | None = None,
               enable_gc: bool = False,
               logfunction: Callable[[str], None] = print,
               validate_outputs: bool = True) -> tuple[list[float], list[list[T]]]:
    """
    Measures the time spent executing the given functions,
    and asserts their outputs are equal (unless validate_outputs is False).
    If the overhead of function calls shouldn't be measured, consider using `compare_inline`.
    Parameters:
        functions: the functions to benchmark.
        loops: how many times to repeatedly execute each function.
        setup: function to run once before executing each function's benchmark.
        enable_gc: if True, garbage collection won't be turned off, and it will affect measurements.
        logfunction: The function to receive outputs as strings (print by default).
    Returns: a tuple with a list of times spent and a list of outputs of each function.
    """

    def outputs_to_str(outputs: list[T]) -> str:
        color = next(colors)
        if outputs and all(out == outputs[0] for out in outputs):
            return color(str(outputs[0]))
        if not outputs or len(outputs) <= 6:
            return color(str(outputs))
        return f'{color(str(outputs[:3]))}, (...), {color(str(outputs[-3:]))}'

    times: list[float] = []
    all_outputs: list[list[T]] = []
    for function in functions:
        time, outputs = benchmark(function, loops, setup, enable_gc, logfunction)
        if validate_outputs and all_outputs:
            assert all_outputs[0] == outputs, 'Different outputs between functions: ' \
                + f'{outputs_to_str(all_outputs[0])} != {outputs_to_str(outputs)}'
        times.append(time)
        all_outputs.append(outputs)
    return times, all_outputs


@overload
def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def timed[**P, R](func: None = None, *, logfunc: Callable[[str], None] = print) \
            -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def timed[**P, R](func: Callable[P, R] | None = None, *, logfunc: Callable[[str], None] = print) \
        -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator that measures the time spent executing a function.
    It logs the time when the function finishes, according to logfunc parameter.

    Can be used with or without parentheses.

    :param func: The function to be decorated (None if used with parentheses).
    :param logfunc: The function for logging the time spent (print by default).
    """
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = timeit.default_timer()
            try:
                return f(*args, **kwargs)
            finally:
                elapsed = timeit.default_timer() - start_time
                logfunc(f"Function {f.__name__ if hasattr(f, '__name__') else '?'} executed in {elapsed:.2f} secs.")
        return wrapper

    return decorator if func is None else decorator(func)
