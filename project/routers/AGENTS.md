# project/routers - Scoped Agent Instructions

## Scope & Precedence
- Governs FastAPI API routes, request/response models, and endpoint handlers in `project/routers/`.
- Root Universal Safeguards Precedence: Root `AGENTS.md`, `.agents/rules/`, and repository safety mandates strictly supersede this document.
- Separation of Concerns: Router handlers coordinate HTTP lifecycle; calculation logic stays in `project/core/`.
- Rate Limiting: Guard endpoints against volumetric abuse with Redis/memory limiters.

## FastAPI Route Contracts
- Define strict Pydantic v2 schemas for all request bodies, query parameters, and response envelopes.
- Validate all incoming parameters with fail-closed error handling (HTTP 400 / 422).
- Maintain backwards compatibility across API versions (`/api/v2`, `/api/v3`).
- Keep router handlers thin: delegate computational logic to `project/core/` and models to `project/models/`.
- Return structured error responses with standardized error codes and actionable descriptions.
- Enforce CORS policies and security headers on every exposed route endpoint.

## OpenAPI Golden Snapshots
- Ensure OpenAPI schema definitions remain consistent and synchronized with golden snapshots.
- Any intentional route schema change requires regenerating and validating the OpenAPI contract snapshot.
- Block breaking API contract modifications without explicit versioning and migration paths.
- Validate parameter types, defaults, and docstrings in generated schema snapshots.
- Verify schema integrity with automated regression tests before committing route changes.

## Zero-Cost AI Multi-Router Failover
- Implement robust failover cascades across free/zero-cost AI inference tiers (Gemini CLI, Codex, Cloudflare Workers AI).
- Gracefully handle rate limits (HTTP 429), provider timeouts, and upstream outages without user disruption.
- Maintain zero-cost routing invariants: prioritize local and free endpoints before gated providers.
- Log routing decisions and fallback events using pure ASCII telemetry.
- Provide health-check probes and fallback metrics to monitor provider availability.
- Ensure automated fallbacks switch seamlessly without raising unhandled exceptions to callers.
