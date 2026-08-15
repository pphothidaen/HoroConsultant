"""
project/core/rate_limiter.py — Multi-Tier Adaptive Token Bucket Rate Limiter
=============================================================================
Provides adaptive rate limiting with role-based quotas (Anonymous 20 RPM, Admin 120 RPM),
DDoS micro-burst protection (Max 5 RPS), and security incident logging.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("rate_limiter")


class RateLimiter:
    """
    Adaptive Multi-Tier Rate Limiter with DDoS micro-burst guard and security auditing (Decision 8).
    """

    def __init__(
        self,
        anonymous_rpm: int = 20,
        admin_rpm: int = 120,
        burst_rps: int = 5,
        monthly_budget_cap_usd: float = 0.0,
        default_rpm: Optional[int] = None,
        ai_rpm: Optional[int] = None,
        **kwargs,
    ):
        if default_rpm is not None:
            anonymous_rpm = default_rpm
        self.anonymous_rpm = anonymous_rpm
        self.admin_rpm = admin_rpm
        self.burst_rps = burst_rps
        self.monthly_budget_cap_usd = monthly_budget_cap_usd
        self.ai_rpm = ai_rpm

        # Token buckets: ip -> (tokens, last_update_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (float(anonymous_rpm), time.monotonic()))
        
        # Second-level sliding window for DDoS micro-burst protection: ip -> list of timestamps
        self._burst_windows: Dict[str, List[float]] = defaultdict(list)

        # Security audit violations log
        self._violations: List[dict] = []
        self._accumulated_cost_usd: float = 0.0

    def check_rate_limit(
        self,
        client_ip: str,
        path: str,
        role: str = "anonymous",
    ) -> Tuple[bool, str]:
        """
        Check if request from client_ip is allowed under multi-tier and burst limits.

        Returns:
            (allowed: bool, reason: str)
        """
        now = time.monotonic()

        # 0. Monthly Budget Guard
        if self.monthly_budget_cap_usd > 0.0 and self._accumulated_cost_usd >= self.monthly_budget_cap_usd:
            self._log_violation(client_ip, path, "monthly_budget_cap_exceeded")
            return False, "monthly_budget_cap_exceeded"

        # 1. DDoS Micro-Burst Protection Guard (Max burst_rps requests / second)
        window = [ts for ts in self._burst_windows[client_ip] if now - ts < 1.0]
        if len(window) >= self.burst_rps:
            self._log_violation(client_ip, path, "micro_burst_exceeded")
            logger.warning(f"[RateLimiter] Micro-burst DDoS limit ({self.burst_rps} RPS) triggered for IP {client_ip}")
            return False, "micro_burst_exceeded"

        window.append(now)
        self._burst_windows[client_ip] = window

        # 2. Quota by Role (Anonymous 20 RPM vs Admin 120 RPM)
        capacity = float(self.admin_rpm if role == "admin" else self.anonymous_rpm)
        fill_rate = capacity / 60.0

        tokens, last_update = self._buckets[client_ip]
        # Refill tokens
        tokens = min(capacity, tokens + (now - last_update) * fill_rate)

        if tokens < 1.0:
            self._buckets[client_ip] = (tokens, now)
            reason = f"{role}_rate_limit_exceeded" if role != "anonymous" else "rate_limit_exceeded"
            self._log_violation(client_ip, path, reason)
            logger.warning(f"[RateLimiter] Rate limit exceeded for {role} IP {client_ip} on {path}")
            return False, reason

        self._buckets[client_ip] = (tokens - 1.0, now)
        return True, "ok"

    def _log_violation(self, client_ip: str, path: str, reason: str) -> None:
        """Record security violation incident."""
        self._violations.append({
            "ip": client_ip,
            "path": path,
            "reason": reason,
            "timestamp": time.time(),
        })
        if len(self._violations) > 500:
            self._violations = self._violations[-500:]

    def record_cost(self, cost_usd: float) -> None:
        """Record accumulated API cost."""
        self._accumulated_cost_usd += cost_usd

    def get_stats(self) -> dict:
        """Return rate limiter statistics and violation counts."""
        return {
            "anonymous_rpm": self.anonymous_rpm,
            "admin_rpm": self.admin_rpm,
            "burst_rps": self.burst_rps,
            "tracked_ips": len(self._buckets),
            "recent_violations_count": len(self._violations),
            "accumulated_cost_usd": self._accumulated_cost_usd,
        }


# Global singleton instance
rate_limiter = RateLimiter()
