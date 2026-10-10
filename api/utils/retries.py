"""
Retry Logic for API Calls

Implements exponential backoff retry strategy for network failures, timeouts, and rate limiting.
Supports yfinance and Schwab API calls with intelligent error classification.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Error categories for intelligent retry handling
TIMEOUT_ERRORS = (asyncio.TimeoutError, TimeoutError)
NETWORK_ERRORS = (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError)
RETRYABLE_HTTP_CODES = {429, 503, 502, 504}  # Rate limit, Service Unavailable, Bad Gateway, Gateway Timeout
PERMANENT_HTTP_CODES = {401, 403, 404}  # Unauthorized, Forbidden, Not Found


class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        timeout: float = 30.0,
        jitter: bool = True,
    ):
        """
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
            initial_delay: Initial delay in seconds (default: 1.0)
            timeout: Timeout per attempt in seconds (default: 30.0)
            jitter: Whether to add jitter to backoff delays (default: True)
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.timeout = timeout
        self.jitter = jitter

    def get_backoff_delay(self, attempt: int) -> float:
        """Calculate backoff delay for a given attempt number."""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        if self.jitter:
            import random
            delay *= (0.5 + random.random())  # Add 50-100% jitter
        return delay


async def with_retry(
    func: Callable[[], T],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    timeout: float = 30.0,
    operation_name: Optional[str] = None,
) -> T:
    """
    Execute an async function with exponential backoff retry logic.

    Handles:
    - Timeouts: Retries up to max_retries times
    - Network errors: Retries with exponential backoff
    - Rate limiting (429): Retries with exponential backoff
    - Server errors (502, 503, 504): Retries with exponential backoff
    - Permanent errors (401, 403, 404): Raises immediately without retry

    Args:
        func: Async function to execute
        max_retries: Maximum number of retries (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 2.0)
        initial_delay: Initial retry delay in seconds (default: 1.0)
        timeout: Timeout per attempt in seconds (default: 30.0)
        operation_name: Name of operation for logging (default: func.__name__)

    Returns:
        Result of the function call

    Raises:
        The exception from the final failed attempt if all retries exhausted
    """
    config = RetryConfig(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        timeout=timeout,
        jitter=True,
    )

    op_name = operation_name or getattr(func, '__name__', 'unknown_operation')
    attempt = 0
    last_exception = None
    attempt_history = []

    while attempt <= config.max_retries:
        try:
            # Execute function with timeout
            try:
                result = await asyncio.wait_for(func(), timeout=config.timeout)
                if attempt > 0:
                    logger.info(
                        f"[RETRY] Success on attempt {attempt + 1}/{config.max_retries + 1} "
                        f"for {op_name}"
                    )
                return result
            except asyncio.TimeoutError as e:
                last_exception = e
                error_type = "TimeoutError"
                should_retry = True
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__

            # Check for HTTP errors with status codes
            if hasattr(e, 'status_code'):
                status_code = e.status_code
                if status_code in PERMANENT_HTTP_CODES:
                    logger.error(
                        f"[RETRY] Permanent error {status_code} for {op_name}: {str(e)[:100]}"
                    )
                    raise
                should_retry = status_code in RETRYABLE_HTTP_CODES
            else:
                # Classify error as retryable or not
                should_retry = isinstance(e, (TIMEOUT_ERRORS, NETWORK_ERRORS))

        # If not retryable, raise immediately
        if not should_retry or attempt >= config.max_retries:
            if attempt >= config.max_retries:
                attempt_history_str = "; ".join(attempt_history) if attempt_history else "no attempts"
                logger.error(
                    f"[RETRY] Failed after {config.max_retries + 1} attempts for {op_name}. "
                    f"Last error: {error_type}: {str(last_exception)[:100]}. "
                    f"Attempts: {attempt_history_str}"
                )
                raise last_exception
            else:
                logger.error(
                    f"[RETRY] Non-retryable error for {op_name}: {error_type}: {str(last_exception)[:100]}"
                )
                raise last_exception

        # Calculate backoff delay
        delay = config.get_backoff_delay(attempt)
        attempt_record = f"attempt {attempt + 1} ({error_type}, retry after {delay:.1f}s)"
        attempt_history.append(attempt_record)

        logger.warning(
            f"[RETRY] {attempt_record} for {op_name}"
        )

        # Wait before retrying
        await asyncio.sleep(delay)
        attempt += 1

    # Should not reach here, but included for completeness
    if last_exception:
        raise last_exception
    raise RuntimeError(f"[RETRY] Unexpected error in retry loop for {op_name}")


def retry_sync(
    func: Callable[[], T],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    timeout: float = 30.0,
    operation_name: Optional[str] = None,
) -> T:
    """
    Execute a synchronous function with exponential backoff retry logic.

    Same retry behavior as with_retry() but for synchronous functions.

    Args:
        func: Synchronous function to execute
        max_retries: Maximum number of retries (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 2.0)
        initial_delay: Initial retry delay in seconds (default: 1.0)
        timeout: Timeout per attempt in seconds (not implemented for sync, for API compatibility)
        operation_name: Name of operation for logging (default: func.__name__)

    Returns:
        Result of the function call

    Raises:
        The exception from the final failed attempt if all retries exhausted
    """
    config = RetryConfig(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        timeout=timeout,
        jitter=True,
    )

    op_name = operation_name or getattr(func, '__name__', 'unknown_operation')
    attempt = 0
    last_exception = None
    attempt_history = []

    while attempt <= config.max_retries:
        try:
            result = func()
            if attempt > 0:
                logger.info(
                    f"[RETRY] Success on attempt {attempt + 1}/{config.max_retries + 1} "
                    f"for {op_name}"
                )
            return result
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__

            # Check for HTTP errors with status codes
            if hasattr(e, 'status_code'):
                status_code = e.status_code
                if status_code in PERMANENT_HTTP_CODES:
                    logger.error(
                        f"[RETRY] Permanent error {status_code} for {op_name}: {str(e)[:100]}"
                    )
                    raise
                should_retry = status_code in RETRYABLE_HTTP_CODES
            else:
                # Classify error as retryable or not
                should_retry = isinstance(e, (TIMEOUT_ERRORS, NETWORK_ERRORS))

            # If not retryable or exhausted retries, raise immediately
            if not should_retry or attempt >= config.max_retries:
                if attempt >= config.max_retries:
                    attempt_history_str = "; ".join(attempt_history) if attempt_history else "no attempts"
                    logger.error(
                        f"[RETRY] Failed after {config.max_retries + 1} attempts for {op_name}. "
                        f"Last error: {error_type}: {str(last_exception)[:100]}. "
                        f"Attempts: {attempt_history_str}"
                    )
                raise last_exception

            # Calculate backoff delay
            delay = config.get_backoff_delay(attempt)
            attempt_record = f"attempt {attempt + 1} ({error_type}, retry after {delay:.1f}s)"
            attempt_history.append(attempt_record)

            logger.warning(
                f"[RETRY] {attempt_record} for {op_name}"
            )

            # Wait before retrying
            time.sleep(delay)
            attempt += 1

    # Should not reach here
    if last_exception:
        raise last_exception
    raise RuntimeError(f"[RETRY] Unexpected error in retry loop for {op_name}")


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    timeout: float = 30.0,
):
    """
    Decorator for retrying sync functions.

    Usage:
        @retry_on_exception(max_retries=3, backoff_factor=2.0)
        def my_function():
            return some_api_call()
    """
    def decorator(func: Callable[[], T]) -> Callable[[], T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return retry_sync(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
                timeout=timeout,
                operation_name=func.__name__,
            )
        return wrapper
    return decorator
