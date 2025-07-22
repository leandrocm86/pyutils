from typing import Callable, TypeVar, ParamSpec
from contextlib import suppress
import functools
import time


_T = TypeVar("_T")
_E = TypeVar("_E", bound=Exception)
_P = ParamSpec("_P")

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
    """ A decorator that captures exceptions thrown by the decorated function.
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


def retry(max_attempts: int,
          delay: int = 2,
          exceptions: tuple[type[_E], ...] = (Exception,),
          logfunc: Callable[[str], None] | None = print) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """
    Retry decorator that will re-execute a function until none of the given exceptions is raised or the given maximum attempts is reached.

    Parameters:
    - max_attempts: Maximum number of attempts. When reached, the exception from the last try will be reraised.
    - delay: Interval between retries in seconds. Defaults to 2.
    - exceptions: Tuple of exceptions to catch and retry on. Defaults to Exception.
    - logfunc: Function to print messages of each retry attempt. Defaults to print. Use None for no logs.
    """
    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            mtries, mdelay = max_attempts, delay
            while mtries > 0:
                try:
                    if logfunc:
                        logfunc(f'Attempting execution of {func.__name__} ({max_attempts - mtries + 1}/{max_attempts})...')
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        raise e
                    time.sleep(mdelay)
            return func(*args, **kwargs)
        return wrapper
    return decorator
