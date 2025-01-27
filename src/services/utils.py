import functools
import asyncio
import logging
from typing import Type, Optional, Callable, Any
import time

from .exceptions import (
    ChatbotError, ServiceError, RateLimitError,
    APIError, AuthenticationError
)

logger = logging.getLogger(__name__)

def with_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (ServiceError, APIError),
    exclude: Optional[tuple] = (AuthenticationError,)
):
    """Retry decorator for handling transient failures
    
    Args:
        retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        exclude: Tuple of exceptions to exclude from retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except RateLimitError as e:
                    # Handle rate limits with their specific retry_after
                    if attempt < retries:
                        retry_after = e.retry_after or current_delay
                        logger.warning(
                            f"Rate limit hit, retrying in {retry_after}s "
                            f"(attempt {attempt + 1}/{retries})"
                        )
                        await asyncio.sleep(retry_after)
                    last_exception = e
                    
                except exclude as e:
                    # Don't retry excluded exceptions
                    raise
                    
                except exceptions as e:
                    if attempt < retries:
                        logger.warning(
                            f"Operation failed, retrying in {current_delay}s "
                            f"(attempt {attempt + 1}/{retries}): {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    last_exception = e
                    
                except Exception as e:
                    # Don't retry unexpected exceptions
                    raise
            
            # If we get here, we've exhausted our retries
            raise last_exception or ChatbotError("Operation failed after retries")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except RateLimitError as e:
                    if attempt < retries:
                        retry_after = e.retry_after or current_delay
                        logger.warning(
                            f"Rate limit hit, retrying in {retry_after}s "
                            f"(attempt {attempt + 1}/{retries})"
                        )
                        time.sleep(retry_after)
                    last_exception = e
                    
                except exclude as e:
                    raise
                    
                except exceptions as e:
                    if attempt < retries:
                        logger.warning(
                            f"Operation failed, retrying in {current_delay}s "
                            f"(attempt {attempt + 1}/{retries}): {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    last_exception = e
                    
                except Exception as e:
                    raise
            
            raise last_exception or ChatbotError("Operation failed after retries")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 