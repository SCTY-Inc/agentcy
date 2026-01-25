"""Retry utilities with exponential backoff.

Provides decorators and utilities for retrying failed operations
with configurable backoff strategies.
"""

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


class RetryExhausted(Exception):
    """All retry attempts exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate delay for exponential backoff.

    Args:
        attempt: Attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        jitter: Add randomization to prevent thundering herd

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2**attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())
    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay cap
        retryable_exceptions: Exception types to retry on
        on_retry: Callback on each retry (attempt, exception)

    Returns:
        Decorator function

    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def call_api():
            return api.get_data()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e

                    if attempt + 1 < max_attempts:
                        delay = exponential_backoff(
                            attempt, base_delay, max_delay
                        )
                        if on_retry:
                            on_retry(attempt + 1, e)
                        time.sleep(delay)

            assert last_error is not None
            raise RetryExhausted(max_attempts, last_error)

        return wrapper

    return decorator


def retry_stage(
    func: Callable[..., T],
    max_attempts: int = 3,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """Retry a stage execution with backoff.

    Args:
        func: Zero-arg function to retry
        max_attempts: Maximum attempts
        on_retry: Callback on each retry

    Returns:
        Function result

    Raises:
        RetryExhausted: If all attempts fail
    """
    from agentcy.controller import StageExecutionError

    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return func()
        except StageExecutionError as e:
            last_error = e

            if not e.retryable:
                raise

            if attempt + 1 < max_attempts:
                delay = exponential_backoff(attempt)
                if on_retry:
                    on_retry(attempt + 1, e)
                time.sleep(delay)

    assert last_error is not None
    raise RetryExhausted(max_attempts, last_error)
