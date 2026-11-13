from collections.abc import Callable
from contextlib import suppress
import functools
import time


# Expected to be used as a 'with' statement, to suppress any possible exception.
care = suppress(BaseException)


def maybe[T](function: Callable[[], T]) -> T | None:
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
                return func(*args, **kwargs)
            except Exception as e:
                if not exceptions or any(isinstance(e, ex) for ex in exceptions):
                    # Log the exception and its arguments
                    var_args_str = ', '.join(map(str, args))
                    if args and kwargs:
                        var_args_str += ', '
                    var_args_str += ', '.join(f'{k}={v}' for k, v in kwargs.items())
                    var_msg = f"Captured exception in function {func.__name__} with arguments ({var_args_str}): {e}"
                    if trace:
                        from traceback import format_exc
                        var_msg += '\n' + format_exc()
                    logfunc(var_msg)
                    if suppress:
                        return error_return
                raise
        return wrapper
    if func is None:
        return decorator
    else:
        return decorator(func)


def retry[**P, T](max_attempts: int,
                  delay: int = 2,
                  exceptions: tuple[type[BaseException], ...] = (BaseException,),
                  logfunc: Callable[[str], None] | None = print) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Retry decorator that will re-execute a function until none
    of the given exceptions is raised or the given maximum attempts is reached.

    Parameters:
    - max_attempts: Maximum number of attempts. When reached, the exception from the last try will be reraised.
    - delay: Interval between retries in seconds. Defaults to 2.
    - exceptions: Tuple of exceptions to catch and retry on. Defaults to Exception.
    - logfunc: Function to print messages of each retry attempt. Defaults to print. Use None for no logs.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            var_mtries, mdelay = max_attempts, delay
            while var_mtries > 0:
                try:
                    if logfunc:
                        funcname = func.__name__ if hasattr(func, '__name__') else 'anonymous function'
                        logfunc(f'Attempting execution of f{funcname}'
                                + f' ({max_attempts - var_mtries + 1}/{max_attempts})...')
                    return func(*args, **kwargs)
                except exceptions:
                    var_mtries -= 1
                    if var_mtries == 0:
                        raise
                    time.sleep(mdelay)
            return func(*args, **kwargs)
        return wrapper
    return decorator
