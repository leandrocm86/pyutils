from typing import Callable, TypeVar
from contextlib import suppress
import functools


_T = TypeVar("_T")

# Expected to be used as a 'with' statement, to suppress any possible exception.
care = suppress(BaseException)


def maybe(function: Callable[[], _T]) -> _T | None:
    """ Evaluates the given function in a safe manner, supressing any possible exception.\n"""
    """ If no exception occurs, the function's output is returned. Otherwise, None is returned."""
    try:
        return function()
    except Exception:
        return None


def raising(func=None, *, exceptions=(), suppress=False, logfunc=print, trace=True, error_return=None):
    """
    A decorator that captures exceptions thrown by the decorated function.
    It logs the error when it happens, according to logfunc and trace parameters.

    :param exceptions: Tuple of exception classes to capture (will capture any if none specified).
    :param suppress: Suppress the exceptions instead of reraising them, when True.
    :param logfunc: The function for logging errors (use None for not logging).
    :param trace: Include stacktrace in the message, when True.
    :param error_return: The value to return when an exception occurs (if suppress is True).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if not exceptions or any(isinstance(e, ex) for ex in exceptions):
                    # Log the exception and its arguments
                    args_str = ', '.join(map(str, args))
                    if args and kwargs:
                        args_str += ', '
                    args_str += ', '.join(f'{k}={v}' for k, v in kwargs.items())
                    msg = f"Captured exception in function {func.__name__} with arguments ({args_str}): {e}"
                    if trace:
                        from traceback import format_exc
                        msg += '\n' + format_exc()
                    logfunc(msg)
                    if suppress:
                        return error_return
                raise
        return wrapper
    if func is None:
        return decorator
    else:
        return decorator(func)
