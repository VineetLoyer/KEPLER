"""Retry utilities with exponential backoff for external service calls

This module provides retry logic for handling transient failures in external
service calls such as LLM APIs, search APIs, and web scraping.
"""
import time
import logging
from typing import Callable, TypeVar, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted"""
    pass


class ExternalServiceError(Exception):
    """Base exception for external service errors"""
    pass


class LLMAPIError(ExternalServiceError):
    """Exception for LLM API failures"""
    pass


class SearchAPIError(ExternalServiceError):
    """Exception for search API failures"""
    pass


class ScrapingError(ExternalServiceError):
    """Exception for web scraping failures"""
    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_exponential_backoff(max_retries=3, initial_delay=1.0)
        def call_external_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful retry if not first attempt
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_retries + 1} attempts. Last error: {str(e)}"
                        ) from e
                    
                    # Log retry attempt
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}, "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    # Wait before retrying
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * exponential_base, max_delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RetryExhaustedError(f"Failed after {max_retries + 1} attempts")
        
        return wrapper
    return decorator


def retry_async_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Async version of retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_retries + 1} attempts. Last error: {str(e)}"
                        ) from e
                    
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}, "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
            
            if last_exception:
                raise last_exception
            raise RetryExhaustedError(f"Failed after {max_retries + 1} attempts")
        
        return wrapper
    return decorator


def is_retryable_error(exception: Exception) -> bool:
    """Determine if an error is retryable
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error is retryable, False otherwise
    """
    # Retryable errors include:
    # - Timeout errors
    # - Connection errors
    # - Rate limit errors (429)
    # - Server errors (5xx)
    # - Temporary service unavailable
    
    error_str = str(exception).lower()
    
    retryable_patterns = [
        'timeout',
        'connection',
        'rate limit',
        '429',
        '500',
        '502',
        '503',
        '504',
        'service unavailable',
        'temporarily unavailable',
        'try again',
    ]
    
    return any(pattern in error_str for pattern in retryable_patterns)
