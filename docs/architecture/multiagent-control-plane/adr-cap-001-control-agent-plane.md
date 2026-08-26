# ADR-CAP-001 — Authority Plane and Read/Notification Plane

**Status:** Accepted target semantics; no runtime or deployment authorization.

## Current facts

Current ticket snapshots, local claims, provider streams and chat SSE are useful
compatibility/read evidence, but none is a multi-host transactional authority.
The target must therefore distinguish authoritative state from eventually
consistent delivery instead of treating “control plane” as one consistency
class.

## Target decision

The **Authority Plane** is CP under partitions. PostgreSQL plus the sole
ControlPlane command handler owns canonical events/transitions, approvals,
leases/fences, attempts, idempotency, capacity, effects and release authority.
The **Read/Notification Plane** may be eventually consistent: projections,
outbox polling, SSE clients and sanitized caches may lag, reconnect or replay.
Providers and notification transports never become authority.

The partition law is exact and fail-closed:

> **No Authority -> No Mutation -> No New Lease -> No New Approval -> No Blind Retry**

Existing valid work may only finish through the authority path with current
version, grant, attempt and fence. An unknown external effect enters durable
reconciliation; it is not retried merely because a connection failed.

## Staleness and API contract

Every read that can be stale discloses `stale`, `as_of_version` or
`projection_version`, `last_event_id` or sequence, `authority_epoch`, `read_at`
and measured/typed lag. A caller cannot use a stale projection, notification
cursor or provider ID as a transition precondition.

Required baseline HTTP semantics:

| Status | Meaning |
|---|---|
| `503` | Authority unavailable, or requested freshness cannot be met |
| `409` | CAS/version conflict or stale/superseded fence |
| `403` | Invalid, revoked, exhausted, mismatched or session-expired approval |
| `202` | Command durably accepted by the Authority Plane; never queue-memory-only acceptance |
| `429` | Capacity/rate limit reached; response is not permission to bypass or retry blindly |

`428 Precondition Required` or `423 Locked` may be added later as optional HTTP
mappings, but they cannot replace or weaken the required baseline above.

## Acceptance gate

Contract/API/conformance tests must prove partition rejection, disclosed stale
reads, durable-before-202 acceptance, typed unknown-effect reconciliation and
that notification/provider reconnect cannot mint state, approval, lease,
attempt, fence, sequence or authority epoch.
