import asyncio
import functools
from pathlib import Path

try:
    from loggers.logger import logger
except ImportError as ie:
    exit(f'{ie} :: {Path(__file__).resolve()}')


class Utils:
    @staticmethod
    def exception(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f'exception in "{func.__name__}" => {e}')
                return False
        return wrapper

    @staticmethod
    def async_exception(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f'exception in "{func.__name__}" => {e}')
                return False
        return wrapper

    @staticmethod
    def async_retry(retries: int = 5, delay: int = 5):
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                for attempt in range(retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        logger.error(f'exception in "{func.__name__}" => {e}')
                    if attempt < retries - 1:
                        logger.info('retrying')
                        await asyncio.sleep(delay)
                logger.error('max retries exceeded')
                return False
            return wrapper
        return decorator


utils: Utils = Utils()
