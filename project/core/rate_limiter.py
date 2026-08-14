"""
project/core/rate_limiter.py — In-Memory Token Bucket Rate Limiter
===================================================================
Provides rate limiting with per-IP limits, endpoint category limits,
and monthly budget protection guards.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Dict, Tuple

logger = logging.getLogger("rate_limiter")


class RateLimiter:
    """
    Token-bucket rate limiter with IP tracking and AI inference budget protection.
    """

    def __init__(
        self,
        default_rpm: int = 120,
        ai_rpm: int = 20,
        monthly_budget_cap_usd: float = 0.0,
    ):
        self.default_rpm = default_rpm
        self.ai_rpm = ai_rpm
        self.monthly_budget_cap_usd = monthly_budget_cap_usd
        
        # IP bucket storage: ip -> (tokens, last_update_timestamp)
        self._ip_buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (float(default_rpm), time.monotonic()))
        self._ai_buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (float(ai_rpm), time.monotonic()))
        
        # Total cost tracked this session
        self._accumulated_cost_usd: float = 0.0

    def check_rate_limit(self, client_ip: str, path: str) -> Tuple[bool, str]:
        """
        Check if a request from client_ip to path is allowed under rate limits.

        Returns:
            (allowed: bool, reason: str)
        """
        now = time.monotonic()
        is_ai_endpoint = any(kw in path for kw in ("/interpret", "/debate", "/generate", "/mian_xiang"))

        # 1. Budget check for paid inference
        if is_ai_endpoint and self.monthly_budget_cap_usd > 0.0:
            if self._accumulated_cost_usd >= self.monthly_budget_cap_usd:
                logger.warning(f"[RateLimiter] Monthly budget cap reached: ${self._accumulated_cost_usd:.2f}")
                return False, "monthly_budget_cap_exceeded"

        # 2. Token refill calculation
        if is_ai_endpoint:
            tokens, last_update = self._ai_buckets[client_ip]
            capacity = float(self.ai_rpm)
            fill_rate = capacity / 60.0
            tokens = min(capacity, tokens + (now - last_update) * fill_rate)

            if tokens < 1.0:
                self._ai_buckets[client_ip] = (tokens, now)
                logger.warning(f"[RateLimiter] AI Rate limit exceeded for IP {client_ip} on {path}")
                return False, "ai_rate_limit_exceeded"

            self._ai_buckets[client_ip] = (tokens - 1.0, now)
            return True, "ok"

        else:
            tokens, last_update = self._ip_buckets[client_ip]
            capacity = float(self.default_rpm)
            fill_rate = capacity / 60.0
            tokens = min(capacity, tokens + (now - last_update) * fill_rate)

            if tokens < 1.0:
                self._ip_buckets[client_ip] = (tokens, now)
                logger.warning(f"[RateLimiter] Standard Rate limit exceeded for IP {client_ip} on {path}")
                return False, "rate_limit_exceeded"

            self._ip_buckets[client_ip] = (tokens - 1.0, now)
            return True, "ok"

    def record_cost(self, cost_usd: float) -> None:
        """Record accumulated API cost."""
        self._accumulated_cost_usd += cost_usd

    def get_stats(self) -> dict:
        """Return rate limiter statistics."""
        return {
            "default_rpm": self.default_rpm,
            "ai_rpm": self.ai_rpm,
            "tracked_ips": len(self._ip_buckets),
            "accumulated_cost_usd": self._accumulated_cost_usd,
            "budget_cap_usd": self.monthly_budget_cap_usd,
        }


# Global singleton
rate_limiter = RateLimiter()
