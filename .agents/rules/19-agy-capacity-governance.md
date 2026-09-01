# Rule 19A: S3 Capacity Governance (Seven-Pool Dual-Root)

## Purpose

Define balanced S3 capacity governance for the seven isolated pools
`codex1`, `codex2`, `codex3`, `agy1`, `agy2`, `agy3`, and `agy4`. This rule complements existing
Rule 19 zero-cost controls and does not replace Rule 17 dispatch/evidence
ownership or Rule 18 adaptive model-effort routing.

## Seven-pool dual-root isolation & dual-bucket governance

- Quota, rate limits, leases, burn state, circuit breakers, and queues are
  isolated per account alias (`codex1`..`codex3`, `agy1`..`agy4`). There is no shared quota pool.
- AGY Dual-Bucket Policy: The Claude Bucket (Claude 3.7 Sonnet Thinking / Opus)
  is dedicated for Orchestrator Conduction only; the Gemini Bucket (Flash/Pro) is the primary
  Worker Pool. Fallback to Gemini for orchestration is permitted only in worst-case Claude exhaustion.
- Host Account Preservation: The Orchestrator session MUST consume other available accounts'
  quotas first for worker lanes. The host account is high-priority and preserved as last to exhaust.

## Capacity admission & 4-tier monitoring

- For governed CLI and bound invocation paths, a valid `CapacityLease` is
  mandatory before admission. It binds pool/account, request, owner/lane,
  request budget, TTL, model floor, and policy version.
- Enforce 4-tier adaptive monitoring: Tier 1 (Normal >50%, poll 600s, max 3 lanes),
  Tier 2 (Warning <40%, poll 120s, max 2 lanes), Tier 3 (Critical <20%, poll 30s, max 1 lane, pre-commit),
  Tier 4 (Exhausted <10%/429, auto-handoff to `HANDOFF.md` Rescue Queue and circuit break).
- S3 defaults to 1-2 lanes per account. Admission may reduce to one lane or
  queue work under pressure without lowering the Rule 18 quality floor.

## Cost, quality, and worker routing

Use Gemini Flash for routine worker tasks, QA, and deterministic triage first.
Use Pro/Terra/Sol only when the Rule 18 quality floor requires it. Quota may
reroute only to an approved profile at or above that floor; never silently downgrade.

## Proof and escalation

User-attested limits are planning inputs and must be labeled as such. Only a
fresh runtime result, provider-native receipt, and typed Rule 17 `WorkResult`
prove execution or capacity. Preserve Rule 17 receipt/evidence boundaries and
Rule 18 decision/binding requirements. AGY success is reported as
`validated in-process only`.

- S3 is the default when lease, quota, ownership, and quality gates pass.
- S4 applies to lease pressure, elevated burn, backpressure, quota near
  exhaustion, open circuits, or transient provider failure; stop or queue the
  affected pool and return typed status.
- S5 applies to unknown/contradictory quota, invalid receipt/result, missing
quality floor, repeated circuit failure, ownership conflict, or required
review. Fail closed, set `required_human_review=True`, and hold unresolved
work until owner sign-off.

## Alias contract evolution

When adding, retiring, or renaming an account alias, treat the alias registry
as one atomic contract. Do not remove an alias from a guard or config merely to
make CI pass.

Before merging an alias change, update and verify every affected layer:

1. account/pool configuration and capacity policy;
2. guard constants, admission, fairness, and fail-closed reason logic;
3. JSON schemas, enums, required fields, and fixtures;
4. unit, integration, and CI matrix coverage for every supported alias; and
5. skills, agent instructions, and generated cross-framework mirrors.

An intentionally smaller closed exception is permitted only when its scope is
explicitly named (for example, a one-shot protocol exception), documented with
its distinct alias set, and tested separately from the general routing
registry. It must never silently narrow general CI support.

The merge gate requires a complete alias matrix: each configured alias is
accepted by the intended governed path, rejected by forbidden paths with a
typed reason, and represented consistently in configuration, schemas, and
fixtures. Any mismatch is a contract defect; repair the missing layer rather
than weakening tests or reducing the supported alias set.

Command-facing logs use only `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.
Secrets, credentials, raw provider streams, and unverified quota claims are
never recorded.
