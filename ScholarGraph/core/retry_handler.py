"""
Retry handler with exponential backoff for network operations.
"""

import time
import functools
from typing import Callable, TypeVar, Any, Type
from neo4j.exceptions import ServiceUnavailable, SessionExpired
import requests

# Type variable for generic function return type
T = TypeVar('T')


def retry_with_exponential_backoff(
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    exponential_base: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (
        ServiceUnavailable,
        SessionExpired,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    )
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Exponential base for calculating delays
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_attempts=3)
        def fetch_data():
            return api.get("/data")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        # Last attempt failed, re-raise the exception
                        raise

                    # Calculate next delay with exponential backoff
                    actual_delay = min(delay, max_delay)

                    print(
                        f"Attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {str(e)}"
                    )
                    print(f"Retrying in {actual_delay:.1f} seconds...")

                    time.sleep(actual_delay)

                    # Increase delay for next attempt
                    delay *= exponential_base

            # This should never be reached, but satisfies type checker
            raise RuntimeError("Unreachable code")

        return wrapper

    return decorator


class RetryContext:
    """
    Context manager for retry operations with custom logic.

    Example:
        with RetryContext(max_attempts=3) as retry:
            while retry.should_retry():
                try:
                    result = api_call()
                    retry.success()
                    break
                except Exception as e:
                    retry.failed(e)
    """

    def __init__(
        self,
        max_attempts: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 32.0,
        exponential_base: float = 2.0,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

        self.attempt = 0
        self.delay = initial_delay
        self.last_exception: Exception | None = None
        self._success = False

    def __enter__(self) -> "RetryContext":
        """Enter the retry context."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit the retry context."""
        if exc_type is not None and not self._success:
            # An exception occurred and we didn't mark as success
            if self.attempt < self.max_attempts:
                # Should have called should_retry() - let the exception propagate
                return False

        # Suppress the exception if we've exhausted retries
        return False

    def should_retry(self) -> bool:
        """
        Check if we should attempt another retry.

        Returns:
            bool: True if we should retry, False if exhausted
        """
        self.attempt += 1
        return self.attempt <= self.max_attempts

    def failed(self, exception: Exception) -> None:
        """
        Mark current attempt as failed and wait before next retry.

        Args:
            exception: The exception that caused the failure
        """
        self.last_exception = exception

        if self.attempt < self.max_attempts:
            actual_delay = min(self.delay, self.max_delay)

            print(
                f"Attempt {self.attempt}/{self.max_attempts} failed: "
                f"{type(exception).__name__}: {str(exception)}"
            )
            print(f"Retrying in {actual_delay:.1f} seconds...")

            time.sleep(actual_delay)
            self.delay *= self.exponential_base
        else:
            # Last attempt failed
            print(
                f"All {self.max_attempts} attempts failed. "
                f"Last error: {type(exception).__name__}: {str(exception)}"
            )

    def success(self) -> None:
        """Mark the current attempt as successful."""
        self._success = True


if __name__ == "__main__":
    # Test the retry decorator
    @retry_with_exponential_backoff(max_attempts=3, initial_delay=0.5)
    def test_function(succeed_on_attempt: int = 2):
        """Test function that succeeds on specified attempt."""
        if not hasattr(test_function, 'attempt'):
            test_function.attempt = 0
        test_function.attempt += 1

        print(f"Test function attempt {test_function.attempt}")

        if test_function.attempt < succeed_on_attempt:
            raise ConnectionError("Simulated connection error")

        return "Success!"

    try:
        result = test_function(succeed_on_attempt=2)
        print(f"Result: {result}")
    except ConnectionError as e:
        print(f"Failed after all retries: {e}")
