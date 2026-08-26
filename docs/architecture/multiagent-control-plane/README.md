# Multi-agent Control Plane C0 Architecture Freeze

**Status:** C0 documentation `DONE — FREEZE PASS`; independent
security/architecture and structural reviews both passed. MAREF-010 is `READY
— NW-SESSION-001 CHILD GRANT REQUIRED`; MAREF-011+ remains blocked. No alias
executed and no lifecycle file exists.
**Decision date:** 2026-08-26 (Asia/Bangkok)
**Owner approval:** current root session only; see [ADR-004](adr-004-session-scoped-approval.md).

This directory is the planning authority for the `MAREF-000..057` refactor. It
does not change runtime behavior, deploy anything, or reinterpret historical
events. Current behavior and target decisions are deliberately separated.

## C0 release package

- [Requirement Grill report](grill-report.md)
- [Active-platform capability matrix](platform-capability-matrix.md)
- [Checkpoint DAG and scheduling gate](sprint-dag.md)
- [ADR-001: canonical authority and stores](adr-001-canonical-authority.md)
- [ADR-002: transitions, attempts, leases, and fencing](adr-002-transition-and-lease.md)
- [ADR-003: REST/SSE and provider WebSocket boundaries](adr-003-transports-and-openai-websocket.md)
- [ADR-004: session-scoped parent and child grants](adr-004-session-scoped-approval.md)
- [ADR-005: frozen v3 ledger reuse boundary](adr-005-event-ledger-boundary.md)
- [ADR-006: HITL governance and effect Saga](adr-006-hitl-effect-saga.md)
- [ADR-007: legacy compatibility and migration](adr-007-compatibility-and-migration.md)
- [ADR-008: service and deployment boundary](adr-008-service-boundary.md)
- [ADR-CAP-001: Authority Plane and read/notification plane](adr-cap-001-control-agent-plane.md)
- Detailed tickets: [C0](tickets/c0.md), [C1](tickets/c1.md), [C2](tickets/c2.md), [C3](tickets/c3.md), [C4](tickets/c4.md), [C5](tickets/c5.md)

## Gate verdict

`C0 = DONE — FREEZE PASS (documentation evidence only; nine ADRs)`. The
security/architecture and structural native-review WorkResults both report
`PASS`; [C0 evidence](tickets/c0.md) records their reviewed digest set and the
structural totals: 39 rows/IDs, 100 internal edges, zero cycles/missing
dependencies/metadata mismatches/relative-link failures and a clean scoped
diff. The current-session user approval records native-fallback parent waiver
`NW-SESSION-001` for `MAREF-010..055`, usable only through a one-ticket child
grant when governed alias execution is unavailable for the same runtime
objective/scope-binding/receipt limitation. Planned, unissued child
`NW-SESSION-001/MAREF-010/1` is restricted to
`docs/architecture/multiagent-control-plane/contracts/lifecycle-v1.md`, the
lifecycle-contract action, native `business_analyst` intent
`gpt-5.6-sol/xhigh`, a frozen-input scope digest, `max_uses=1`, and this root
session. It accepts no alias/provider ExecutionReceipt but still requires a
native WorkResult, scoped diff/evidence and independent reviewer `PASS`. No
execution has occurred. MAREF-011+, schemas, source, tests and external actions
remain blocked. Static model/config labels remain intent only.

The waiver was recorded at `2026-08-26T12:11:01+07:00` and binds canonical
session `current runtime-enforced collaboration root thread /root`; it invents
no opaque provider/session ID. A completed numbered MAREF-010..055 ticket also
requires a separately delegated, single-use local-commit child after its
implementation WorkResult is `DONE` and independent review is `PASS`. That
commit is exact-ticket files/hunks only; blocked/HITL and unrelated content are
never committed, root stays orchestrator-only, and no push is automatic.

The preserved MAREF-010 runtime blocker is bypassed only by an issued,
single-use native child under `NW-SESSION-001`; the ticket is therefore `READY
— NW-SESSION-001 CHILD GRANT REQUIRED`. Validated decision digest is
`cb2cf84444b699a642969e5fb4be43829d39548b87b66531ab8f87fff5b01d6d`;
snapshot digest
`5611f252f987aef0e6f5c54c0d60e19d0aacce2cc110e5ba3d2989a4934fc39b`
is candidate/non-live. Only read-only/high runtime config is approved; mutation
mode does not enforce it, the objective is arbitrary/unbound CLI text, and
self-declared temporary approval is prohibited. Except for the exact post-PASS
local commit child above, the waiver does not cover MAREF-056/057,
external/production/Git/secret/paid/destructive actions, root implementation,
out-of-ticket tests, force bypass or any other gate, and it expires on a new
root session, `/clear`, or app/control restart. This support-metadata waiver
record is not itself a numbered completion and receives no commit.
