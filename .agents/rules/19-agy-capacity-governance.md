# Rule 19A: S3 Capacity Governance (Five-Pool Dual-Root)

## Purpose

Define balanced S3 capacity governance for the five isolated pools
`codex1`, `codex2`, `codex3`, `agy1`, and `agy2`. This rule complements existing
Rule 19 zero-cost controls and does not replace Rule 17 dispatch/evidence
ownership or Rule 18 adaptive model-effort routing.

## Five-pool dual-root isolation

- Quota, rate limits, leases, burn state, circuit breakers, and queues are
  isolated per account alias. There is no shared or inferred quota pool.
- Root A (Codex) owns `codex1`, `codex2`, and `codex3`, and emits typed
  requests. Root B owns `agy1` and `agy2` account queues and workers, and
  returns typed outcomes; Root A does not directly spawn AGY.
- Each lane has one owner and an exact non-overlapping scope. Duplicate
  implementation is not useful parallelism and is rejected.

## Capacity admission

- For governed CLI and bound invocation paths, a valid `CapacityLease` is
  mandatory before admission. It binds pool/account, request, owner/lane,
  request budget, TTL, model floor, and policy version.
- Per-account burn rate, pool-local circuit-breaker state, and backpressure are
  policy/ledger admission state, not lease fields. Enforce them with the request
  budget and TTL; expired, consumed, over-budget, or mismatched leases fail
  closed. `Invocation.capacity_required=False` is explicit programmatic
  dry-run/legacy optionality, not provider/runtime proof or governed admission.
- AGY is capped at 3 parallel sub-agents per account. Provider nesting max 10
  is an external ceiling only; operational nesting depth is 2-3. Six AGY
  workers is theoretical only and never proves available capacity.
- S3 defaults to 1-2 lanes per account. Admission may reduce to one lane or
  queue work under pressure without lowering the Rule 18 quality floor.

## Cost and quality

Use Flash or another cheap catalog-supported profile for triage first. Use Pro
only when the Rule 18 quality floor or evidence burden requires it. Quota may
reroute only to an approved profile at or above that floor; it may not cause a
duplicate implementation or silent downgrade.

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

Command-facing logs use only `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.
Secrets, credentials, raw provider streams, and unverified quota claims are
never recorded.
