# Rule 19: Zero-Cost Multi-Tier AI Provider Governance

## Purpose

Enforce a fail-closed, $0 zero-cost guarantee across all AI provider routing,
quota pooling, circuit breakers, rate limits, and fallback execution.

## Core Mandates

1. **Zero-Cost Fail-Closed Enforcement**:
   When `AI_ZERO_COST_ONLY=true`, all paid API endpoints (OpenAI Direct API,
   Vertex AI Paid, Claude API) MUST be blocked at the class abstraction level.
   If all free capacity is exhausted, the system MUST return HTTP 429 or fall
   back to the deterministic Rust PyO3 engine. Never fall back to paid routes.

2. **Project-Level Quota Pooling**:
   Multiple API keys in the same Google Cloud Project share one quota pool.
   Routers MUST distinguish:
   - **Key Redundancy**: Rotate keys within the same project on 401/403 auth errors.
   - **Quota Rotation**: Rotate across distinct projects (Project A -> B -> Cloudflare) on 429 errors.

3. **In-Memory Circuit Breaker**:
   When any provider hits a 429 rate limit, trip its circuit breaker for 60s.
   Subsequent requests MUST immediately bypass the exhausted provider (0ms latency).

4. **Multi-Tier Rate Limiting & Input Clamping**:
   - IP limit (10 RPM), User limit (20 RPM), Daily Budget (40-150 req/day).
   - Clamp prompt input to <= 12,000 characters and max output tokens to <= 1,200.

5. **Deterministic Safe Net**:
   When all free LLMs are unavailable, invoke Rust PyO3 calculation engine
   to deliver deterministic astrological interpretations (<1ms, $0 cost).
