import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("suraksha.circuit")


class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Tripped, requests diverted to fallback
    HALF_OPEN = "HALF_OPEN"# Testing dependency recovery


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 10.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def call(self, func: Callable, fallback: Callable, *args, **kwargs) -> Any:
        now = time.monotonic()

        # Check if circuit can attempt half-open recovery
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.recovery_timeout:
                logger.warning(f"Circuit Breaker [{self.name}] entering HALF_OPEN state.")
                self.state = CircuitState.HALF_OPEN
            else:
                return await fallback(*args, **kwargs)

        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit Breaker [{self.name}] recovered! Transitioning to CLOSED.")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            logger.error(f"Circuit Breaker [{self.name}] call failed: {e}. Failures: {self.failure_count}")

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.critical(f"Circuit Breaker [{self.name}] TRIPPED OPEN. Fallback activated.")

            return await fallback(*args, **kwargs)


redis_breaker = CircuitBreaker(name="RedisFeatureStore", failure_threshold=3, recovery_timeout=15.0)