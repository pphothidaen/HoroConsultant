"""
project/core/rate_limiter.py -- Multi-Tier Adaptive Token Bucket Rate Limiter
=============================================================================
Provides adaptive rate limiting with multi-tier quotas:
- IP-level rate limiting: 10 RPM (Requests Per Minute) default
- User/Session-level rate limiting: 20 RPM default
- Admin role quota: 120 RPM default
- Daily request budget cap: 40-150 req/day (default 100 req/day)
- DDoS micro-burst protection: Max 5 RPS (Requests Per Second)
- Input character clamping: <= 12,000 characters
- Max output tokens limit: <= 1,200 tokens
- Monthly budget cap guard (USD)
- Security audit violation logging with pure ASCII logs.
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("rate_limiter")

# Default Policy Constants
DEFAULT_IP_RPM: int = 10
DEFAULT_USER_RPM: int = 20
DEFAULT_ADMIN_RPM: int = 120
DEFAULT_BURST_RPS: int = 5
DEFAULT_DAILY_BUDGET: int = 100
MIN_DAILY_BUDGET: int = 40
MAX_DAILY_BUDGET: int = 150
MAX_INPUT_CHARS: int = 12000
MAX_OUTPUT_TOKENS: int = 1200


def clamp_input(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """
    Clamp input prompt/text to maximum character limit (<= 12,000 chars).
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def clamp_prompt(prompt: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """
    Alias for clamp_input for prompt strings.
    """
    return clamp_input(prompt, max_chars=max_chars)


def clamp_output_tokens(requested_tokens: int, max_tokens: int = MAX_OUTPUT_TOKENS) -> int:
    """
    Clamp requested output tokens to maximum token limit (<= 1,200 tokens).
    """
    try:
        tokens = int(requested_tokens)
    except (ValueError, TypeError):
        tokens = max_tokens
    if tokens < 1:
        return 1
    return min(tokens, max_tokens)


def check_input_size(text: str, max_chars: int = MAX_INPUT_CHARS) -> Tuple[bool, str]:
    """
    Check if input text exceeds character limit (<= 12,000 chars).

    Returns:
        (valid: bool, reason: str)
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    if len(text) > max_chars:
        return False, "input_character_limit_exceeded"
    return True, "ok"


class RateLimiter:
    """
    Adaptive Multi-Tier Rate Limiter with DDoS micro-burst guard,
    daily budget enforcement, input/output clamping, and security audit logging.
    """

    def __init__(
        self,
        ip_rpm: int = DEFAULT_IP_RPM,
        user_rpm: int = DEFAULT_USER_RPM,
        admin_rpm: int = DEFAULT_ADMIN_RPM,
        daily_budget_requests: int = DEFAULT_DAILY_BUDGET,
        burst_rps: int = DEFAULT_BURST_RPS,
        max_input_chars: int = MAX_INPUT_CHARS,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        monthly_budget_cap_usd: float = 0.0,
        anonymous_rpm: Optional[int] = None,
        default_rpm: Optional[int] = None,
        ai_rpm: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        # Resolve legacy and alias parameters
        if anonymous_rpm is not None:
            ip_rpm = anonymous_rpm
        if default_rpm is not None:
            ip_rpm = default_rpm

        # Read environment variables if available
        env_ip_rpm = os.getenv("RATE_LIMIT_IP_RPM")
        if env_ip_rpm is not None and default_rpm is None and anonymous_rpm is None:
            try:
                ip_rpm = int(env_ip_rpm)
            except ValueError:
                pass

        env_user_rpm = os.getenv("RATE_LIMIT_USER_RPM")
        if env_user_rpm is not None:
            try:
                user_rpm = int(env_user_rpm)
            except ValueError:
                pass

        env_daily_budget = os.getenv("DAILY_BUDGET_REQUESTS")
        if env_daily_budget is not None:
            try:
                daily_budget_requests = int(env_daily_budget)
            except ValueError:
                pass

        self.ip_rpm: int = ip_rpm
        self.anonymous_rpm: int = ip_rpm
        self.user_rpm: int = user_rpm
        self.admin_rpm: int = admin_rpm
        self.daily_budget_requests: int = daily_budget_requests
        self.burst_rps: int = burst_rps
        self.max_input_chars: int = max_input_chars
        self.max_output_tokens: int = max_output_tokens
        self.monthly_budget_cap_usd: float = monthly_budget_cap_usd
        self.ai_rpm: Optional[int] = ai_rpm

        # Token buckets: bucket_key -> (tokens, last_update_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (float(self.ip_rpm), time.monotonic()))

        # Second-level sliding window for DDoS micro-burst protection: ip -> list of timestamps
        self._burst_windows: Dict[str, List[float]] = defaultdict(list)

        # 24-hour sliding window for daily budget tracking: identifier -> list of timestamps
        self._daily_windows: Dict[str, List[float]] = defaultdict(list)

        # Security audit violations log
        self._violations: List[Dict[str, Any]] = []
        self._accumulated_cost_usd: float = 0.0

    def check_rate_limit(
        self,
        client_ip: str,
        path: str = "",
        role: str = "anonymous",
        user_id: Optional[str] = None,
        cost_usd: float = 0.0,
    ) -> Tuple[bool, str]:
        """
        Check if request from client_ip or user_id is allowed under:
        1. Monthly budget cap guard (USD)
        2. DDoS micro-burst protection guard (Max burst_rps requests/second)
        3. Daily budget cap (40-150 req/day per IP/User)
        4. Token bucket rate limit (IP: 10 RPM, User: 20 RPM, Admin: 120 RPM)

        Returns:
            (allowed: bool, reason: str)
        """
        now = time.monotonic()

        # 0. Monthly Budget Guard
        if self.monthly_budget_cap_usd > 0.0 and self._accumulated_cost_usd >= self.monthly_budget_cap_usd:
            self._log_violation(client_ip, path, "monthly_budget_cap_exceeded", user_id=user_id)
            logger.warning(f"[RateLimiter] [WARNING] Monthly budget cap (${self.monthly_budget_cap_usd:.2f}) exceeded")
            return False, "monthly_budget_cap_exceeded"

        # 1. DDoS Micro-Burst Protection Guard (Max burst_rps requests / second)
        burst_window = [ts for ts in self._burst_windows[client_ip] if now - ts < 1.0]
        if len(burst_window) >= self.burst_rps:
            self._log_violation(client_ip, path, "micro_burst_exceeded", user_id=user_id)
            logger.warning(
                f"[RateLimiter] [WARNING] Micro-burst DDoS limit ({self.burst_rps} RPS) triggered for IP {client_ip}"
            )
            return False, "micro_burst_exceeded"

        burst_window.append(now)
        self._burst_windows[client_ip] = burst_window

        # 2. Daily Budget Guard (Per User or IP)
        identity_key = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        if self.daily_budget_requests > 0 and role != "admin":
            daily_window = [ts for ts in self._daily_windows[identity_key] if now - ts < 86400.0]
            if len(daily_window) >= self.daily_budget_requests:
                self._log_violation(client_ip, path, "daily_budget_exceeded", user_id=user_id)
                logger.warning(
                    f"[RateLimiter] [WARNING] Daily budget ({self.daily_budget_requests} req/day) exceeded for {identity_key}"
                )
                return False, "daily_budget_exceeded"
        else:
            daily_window = [ts for ts in self._daily_windows[identity_key] if now - ts < 86400.0]

        # 3. Quota by Role & Identifier (IP: 10 RPM, User: 20 RPM, Admin: 120 RPM)
        if role == "admin":
            capacity = float(self.admin_rpm)
            bucket_key = f"admin:{client_ip}"
        elif user_id or role in ("user", "authenticated"):
            capacity = float(self.user_rpm)
            bucket_key = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        elif self.ai_rpm is not None and (role == "ai" or any(kw in path for kw in ("/interpret", "/ai", "/chat", "/debate"))):
            capacity = float(self.ai_rpm)
            bucket_key = f"ai:{client_ip}"
        else:
            capacity = float(self.ip_rpm)
            bucket_key = client_ip

        fill_rate = capacity / 60.0

        if bucket_key in self._buckets:
            tokens, last_update = self._buckets[bucket_key]
        else:
            tokens, last_update = capacity, now

        # Refill tokens
        tokens = min(capacity, tokens + (now - last_update) * fill_rate)

        if tokens < 1.0:
            self._buckets[bucket_key] = (tokens, now)
            reason = f"{role}_rate_limit_exceeded" if role not in ("anonymous", "default") else "rate_limit_exceeded"
            self._log_violation(client_ip, path, reason, user_id=user_id)
            logger.warning(
                f"[RateLimiter] [WARNING] Rate limit exceeded for {role} key {bucket_key} on {path}"
            )
            return False, reason

        self._buckets[bucket_key] = (tokens - 1.0, now)

        # Record daily usage timestamp
        daily_window.append(now)
        self._daily_windows[identity_key] = daily_window

        if cost_usd > 0.0:
            self.record_cost(cost_usd)

        return True, "ok"

    def clamp_input(self, text: str, max_chars: Optional[int] = None) -> str:
        """Clamp input text to character limit (<= 12,000 chars default)."""
        limit = max_chars if max_chars is not None else self.max_input_chars
        return clamp_input(text, max_chars=limit)

    def clamp_prompt(self, prompt: str, max_chars: Optional[int] = None) -> str:
        """Clamp prompt to character limit (<= 12,000 chars default)."""
        return self.clamp_input(prompt, max_chars=max_chars)

    def clamp_output_tokens(self, requested_tokens: int, max_tokens: Optional[int] = None) -> int:
        """Clamp requested output tokens (<= 1,200 tokens default)."""
        limit = max_tokens if max_tokens is not None else self.max_output_tokens
        return clamp_output_tokens(requested_tokens, max_tokens=limit)

    def check_input_size(self, text: str, max_chars: Optional[int] = None) -> Tuple[bool, str]:
        """Check if input text exceeds max character limit."""
        limit = max_chars if max_chars is not None else self.max_input_chars
        return check_input_size(text, max_chars=limit)

    def validate_and_clamp_request(
        self,
        prompt: str,
        max_output_tokens: Optional[int] = None,
        client_ip: str = "127.0.0.1",
        path: str = "",
    ) -> Tuple[str, int]:
        """
        Validate and clamp input prompt and output tokens.
        Logs security audit violation if prompt was truncated.

        Returns:
            (clamped_prompt: str, clamped_max_tokens: int)
        """
        limit_chars = self.max_input_chars
        limit_tokens = self.max_output_tokens if max_output_tokens is None else max_output_tokens

        clamped_prompt = self.clamp_input(prompt, max_chars=limit_chars)
        clamped_tokens = self.clamp_output_tokens(limit_tokens, max_tokens=self.max_output_tokens)

        if len(prompt) > limit_chars:
            self._log_violation(
                client_ip,
                path,
                "input_character_clamped",
                details={"original_length": len(prompt), "clamped_length": len(clamped_prompt)},
            )
            logger.info(
                f"[RateLimiter] [INFO] Prompt clamped from {len(prompt)} to {len(clamped_prompt)} chars for IP {client_ip}"
            )

        return clamped_prompt, clamped_tokens

    def _log_violation(
        self,
        client_ip: str,
        path: str,
        reason: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record security violation incident."""
        incident: Dict[str, Any] = {
            "ip": client_ip,
            "path": path,
            "reason": reason,
            "timestamp": time.time(),
        }
        if user_id:
            incident["user_id"] = user_id
        if details:
            incident["details"] = details
        self._violations.append(incident)
        if len(self._violations) > 500:
            self._violations = self._violations[-500:]

    def get_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return recent security audit violations."""
        return list(self._violations[-limit:])

    def clear_violations(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()

    def get_daily_budget_remaining(self, identifier: str) -> int:
        """Return remaining daily requests for an IP or User."""
        now = time.monotonic()
        identity_key = identifier if identifier.startswith(("user:", "ip:")) else f"ip:{identifier}"
        daily_window = [ts for ts in self._daily_windows[identity_key] if now - ts < 86400.0]
        remaining = max(0, self.daily_budget_requests - len(daily_window))
        return remaining

    def record_cost(self, cost_usd: float) -> None:
        """Record accumulated API cost."""
        self._accumulated_cost_usd += cost_usd

    def get_stats(self) -> Dict[str, Any]:
        """Return rate limiter statistics, quotas, and violation counts."""
        return {
            "ip_rpm": self.ip_rpm,
            "anonymous_rpm": self.anonymous_rpm,
            "user_rpm": self.user_rpm,
            "admin_rpm": self.admin_rpm,
            "daily_budget_requests": self.daily_budget_requests,
            "burst_rps": self.burst_rps,
            "max_input_chars": self.max_input_chars,
            "max_output_tokens": self.max_output_tokens,
            "tracked_ips": len(self._buckets),
            "tracked_daily_identities": len(self._daily_windows),
            "recent_violations_count": len(self._violations),
            "accumulated_cost_usd": self._accumulated_cost_usd,
        }


# Global singleton instance
rate_limiter = RateLimiter()
