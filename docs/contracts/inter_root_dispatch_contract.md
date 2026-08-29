# HITL-1 Inter-root RootA -> RootB Dispatch Contract

Status: local contract only; verified during HITL-2 policy freeze. This document
defines the wire boundary for a future dispatcher; it does not authorize, activate, or prove dispatch.

## 1. Boundary and ownership

RootA is the primary coordinator. It creates one bounded typed request,
validates the returned typed response, and owns the caller-facing result.
RootB is the secondary coordinator. It owns the target AGY pool queue, worker
admission, reservation and lease lifecycle, and aggregate response. RootA must
not directly spawn an AGY worker.

The request is bound to exactly one isolated pool: `agy1` or `agy2`. The frozen
RootB mapping is `primary -> agy1` and `secondary -> agy2`; a role cannot select
the other account. Pool,
account, and provider are one immutable binding; quota or workers cannot be
borrowed from another pool. A primary/secondary role describes the two roots,
not a permission to fail over. There is no implicit secondary pool.

This is a HITL-1 contract and every example has `activation_prohibited: true`.
An implementation MUST reject an activation attempt while that value is true.
The examples are deterministic fixtures only and MUST NOT invoke a provider,
network, account, queue worker, or dispatcher process.

## 2. Typed request

`DispatchRequest` is a closed object with these fields:

| Field | Type and rule |
|---|---|
| `contract` | exactly `horoconsultant.inter-root-dispatch` |
| `protocol_version` | integer `1` |
| `hitl_stage` | exactly `HITL-1` |
| `activation_prohibited` | boolean, exactly `true` for this contract |
| `request_id` | non-empty ASCII identifier, unique per attempt |
| `idempotency_key` | non-empty ASCII key, stable for one logical attempt |
| `attempt` | integer, at least `1`; a retry increments it |
| `source` | `{root_id: RootA, role: primary, account: codex1\|codex2, pool: same account, provider: codex}` |
| `target` | `{root_id: RootB, role: secondary, account: agy2, pool: agy2, provider: agy}` |
| `objective` | one bounded objective string |
| `scope` | non-empty exact writable-scope list; no overlap is implied |
| `reservation` | required reservation handle, bound to `request_id`, target pool, owner, lane, and TTL |
| `lease` | required capacity lease handle, bound to the same request, pool, owner, budget, TTL, quality floor, and policy version |
| `provider_state` | one of `known`, `unknown`; `unknown` forces `S5` |
| `mode` | one of `S3`, `S4`, `S5` |
| `evidence_boundary` | exactly `validated_in_process_only` |

`source` and `target` are closed bindings. `source.pool == source.account` and
`target.pool == target.account`; RootA is always `primary`, RootB always
`secondary`. The request is rejected if a lease is absent, expired, consumed,
over budget, or mismatched. A reservation precedes a lease; a lease does not
prove provider execution.

## 3. Typed response

`DispatchResponse` is a closed object with these fields:

| Field | Type and rule |
|---|---|
| `contract`, `protocol_version`, `hitl_stage`, `activation_prohibited` | exactly the request values |
| `request_id`, `idempotency_key`, `attempt` | exactly the request values |
| `source`, `target` | exact binding echoed from the request |
| `status` | `QUEUED`, `DRAINING`, `BLOCKED`, `DONE`, or `REJECTED` |
| `mode` | `S3`, `S4`, or `S5` |
| `provider_state` | `known` or `unknown` |
| `required_human_review` | boolean; true for S5 or unresolved evidence |
| `reservation` | typed reservation outcome, never a provider receipt |
| `lease` | typed lease outcome, never a provider receipt |
| `result` | typed `WorkResult` summary or `null` when no work ran |
| `receipt` | provider-native receipt or `null`; no local summary may impersonate it |
| `evidence_boundary` | exactly `validated_in_process_only` |

`DONE` requires a provider-native receipt and typed `WorkResult`; a local
response, lease, queue event, copied quota band, or prose summary is not proof
that a provider ran. RootB returns no raw provider stream, credentials,
secrets, account-home paths, or unsanitized exception text. RootA may accept a
receipt only after revalidating all request, binding, lease, reservation,
policy, and digest relationships.

## 4. Reservation, lease, retry, and idempotency

Reservation is the queue admission record. It is immutable for the attempt and
contains `reservation_id`, `request_id`, `pool`, `owner`, `lane`, `reserved_at`,
and `expires_at`. The capacity lease is the worker admission record and adds a
bounded request budget, quality floor, policy version, and lease digest.

The idempotency key is checked before creating either record. A duplicate key
with the same request fingerprint returns the original response without a new
reservation, lease, queue item, retry, or provider action. The same key with a
different fingerprint is `REJECTED` with a typed conflict.

A retry is a new attempt with a new `request_id`, reservation, lease, and
idempotency key (`<logical-key>:retry:<attempt>`). It requires a fresh
reservation and fresh lease; it cannot reuse an expired/consumed lease, revive
a drained item, switch pools, lower the quality floor, or silently fail over.

## 5. Queue and drain rules

`S3` admits only with fresh quota state, a valid non-overlapping reservation,
and a valid lease. `S4` is pool-local pressure or transient failure: stop new
work in that pool, retain queued work as `QUEUED` or return `DRAINING`, release
unused capacity, and never admit a worker without a live lease. Draining does
not transfer work to another pool.

`provider_state == unknown` is always `mode == S5`, `status == BLOCKED` or
`REJECTED`, and `required_human_review == true`. S5 is fail-closed: no queue
drain, retry, reroute, lease renewal, worker spawn, or provider invocation may
occur until the owning human review is recorded. Unknown never sorts into an
executable queue.

## 6. Evidence and receipt boundaries

Local validation proves only shape, binding, idempotency, reservation/lease
relationships, and deterministic state transitions. It does not prove quota,
account capacity, provider identity, provider execution, model quality, or
external side effects. Provider proof, when separately authorized, requires a
provider-native receipt plus typed `WorkResult`; both remain bound to the exact
attempt and are validated in-process only. No example in this document is a
receipt of execution.

## 7. Machine-readable examples

The following JSON objects are closed fixtures consumed by
`tests/test_inter_root_dispatch_contract.py`.

### Valid queued request

```json
{
  "contract": "horoconsultant.inter-root-dispatch",
  "protocol_version": 1,
  "hitl_stage": "HITL-1",
  "activation_prohibited": true,
  "request_id": "req-20260828-001",
  "idempotency_key": "roota:case-001:attempt-1",
  "attempt": 1,
  "source": {"root_id": "RootA", "role": "primary", "account": "codex1", "pool": "codex1", "provider": "codex"},
  "target": {"root_id": "RootB", "role": "secondary", "account": "agy2", "pool": "agy2", "provider": "agy"},
  "objective": "Review the frozen contract test evidence",
  "scope": ["tests/test_inter_root_dispatch_contract.py"],
  "reservation": {"reservation_id": "res-001", "request_id": "req-20260828-001", "pool": "agy2", "owner": "RootB", "lane": 1, "reserved_at": 1000, "expires_at": 1060},
  "lease": {"lease_id": "lease-001", "request_id": "req-20260828-001", "pool": "agy2", "owner": "RootB", "request_budget": 1, "requests_used": 0, "expires_at": 1060, "model_quality_floor": "flash", "policy_version": "s3-1"},
  "provider_state": "known",
  "mode": "S3",
  "evidence_boundary": "validated_in_process_only"
}
```

### Valid queued response

```json
{
  "contract": "horoconsultant.inter-root-dispatch",
  "protocol_version": 1,
  "hitl_stage": "HITL-1",
  "activation_prohibited": true,
  "request_id": "req-20260828-001",
  "idempotency_key": "roota:case-001:attempt-1",
  "attempt": 1,
  "source": {"root_id": "RootA", "role": "primary", "account": "codex1", "pool": "codex1", "provider": "codex"},
  "target": {"root_id": "RootB", "role": "secondary", "account": "agy2", "pool": "agy2", "provider": "agy"},
  "status": "QUEUED",
  "mode": "S3",
  "provider_state": "known",
  "required_human_review": false,
  "reservation": {"reservation_id": "res-001", "state": "ACTIVE"},
  "lease": {"lease_id": "lease-001", "state": "ACTIVE"},
  "result": null,
  "receipt": null,
  "evidence_boundary": "validated_in_process_only"
}
```

### Unknown provider state, fail-closed S5 response

```json
{
  "contract": "horoconsultant.inter-root-dispatch",
  "protocol_version": 1,
  "hitl_stage": "HITL-1",
  "activation_prohibited": true,
  "request_id": "req-20260828-002",
  "idempotency_key": "roota:case-002:attempt-1",
  "attempt": 1,
  "source": {"root_id": "RootA", "role": "primary", "account": "codex1", "pool": "codex1", "provider": "codex"},
  "target": {"root_id": "RootB", "role": "secondary", "account": "agy2", "pool": "agy2", "provider": "agy"},
  "status": "BLOCKED",
  "mode": "S5",
  "provider_state": "unknown",
  "required_human_review": true,
  "reservation": {"reservation_id": "res-002", "state": "HELD_NO_EXECUTION"},
  "lease": {"lease_id": "lease-002", "state": "NOT_ADMITTED"},
  "result": null,
  "receipt": null,
  "evidence_boundary": "validated_in_process_only"
}
```
