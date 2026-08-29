"""
project/tests/test_zero_cost_pipeline.py
=========================================
Comprehensive Test Suite for Zero-Cost Fail-Closed Pipeline, Circuit Breakers,
Multi-Tier Rate Limiting, and Resilient AI Routing.

Covers:
1. Fail-Closed Zero-Cost Verification (AI_ZERO_COST_ONLY=true blocks paid providers).
2. Circuit Breaker 60s cooldown verification & 0ms instant bypass.
3. Multi-tier Rate Limiter (IP 10 RPM, User 20 RPM, Admin 120 RPM, Daily Budget 100 req/day).
4. Input Clamping (<=12k chars), Output Clamping (<=1.2k tokens), Micro-burst (5 RPS).
5. Deterministic Safe Net Fallback (<1ms baseline, zero cost).
6. Thread safety and concurrent stress testing.
"""

from __future__ import annotations

import concurrent.futures
import time
from unittest.mock import MagicMock, patch

import pytest

from project.core.ai_provider_router import (
    AIProviderRouter,
    BillingMode,
    CircuitBreakerState,
    ProjectQuotaPool,
    ProviderPool,
)
from project.core.rate_limiter import (
    RateLimiter,
    clamp_input,
    clamp_output_tokens,
    clamp_prompt,
    check_input_size,
)


# ============================================================================
# 1. FAIL-CLOSED ZERO-COST VERIFICATION
# ============================================================================

class TestFailClosedZeroCost:
    """Tests verifying strict fail-closed enforcement of zero-cost policy."""

    def test_zero_cost_flag_blocks_paid_providers_fail_closed(self):
        """When AI_ZERO_COST_ONLY=true, paid providers are blocked with 'zero_cost_blocked'."""
        paid_providers = ["openai", "vertex_ai", "claude", "anthropic", "azure_openai"]
        for provider in paid_providers:
            router = AIProviderRouter(
                primary_provider=provider,
                zero_cost_only=True,
            )
            res = router.call_ai(prompt="Analyze BaZi chart for Career")
            assert res["status"] == "error"
            assert res["error_type"] == "zero_cost_blocked"
            assert res["route_used"] == "fail_closed_zero_cost"
            assert res["model"] == "paid_provider_blocked"
            assert f"AI_ZERO_COST_ONLY=true blocked non-free provider '{provider}' fail-closed." in res["error_message"]

    def test_zero_cost_recognizes_free_and_subscription_providers(self):
        """Zero-cost mode permits Codex CLI (ChatGPT subscription), Gemini free, Reasoning Proxy, and Safe Net."""
        router = AIProviderRouter(zero_cost_only=True)
        assert router.is_provider_zero_cost("codex_chatgpt") is True
        assert router.is_provider_zero_cost("gemini") is True
        assert router.is_provider_zero_cost("reasoning_proxy") is True
        assert router.is_provider_zero_cost("deterministic_safe_net") is True
        assert router.is_provider_zero_cost("ollama") is True
        assert router.is_provider_zero_cost("cloudflare_ai") is True

    def test_zero_cost_rejects_paid_provider_classification(self):
        """Explicit paid provider names must return False from is_provider_zero_cost."""
        router = AIProviderRouter(zero_cost_only=True)
        assert router.is_provider_zero_cost("openai") is False
        assert router.is_provider_zero_cost("vertex_ai") is False
        assert router.is_provider_zero_cost("claude") is False
        assert router.is_provider_zero_cost("anthropic") is False
        assert router.is_provider_zero_cost("azure_openai") is False

    def test_billing_mode_enum_values(self):
        """Verify BillingMode enum string representation."""
        assert BillingMode.FREE.value == "free"
        assert BillingMode.SUBSCRIPTION.value == "subscription"
        assert BillingMode.PAID.value == "paid"

    def test_provider_pool_billing_mode_and_quota_pools(self):
        """Verify default provider pools maintain BillingMode.FREE classification."""
        router = AIProviderRouter()
        for name, pool in router.provider_pools.items():
            assert pool.billing_mode in {BillingMode.FREE, BillingMode.SUBSCRIPTION}
            assert pool.is_available() is True


# ============================================================================
# 2. CIRCUIT BREAKER 60S COOLDOWN & 0MS INSTANT BYPASS
# ============================================================================

class TestCircuitBreakerCooldown:
    """Tests verifying 60s cooldown tripping on 429 and 0ms instant bypass."""

    def test_circuit_breaker_initial_state_is_closed(self):
        """New circuit breaker starts in CLOSED state."""
        cb = CircuitBreakerState(name="test_cb", cooldown_seconds=60.0)
        assert cb.state == "CLOSED"
        assert cb.is_open() is False
        assert cb.failure_count == 0

    def test_circuit_breaker_trips_immediately_on_429_rate_limit(self):
        """429 rate limit error trips circuit breaker to OPEN on first occurrence."""
        cb = CircuitBreakerState(name="codex_cb", cooldown_seconds=60.0)
        t0 = 1000.0
        cb.record_failure(is_rate_limit=True, now=t0)
        assert cb.state == "OPEN"
        assert cb.is_open(now=t0 + 10.0) is True
        assert cb.is_open(now=t0 + 59.9) is True

    def test_circuit_breaker_instant_bypass_when_open(self):
        """When circuit is OPEN, is_open() returns True instantly without executing calls."""
        router = AIProviderRouter(primary_provider="codex_chatgpt")
        # Trip the Codex circuit breaker
        router.circuit_breakers["codex_chatgpt"].trip(cooldown=60.0)
        assert router.circuit_breakers["codex_chatgpt"].is_open() is True

        t_start = time.perf_counter()
        res = router.invoke_codex_chatgpt(prompt="Quick prompt")
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        assert res["status"] == "error"
        assert res["error_type"] == "circuit_breaker_open"
        assert "Circuit breaker OPEN" in res["error_message"]
        # Must execute in under 10ms (instant bypass)
        assert elapsed_ms < 10.0

    def test_circuit_breaker_half_open_transition_after_cooldown(self):
        """After cooldown_seconds, is_open() transitions circuit to HALF_OPEN and returns False."""
        cb = CircuitBreakerState(name="test_cb", cooldown_seconds=60.0)
        t0 = 1000.0
        cb.trip(cooldown=60.0, now=t0)
        assert cb.is_open(now=t0 + 30.0) is True

        # At exactly or after 60s
        assert cb.is_open(now=t0 + 60.0) is False
        assert cb.state == "HALF_OPEN"

    def test_circuit_breaker_success_resets_to_closed(self):
        """Successful invocation resets state to CLOSED and clears failure count."""
        cb = CircuitBreakerState(name="test_cb", cooldown_seconds=60.0)
        cb.record_failure(is_rate_limit=True)
        assert cb.state == "OPEN"

        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.is_open() is False

    def test_circuit_breaker_manual_reset(self):
        """Manual reset returns circuit breaker to initial CLOSED state."""
        cb = CircuitBreakerState(name="test_cb", cooldown_seconds=60.0)
        cb.trip()
        assert cb.state == "OPEN"
        cb.reset()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time == 0.0

    def test_circuit_breaker_consecutive_non_rate_limit_failures(self):
        """Non-rate-limit failures trip circuit breaker after reaching failure_threshold."""
        cb = CircuitBreakerState(name="test_cb", failure_threshold=3, cooldown_seconds=60.0)
        cb.record_failure(is_rate_limit=False)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 1

        cb.record_failure(is_rate_limit=False)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 2

        cb.record_failure(is_rate_limit=False)
        assert cb.state == "OPEN"
        assert cb.failure_count == 3

    def test_multi_tier_circuit_breaker_cascading_failover(self):
        """
        When Tier 1 (Codex) circuit trips, routes to Tier 3 (Reasoning Proxy).
        When Tier 3 circuit trips, routes to Tier 2 (Gemini).
        When Tier 2 circuit trips, routes to Tier 4 (Deterministic Safe Net).
        """
        router = AIProviderRouter(
            primary_provider="codex_chatgpt",
            reasoning_base_url="https://api.reasoning.local/v1",
        )

        # 1. Trip Tier 1
        router.circuit_breakers["codex_chatgpt"].trip()

        # Mock Reasoning Proxy success
        with patch.object(router, "invoke_reasoning_proxy", return_value={
            "status": "success",
            "provider": "REASONING_PROXY",
            "model": "deepseek-r1",
            "content": "Reasoning Tier Output",
            "raw_response": None,
            "error_message": None,
            "error_type": None,
            "route_used": "reasoning_proxy",
        }):
            res1 = router.call_ai(prompt="Test cascade")
            assert res1["status"] == "success"
            assert res1["provider"] == "REASONING_PROXY"

        # 2. Trip Tier 3 as well
        router.circuit_breakers["reasoning_proxy"].trip()
        res2 = router.call_ai(prompt="Test cascade 2")
        assert res2["status"] == "fallback"
        assert res2["provider"] == "GEMINI"
        assert res2["route_used"] == "gemini_fallback"

        # 3. Trip Tier 2 as well -> Falls to Tier 4 Deterministic Safe Net
        router.circuit_breakers["gemini"].trip()
        res3 = router.call_ai(prompt="Test cascade 3")
        assert res3["status"] == "fallback"
        assert res3["provider"] == "DETERMINISTIC_SAFE_NET"
        assert res3["route_used"] == "deterministic_safe_net"
        assert "DETERMINISTIC SAFE NET" in res3["content"]


# ============================================================================
# 3. MULTI-TIER RATE LIMITER & CLAMPING VERIFICATION
# ============================================================================

class TestMultiTierRateLimiter:
    """Tests verifying multi-tier quotas, daily budgets, micro-burst, and clamping."""

    def test_ip_rate_limit_10_rpm(self):
        """Anonymous IP bucket allows exactly 10 RPM and rejects the 11th request."""
        limiter = RateLimiter(ip_rpm=10, burst_rps=100, daily_budget_requests=100)
        ip = "192.168.1.100"

        for i in range(10):
            allowed, reason = limiter.check_rate_limit(client_ip=ip, role="anonymous")
            assert allowed is True, f"Request {i+1} should be allowed, got {reason}"
            assert reason == "ok"

        # 11th request must be rejected
        allowed, reason = limiter.check_rate_limit(client_ip=ip, role="anonymous")
        assert allowed is False
        assert reason in ("rate_limit_exceeded", "anonymous_rate_limit_exceeded")

    def test_user_rate_limit_20_rpm(self):
        """Authenticated User bucket allows 20 RPM and tracks by user_id."""
        limiter = RateLimiter(user_rpm=20, burst_rps=100, daily_budget_requests=100)
        user_id = "user_premium_01"

        for i in range(20):
            allowed, reason = limiter.check_rate_limit(
                client_ip="10.0.0.1",
                role="user",
                user_id=user_id,
            )
            assert allowed is True, f"Request {i+1} should be allowed, got {reason}"

        # 21st request must be rejected
        allowed, reason = limiter.check_rate_limit(
            client_ip="10.0.0.1",
            role="user",
            user_id=user_id,
        )
        assert allowed is False
        assert reason == "user_rate_limit_exceeded"

    def test_admin_rate_limit_120_rpm(self):
        """Admin role has high quota (120 RPM)."""
        limiter = RateLimiter(admin_rpm=120, burst_rps=200, daily_budget_requests=500)
        admin_ip = "127.0.0.1"

        for i in range(120):
            allowed, reason = limiter.check_rate_limit(client_ip=admin_ip, role="admin")
            assert allowed is True, f"Admin request {i+1} failed"

        allowed, reason = limiter.check_rate_limit(client_ip=admin_ip, role="admin")
        assert allowed is False
        assert reason == "admin_rate_limit_exceeded"

    def test_daily_budget_100_requests_cap(self):
        """Daily request budget cap (100 req/day) enforces hard ceiling across rolling 24h."""
        limiter = RateLimiter(
            ip_rpm=1000,  # High RPM so RPM bucket doesn't block
            burst_rps=1000,
            daily_budget_requests=100,
        )
        ip = "192.168.1.50"

        for i in range(100):
            assert limiter.get_daily_budget_remaining(ip) == 100 - i
            allowed, reason = limiter.check_rate_limit(client_ip=ip)
            assert allowed is True

        assert limiter.get_daily_budget_remaining(ip) == 0

        # 101st request must be blocked by daily budget
        allowed, reason = limiter.check_rate_limit(client_ip=ip)
        assert allowed is False
        assert reason == "daily_budget_exceeded"

    def test_micro_burst_ddos_guard_5_rps(self):
        """Micro-burst limit strictly caps at 5 RPS within a 1-second sliding window."""
        limiter = RateLimiter(
            ip_rpm=100,
            burst_rps=5,
            daily_budget_requests=100,
        )
        ip = "172.16.0.5"

        for i in range(5):
            allowed, reason = limiter.check_rate_limit(client_ip=ip)
            assert allowed is True, f"Burst request {i+1} failed"

        # 6th request within same second must be blocked
        allowed, reason = limiter.check_rate_limit(client_ip=ip)
        assert allowed is False
        assert reason == "micro_burst_exceeded"

    def test_input_character_clamping_12k_chars(self):
        """Input character clamping truncates prompt text > 12,000 characters."""
        short_prompt = "A" * 1000
        assert clamp_input(short_prompt) == short_prompt

        exact_prompt = "B" * 12000
        assert clamp_input(exact_prompt) == exact_prompt

        oversized_prompt = "C" * 15000
        clamped = clamp_input(oversized_prompt)
        assert len(clamped) == 12000
        assert clamped == "C" * 12000

        # Alias function check
        assert clamp_prompt(oversized_prompt) == "C" * 12000

    def test_check_input_size_validation(self):
        """check_input_size returns valid boolean flag and reason."""
        valid_res, valid_msg = check_input_size("Safe prompt", max_chars=12000)
        assert valid_res is True
        assert valid_msg == "ok"

        invalid_res, invalid_msg = check_input_size("X" * 12001, max_chars=12000)
        assert invalid_res is False
        assert invalid_msg == "input_character_limit_exceeded"

    def test_output_token_clamping_1200_tokens(self):
        """clamp_output_tokens restricts requested tokens <= 1,200 tokens."""
        assert clamp_output_tokens(500) == 500
        assert clamp_output_tokens(1200) == 1200
        assert clamp_output_tokens(2048) == 1200
        assert clamp_output_tokens(8192) == 1200

        # Boundary and invalid values
        assert clamp_output_tokens(0) == 1
        assert clamp_output_tokens(-10) == 1
        assert clamp_output_tokens("invalid_number") == 1200

    def test_validate_and_clamp_request_with_audit_log(self):
        """validate_and_clamp_request logs audit violation when input is clamped."""
        limiter = RateLimiter()
        oversized = "Z" * 13000
        clamped_p, clamped_t = limiter.validate_and_clamp_request(
            prompt=oversized,
            max_output_tokens=3000,
            client_ip="192.168.1.99",
            path="/api/interpret",
        )
        assert len(clamped_p) == 12000
        assert clamped_t == 1200

        violations = limiter.get_violations()
        assert len(violations) >= 1
        last_v = violations[-1]
        assert last_v["reason"] == "input_character_clamped"
        assert last_v["ip"] == "192.168.1.99"
        assert last_v["details"]["original_length"] == 13000
        assert last_v["details"]["clamped_length"] == 12000

    def test_monthly_budget_cap_guard(self):
        """When monthly budget cap is exceeded, requests are rejected with monthly_budget_cap_exceeded."""
        limiter = RateLimiter(monthly_budget_cap_usd=5.0)
        limiter.record_cost(4.50)

        # Under cap
        allowed, _ = limiter.check_rate_limit(client_ip="1.1.1.1")
        assert allowed is True

        # Exceed cap
        limiter.record_cost(0.60)  # Total 5.10 > 5.00
        allowed, reason = limiter.check_rate_limit(client_ip="1.1.1.1")
        assert allowed is False
        assert reason == "monthly_budget_cap_exceeded"

    def test_rate_limiter_stats_and_violations_clearing(self):
        """Verify get_stats output and clear_violations functionality."""
        limiter = RateLimiter(ip_rpm=10, user_rpm=20, daily_budget_requests=100)
        stats = limiter.get_stats()
        assert stats["ip_rpm"] == 10
        assert stats["user_rpm"] == 20
        assert stats["daily_budget_requests"] == 100
        assert stats["burst_rps"] == 5
        assert stats["max_input_chars"] == 12000
        assert stats["max_output_tokens"] == 1200

        limiter._log_violation("1.2.3.4", "/test", "test_reason")
        assert len(limiter.get_violations()) == 1
        limiter.clear_violations()
        assert len(limiter.get_violations()) == 0


# ============================================================================
# 4. ZERO-COST PIPELINE INTEGRATION & CONCURRENCY
# ============================================================================

class TestZeroCostPipelineIntegration:
    """Integration and stress tests for zero-cost pipeline components."""

    def test_end_to_end_rate_limit_clamp_and_dispatch(self):
        """Full pipeline: validate & clamp request, check rate limit, and route to free provider."""
        limiter = RateLimiter()
        router = AIProviderRouter(primary_provider="codex_chatgpt", zero_cost_only=True)

        user_prompt = "  Calculate BaZi Natal Chart for 1990-05-15  " + ("X" * 13000)
        clamped_prompt, clamped_tokens = limiter.validate_and_clamp_request(
            prompt=user_prompt,
            max_output_tokens=2000,
            client_ip="192.168.1.1",
        )

        assert len(clamped_prompt) == 12000
        assert clamped_tokens == 1200

        allowed, reason = limiter.check_rate_limit(client_ip="192.168.1.1", role="user", user_id="u123")
        assert allowed is True

        # Mock codex CLI success
        with patch.object(router, "invoke_codex_chatgpt", return_value={
            "status": "success",
            "provider": "CODEX_CHATGPT",
            "model": "codex_chatgpt",
            "content": "BaZi Analysis: Day Master is Bing Fire.",
            "raw_response": None,
            "error_message": None,
            "error_type": None,
            "route_used": "codex_chatgpt",
        }):
            res = router.call_ai(prompt=clamped_prompt)
            assert res["status"] == "success"
            assert res["provider"] == "CODEX_CHATGPT"
            assert "Bing Fire" in res["content"]

    def test_deterministic_safe_net_fallback_on_total_exhaustion(self):
        """When all tiers fail, deterministic safe net returns instant offline calculation baseline."""
        router = AIProviderRouter(primary_provider="codex_chatgpt", zero_cost_only=True)

        # Trip all circuit breakers
        router.circuit_breakers["codex_chatgpt"].trip()
        router.circuit_breakers["reasoning_proxy"].trip()
        router.circuit_breakers["gemini"].trip()

        t_start = time.perf_counter()
        res = router.call_ai(prompt="Calculate Feng Shui Bagua map")
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        assert res["status"] == "fallback"
        assert res["provider"] == "DETERMINISTIC_SAFE_NET"
        assert res["route_used"] == "deterministic_safe_net"
        assert "DETERMINISTIC SAFE NET" in res["content"]
        # Guaranteed <5ms
        assert elapsed_ms < 5.0

    def test_concurrent_rate_limiting_thread_safety(self):
        """Concurrent threads checking rate limits maintain thread safety and accurate limits."""
        limiter = RateLimiter(ip_rpm=50, burst_rps=100, daily_budget_requests=200)
        ip = "10.0.0.99"
        total_requests = 100

        def fire_request(req_id: int):
            return limiter.check_rate_limit(client_ip=ip, role="anonymous")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(fire_request, range(total_requests)))

        allowed_count = sum(1 for allowed, _ in results if allowed)
        blocked_count = sum(1 for allowed, _ in results if not allowed)

        assert allowed_count == 50
        assert blocked_count == 50
        assert len(results) == 100
# Baseline 03 provenance marker
