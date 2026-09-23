"""
Circuit Breaker Pattern for external service resilience.
Prevents cascade failures when services like Jira/Cloudflare are down.
"""
from enum import Enum
from time import time
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Prevents repeated calls to failing services by temporarily stopping requests.

    States:
      - CLOSED: Normal operation, requests flow through
      - OPEN: Requests are blocked for a cooldown period
      - HALF_OPEN: Allow one test request to determine if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: tuple = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[float] = None
        self._success_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function call with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' → HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN — blocking call")
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            logger.warning(f"Circuit breaker '{self.name}' failure: {e}")
            raise e

    def _on_success(self):
        """Reset failure counter on successful call."""
        self.failure_count = 0
        self._success_count += 1
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' → CLOSED (recovered)")
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Increment failure counter and open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self._success_count = 0
            logger.error(f"Circuit breaker '{self.name}' → OPEN")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False
        return (time() - self.last_failure_time) >= self.timeout

    @property
    def is_open(self) -> bool:
        """Check if circuit is currently open."""
        return self.state == CircuitState.OPEN


# Pre-configured breakers for common services
BREAKERS = {
    "jira": CircuitBreaker(
        name="jira-api",
        failure_threshold=3,
        timeout=60,
        expected_exception=(ConnectionError, TimeoutError, Exception)
    ),
    "github": CircuitBreaker(
        name="github-api",
        failure_threshold=5,
        timeout=30,
        expected_exception=(ConnectionError, TimeoutError, Exception)
    ),
    "cloudflare": CircuitBreaker(
        name="cloudflare-api",
        failure_threshold=3,
        timeout=60,
        expected_exception=(ConnectionError, TimeoutError, Exception)
    ),
    "vercel": CircuitBreaker(
        name="vercel-api",
        failure_threshold=3,
        timeout=30,
        expected_exception=(ConnectionError, TimeoutError, Exception)
    ),
    "doppler": CircuitBreaker(
        name="doppler-cli",
        failure_threshold=3,
        timeout=30,
        expected_exception=(ConnectionError, TimeoutError, Exception)
    ),
}


def get_breaker(name: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.
    Used by all subagents when calling external services.
    """
    if name not in BREAKERS:
        BREAKERS[name] = CircuitBreaker(
            name=name,
            failure_threshold=3,
            timeout=60,
            expected_exception=(ConnectionError, TimeoutError, Exception)
        )
    return BREAKERS[name]
