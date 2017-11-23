import warnings
from asyncio.coroutines import iscoroutine, coroutine
from asyncio.tasks import sleep
from functools import wraps


def deprecated(func):
    """
    Generates a deprecation warning
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        msg = "'{}' is deprecated".format(func.__name__)
        warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return wrapper


def retry(exceptions, tries=5, delay=1, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """

    def deco_retry(func):
        @wraps(func)
        async def f_retry(self, *args, **kwargs):
            if not iscoroutine(func):
                f = coroutine(func)
            else:
                f = func

            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return await f(self, *args, **kwargs)
                except exceptions:
                    if logger:
                        logger.info('Retrying %s after %s seconds', f.__name__, mdelay)
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return await f(self, *args, **kwargs)

        return f_retry

    return deco_retry
