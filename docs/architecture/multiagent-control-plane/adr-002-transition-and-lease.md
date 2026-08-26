# ADR-002 — Transitions, Attempts, Leases, and Fencing

**Status:** Accepted target; lease timings are provisional until telemetry.

## Current facts

Current Rule 11 scheduling rejects missing metadata and ownership conflicts,
but selection is a pure snapshot calculation
([ticket model](../../../scripts/multiagent_ticket_scheduler.py#L36-L57),
[selection](../../../scripts/multiagent_ticket_scheduler.py#L378-L404)). A local
dispatch claim and provider/thread ID are not a distributed lease.

## Target decision

- Execution, Approval and Lease are orthogonal state machines. No state implies
  another: `APPROVED` does not mean leased, and a lease does not authorize an
  effect or terminal transition.
- Every command carries `command_id` and `expected_version`. Duplicate IDs
  return the recorded result; version mismatch fails with typed conflict.
- The database allocates `attempt_no` and monotonic `fencing_token`; workers
  cannot choose either. Every worker result/effect proposal binds both.
- Lease acquisition/renewal uses the database clock and atomic compare-and-set.
  A superseded/expired fence can append only a rejection/audit event, never
  mutate canonical execution or effect state.
- Provisional profile: 120-second TTL, renew no later than 40 seconds after
  acquisition/last renewal, and zero grace after database expiry. Tune from
  production-like telemetry before C5 cutover; never silently extend grace.
- Capacity applies independently at global, tenant, provider and alias levels.

## Required negative gates

Reject stale/future expected versions, duplicate non-identical commands,
client-chosen attempts/fences, cross-run leases, late renewals, superseded
workers, approval-as-lease and lease-as-approval. Provider `stream_id`, Codex
thread ID and AGY conversation ID remain correlation metadata only.

