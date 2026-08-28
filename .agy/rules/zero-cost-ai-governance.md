---
description: Enforce zero-cost fail-closed AI routing, quota pooling, and rate limits.
paths:
  - "project/core/ai_provider_router.py"
  - "project/api_router.py"
  - "project/core/rate_limiter.py"
  - "project/core/semantic_cache.py"
  - ".agents/rules/**"
  - ".agents/skills/**"
---

# Zero-Cost AI Provider Governance

- **Zero-Cost Guarantee**: Block all paid providers when `AI_ZERO_COST_ONLY=true`.
- **Project Quota Pooling**: Keys in same Google project share quota. Rotate projects on 429.
- **Circuit Breaker**: Trip 60s cooldown on 429 for 0ms instant bypass on subsequent calls.
- **Rate Limits & Clamping**: Enforce IP/User RPM, daily budgets, <=12k chars, <=1.2k tokens.
- **Deterministic Safe Net**: Fall back to Rust PyO3 engine (<1ms) when free LLMs are exhausted.
