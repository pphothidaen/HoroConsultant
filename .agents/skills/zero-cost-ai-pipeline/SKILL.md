---
name: zero-cost-ai-pipeline
description: Implement fail-closed zero-cost AI provider routing, circuit breakers, and rate limits.
---

# Zero-Cost AI Pipeline Implementation & Verification

## 1. Core Principles
- **Fail-Closed Zero-Cost**: When `AI_ZERO_COST_ONLY=true`, never fallback to paid APIs.
- **Quota Pooling**: Separate key auth redundancy from multi-project quota pools.
- **In-Memory Circuit Breakers**: Trip 60s cooldown on 429 rate limit for 0ms instant bypass.
- **Multi-Tier Rate Limiting**: IP limit (10 RPM), User limit (20 RPM), Daily Budget (40-150 req/day).
- **Deterministic Safe Net**: Fallback to Rust PyO3 engine (<1ms) on full free tier exhaustion.

## 2. Implementation Checklist
1. **AI Provider Router (`project/core/ai_provider_router.py` & `project/api_router.py`)**:
   - Filter active providers by `BillingMode.FREE` and `estimated_cost == 0.0`.
   - Implement `ProviderPool` with project-grouped keys.
   - Attach `CircuitBreakerState` tracking 429 rate limits.
2. **Rate Limiter (`project/core/rate_limiter.py`)**:
   - Enforce IP, User, Session, and Daily request quotas.
   - Enforce input character and output token clamping.
3. **Semantic Cache (`project/core/semantic_cache.py`)**:
   - SHA-256 normalized prompt + metadata caching.
   - TTL by domain category (daily horoscope: 6-24h, FAQ: 30d).
4. **Verification & Testing**:
   - Run unit tests in `project/tests/test_zero_cost_pipeline.py`.
   - Verify zero paid leaks with `python3 project/core/code_reviewer.py --scan-secrets`.
