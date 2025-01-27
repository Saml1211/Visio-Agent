"""Retry functionality for handling transient failures"""

import functools
import asyncio
import logging
import time
from typing import Type, Optional, Callable, Any, Union, Tuple

from ..services.exceptions import (
    ChatbotError, ServiceError, RateLimitError,
    APIError, AuthenticationError
)

logger = logging.getLogger(__name__)

def with_retry(retries: int = 3, delay: float = 1.0):
    """Basic retry decorator
    
    Args:
        retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < retries - 1:
                        logger.warning(
                            f"Operation failed, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{retries}): {str(e)}"
                        )
                        await asyncio.sleep(delay)
            
            raise last_error or ChatbotError("Operation failed after retries")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < retries - 1:
                        logger.warning(
                            f"Operation failed, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{retries}): {str(e)}"
                        )
                        time.sleep(delay)
            
            raise last_error or ChatbotError("Operation failed after retries")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def retry_async(
    func: Optional[Callable] = None,
    *,
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (ServiceError, APIError),
    exclude: Optional[tuple] = (AuthenticationError,)
) -> Callable:
    """Async-specific retry decorator with optional parameters
    
    Can be used as @retry_async or @retry_async(retries=5, delay=2.0)
    """
    if func is None:
        return lambda f: with_retry(retries=retries, delay=delay)(f)
    return with_retry()(func)

def retry_sync(
    func: Optional[Callable] = None,
    *,
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (ServiceError, APIError),
    exclude: Optional[tuple] = (AuthenticationError,)
) -> Callable:
    """Sync-specific retry decorator with optional parameters
    
    Can be used as @retry_sync or @retry_sync(retries=5, delay=2.0)
    """
    if func is None:
        return lambda f: with_retry(retries=retries, delay=delay)(f)
    return with_retry()(func) 