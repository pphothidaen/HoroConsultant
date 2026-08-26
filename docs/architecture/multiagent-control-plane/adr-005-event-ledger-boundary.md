# ADR-005 — Frozen v3 Ledger and SDLC Control-plane Events

**Status:** Accepted boundary; frozen history is read-only.

## Current facts

The TDD-HORO-v3.0 event ledger defines an append-only execution stream,
17 canonical FSM event types, sequence/hash fields and RFC 8785 JCS hash
chaining
([ledger](../../../TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md#L22-L78)).
It describes replay from ordered events with hash verification before the FSM
reducer
([recovery](../../../TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md#L106-L121)).

## Target decision

- Do not edit, extend, alias or reinterpret the frozen 17-event catalog or its
  historical records.
- Reuse only architectural concepts: canonical JSON/JCS, SHA-256 chaining,
  monotonic sequence, causation/correlation, immutable append and deterministic
  replay.
- Create a separately versioned SDLC control-plane event catalog and stream
  namespace covering commands, execution, approval, leases/fences, evidence,
  effects, outbox and migration. Its event envelope identifies catalog/domain
  explicitly so a control-plane event cannot validate as a v3 domain event.
- Imported legacy evidence remains historical evidence; migration emits new
  import/projection events and never fabricates old canonical events.

## Gate

C1 closed schemas must reject cross-catalog types, unknown fields, invalid JCS,
broken previous hashes, duplicate/out-of-order sequence and replay into another
run/tenant/session. Frozen TDD tests and artifacts remain untouched.

