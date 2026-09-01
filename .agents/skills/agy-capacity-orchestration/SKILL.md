---
name: agy-capacity-orchestration
description: Govern seven-pool AGY/Codex capacity with leases, backpressure, and evidence.
---

# AGY Capacity Orchestration

Use this skill for S3 capacity planning or dispatch preparation across the
seven isolated pools `agy1` through `agy4` and `codex1` through `codex3`. This is a governance
contract. It does not authenticate accounts, invoke providers, change quotas,
or establish runtime proof.

## S3 topology & isolated pools

Each account is an independent quota pool (`codex1`..`codex3`, `agy1`..`agy4`). Never aggregate quota, workers, or
rate limits across aliases.

| Pool | Queue owner | S3 default | Account hard cap | Model role |
|---|---|---:|---:|---|
| `codex1` | Root A (Codex) | 1-2 lanes | Fresh lease and runtime limit | Rank-3 Sol (Architecture/Safety) |
| `codex2` | Root A (Codex) | 1-2 lanes | Fresh lease and runtime limit | Rank-2 Terra/Luna (Feature/Dev) |
| `codex3` | Root A (Codex) | 1-2 lanes | Fresh lease and runtime limit | Rank-2 Terra/Luna (Feature/Dev) |
| `agy1` | Root B (AGY) | 1-2 lanes | 3 parallel sub-agents | Claude Brain (Conductor) / Gemini Worker |
| `agy2` | Root B (AGY) | 1-2 lanes | 3 parallel sub-agents | Claude Brain (Conductor) / Gemini Worker |
| `agy3` | Root B (AGY) | 1-2 lanes | 3 parallel sub-agents | Claude Brain (Conductor) / Gemini Worker |
| `agy4` | Root B (AGY) | 1-2 lanes | 3 parallel sub-agents | Claude Brain (Conductor) / Gemini Worker |

## Alias contract changes

Adding or changing an alias is an atomic compatibility change. Update the
capacity policy, guard constants and fairness records, schemas, fixtures, CI
matrix, and generated agent/skill mirrors together. Never shrink a configured
alias set solely to make a failing CI job green. A narrower exception is valid
only when it is explicitly named, documented, and tested as separate from the
general routing registry.

### AGY Dual-Bucket & Host Preservation Rules
1. **Claude Bucket (Conductor Only):** Dedicated strictly as Orchestrator Brain / Conductor. Never wasted on worker lanes.
2. **Gemini Bucket (Worker Pool):** Primary high-volume worker pool for coding, QA, and deterministic calculations.
3. **Worst-Case Fallback:** Gemini Bucket is used for Orchestrator conduction ONLY when Claude Bucket is exhausted (Tier 4 Red).
4. **Host Account Preservation:** The Orchestrator MUST dispatch worker lanes to other available accounts first, preserving its host account as the last to be exhausted.

Root A sends typed requests to Root B. Root B owns AGY account queues,
worker admission, lease release, and typed responses. Root A must not directly
spawn an AGY worker. A request has one owner, one bounded objective, and a
non-overlapping writable scope; duplicate implementation is rejected.

## Typed request and lease gate

For a governed CLI or bound invocation path, create and validate a
`CapacityRequest` before admission containing:

- request ID, parent/root ID, target pool, owner, objective, and exact scope;
- Rule 18 quality floor, selected model tier, and semantic routing rationale;
- requested lane count, request/token budget, expected evidence, and stop state;
- lease TTL and the required receipt/result contract.

A valid `CapacityLease` is required before that governed path admits its bound
invocation. It binds the request ID, one pool/account, one lane, owner, request
budget, TTL, model floor, and policy version. Per-account burn rate,
circuit-breaker state, and backpressure are separate policy/ledger admission
state, not lease fields. A lease is not an execution receipt and does not prove
that a provider ran. `Invocation.capacity_required=False` is an explicit
programmatic dry-run/legacy optionality; it neither proves provider/runtime
execution nor makes an unbound programmatic path governed admission.

Admission fails closed when the lease is missing, expired, over budget,
already consumed, pool identity differs, ownership overlaps, or the account
quota band is unknown for broad work. Do not renew a lease silently; renewal
requires a fresh safe quota check and the same bounded scope.

## Cost and pressure controls

1. Triage with the cheapest catalog-supported Flash profile first.
2. Select Pro only when the Rule 18 quality floor, evidence burden, or
   unresolved high-impact ambiguity requires it. Never lower the floor to fit
   quota.
3. Count request and token consumption against the lease budget. Monitor burn
   rate against the approved budget and stop admission before exhaustion.
4. Trip a pool-local circuit breaker on quota exhaustion, repeated rate-limit
   or timeout failures, invalid provider events, or missing runtime proof.
   Open circuits do not silently fail over into another account's quota.
5. Apply backpressure by queueing, returning typed `WAIT`/`BLOCKED`, or
   reducing admission to one lane per account. Do not oversubscribe, duplicate,
   or silently downgrade work.

Release unused capacity when a lane ends, fails, or reaches TTL. An expired
lease cannot be used by a queued or running worker. Preserve the request,
lease, circuit, and backpressure state as non-secret operational evidence.

## Quota and evidence truth

User-attested limits are planning inputs only and must be labeled
`user_attested`. Runtime-proven limits require a fresh provider-native status
or execution result, a valid Rule 17 `ExecutionReceipt`, and the typed
`WorkResult`. A configured alias, model label, prompt, dry-run, theoretical
worker count, or copied quota band is not runtime proof.

Preserve Rule 17 ownership, receipt, evidence, and portability boundaries and
Rule 18 quality-floor, decision, and binding requirements. For AGY success,
use the exact evidence language `validated in-process only`; do not claim
portable, offline, or receipt-only verification.

Set `required_human_review=True` for conflict, low-consensus, force-review,
quality-floor, receipt, or evidence-boundary cases. Hold unresolved work until
owner sign-off is recorded. A failed or ambiguous child result is not replaced
by a second implementation from another pool.

## S3, S4, and S5 modes

| Mode | Entry conditions | Required behavior |
|---|---|---|
| `S3` | Fresh safe quota bands, valid leases, no overlap, and Rule 17/18 gates pass | Default 1-2 lanes per account; Flash-first triage; bounded queues and evidence |
| `S4` | Lease pressure, elevated burn rate, backpressure, circuit-open pool, quota near exhaustion, or transient provider failure | Stop new work in the affected pool, drain or queue safely, use one lane only when leased and floor-compatible, and send a typed Root B status to Root A |
| `S5` | Unknown or contradictory quota, invalid receipt/result, quality floor unavailable, repeated circuit failure, ownership conflict, or required HITL | Fail closed; do not spawn or reroute silently; set `required_human_review=True` and hold until owner sign-off |

## Dispatch result and logging

Every bounded lane returns `Status`, `Scope owned`, `Evidence`, `Findings`,
`Changed files`, `Residual risk`, and `Recommended next action`. A successful
AGY result must include the provider-native receipt and typed result; prose is
not a substitute. Use only `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]` in
command-facing logs. Never record secrets, raw provider streams, or account
credentials.
