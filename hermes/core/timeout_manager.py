"""
Adaptive timeout manager for external service calls.
Implements exponential backoff with ceilings per service.
"""
from typing import Dict, Any
import time


# Base configuration: tuned for observed service latencies
SERVICE_TIMEOUTS: Dict[str, Dict[str, Any]] = {
    # Jira Cloud API
    "jira": {
        "base": 30,
        "retry_multiplier": 1.5,
        "max": 120,
        "max_retries": 3
    },
    # GitHub API
    "github_api": {
        "base": 60,
        "retry_multiplier": 2.0,
        "max": 300,
        "max_retries": 3
    },
    # Render.com deploy status
    "render": {
        "base": 30,
        "retry_multiplier": 1.5,
        "max": 120,
        "max_retries": 3
    },
    # Doppler CLI / secrets
    "doppler": {
        "base": 15,
        "retry_multiplier": 1.3,
        "max": 60,
        "max_retries": 3
    },
    # Cloudflare Workers KV
    "workers_kv": {
        "base": 15,
        "retry_multiplier": 1.3,
        "max": 60,
        "max_retries": 3
    }
}


class AdaptiveTimeoutManager:
    """
    Manages timeout values per service, adapting based on failure history.
    Used by all subagents making external API calls.
    """

    def __init__(self):
        self._call_history: Dict[str, list] = {}

    def get_timeout(self, service: str) -> float:
        """
        Get current timeout for a service.
        Adjusts based on recent failure rate.
        """
        config = SERVICE_TIMEOUTS.get(service)
        if not config:
            return 30.0  # default

        base = config["base"]
        multiplier = config["retry_multiplier"]
        max_val = config["max"]

        history = self._call_history.get(service, [])
        fail_count = sum(1 for h in history if not h)

        if fail_count == 0:
            return base

        # Exponential backoff: failed N times → increase timeout
        timeout = base
        for i in range(fail_count):
            timeout = min(timeout * multiplier, max_val)

        return timeout

    def record_result(self, service: str, success: bool):
        """Record a call result to inform future timeout decisions."""
        if service not in self._call_history:
            self._call_history[service] = []

        # Keep last 20 results
        self._call_history[service].append(success)
        if len(self._call_history[service]) > 20:
            self._call_history[service] = self._call_history[service][-20:]

    def should_retry(self, service: str, attempt: int) -> bool:
        """Check if we should retry based on attempt count and config."""
        config = SERVICE_TIMEOUTS.get(service, {})
        return attempt < config.get("max_retries", 3)


# Module-level instance
timeout_manager = AdaptiveTimeoutManager()
