# ADR-001 — Canonical Authority and Persistence

**Status:** Accepted for target design in the current owner session.

## Current facts

- The scheduler validates caller-supplied ticket snapshots, including copied
  `quota_passed` and `hitl_passed` booleans
  ([scheduler](../../../scripts/multiagent_ticket_scheduler.py#L210-L264)); it
  then uses those values for eligibility
  ([scheduler](../../../scripts/multiagent_ticket_scheduler.py#L361-L375)).
- Dispatch claims are local-process/local-filesystem oriented, including
  `fcntl`, in-memory locks and a six-hour stale threshold
  ([dispatcher](../../../scripts/multiagent_prompt_command.py#L13-L16),
  [dispatcher](../../../scripts/multiagent_prompt_command.py#L186-L192)).
- This is useful compatibility evidence, but it is not multi-host canonical
  state or a transactional event store.

## Target decision

1. PostgreSQL is production canonical authority: transactional append-only
   control-plane event log, current-state projections and outbox in one commit.
2. SQLite WAL is allowed only for local/single-host development and tests; its
   adapter must preserve the same observable domain semantics.
3. The design is multi-host capable. Initial `tenant_id` is the literal
   `system` until authenticated tenant identity exists; adapters may not invent
   tenant identity.
4. Exactly one ControlPlane command handler is the canonical transition writer.
   Workers, providers and transports submit commands/proposals/evidence only.
5. Reducer-authoritative events and projections use closed, platform-neutral
   fields only. Provider/platform values live under a namespaced opaque
   correlation-metadata object; reducers, approval checks, lease allocation,
   fencing, idempotency and capacity decisions must never consult it.
6. C0-C5 requires no Redis, Kafka or NATS. PostgreSQL transactional outbox
   polling plus SSE is sufficient initially. Any later broker requires a new
   narrow ADR and remains notification delivery only, never state, approval,
   lease, fence, attempt or sequence authority.

## Consequences and gate

Every accepted command appends event(s), updates projections and enqueues
outbox row(s) atomically. Recovery replays durable events without chat history
or connection-local caches. C2 cannot close until two schedulers racing the
same work yield one canonical winner and a deterministic replay produces the
same projection.

Schema and adapter QA must reject a canonical field encoded only inside
provider metadata, adapter-specific fields at the canonical root, an adapter
that promotes opaque metadata into a transition input, and any silent field
loss or invented authority proof.
