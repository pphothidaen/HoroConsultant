"""
Hermes Core - Shared infrastructure for resource management,
timeout handling, and circuit breaking across all subagents.

All subagents import from this package to ensure consistent
resiliency policies.
"""

from hermes.core.resource_manager import (
    ResourceGovernor,
    ResourceExhausted,
    get_governor,
)

from hermes.core.timeout_manager import (
    AdaptiveTimeoutManager,
    timeout_manager,
)

from hermes.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    BREAKERS,
    get_breaker,
)

from hermes.core.atomic_fs import (
    file_lock,
    atomic_write_json,
    atomic_write_text,
    safe_read_json,
)

__all__ = [
    "ResourceGovernor",
    "ResourceExhausted",
    "get_governor",
    "AdaptiveTimeoutManager",
    "timeout_manager",
    "CircuitBreaker",
    "CircuitState",
    "BREAKERS",
    "get_breaker",
    "file_lock",
    "atomic_write_json",
    "atomic_write_text",
    "safe_read_json",
]
