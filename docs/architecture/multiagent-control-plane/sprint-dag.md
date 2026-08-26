# MAREF Checkpoint DAG and Scheduling Freeze

**Scope:** `MAREF-000..057` control-plane refactor.
**C0 verdict:** documentation `DONE — FREEZE PASS`; independent
security/architecture and structural reviews both passed.
**Execution verdict:** `MAREF-010 READY — NW-SESSION-001 CHILD GRANT REQUIRED`;
`MAREF-011+ BLOCKED`. MAREF-010 remains non-executable until its exact native
child is issued; no later contract/source/schema/test lane is eligible.

```text
C0 decisions (000-005)
  -> two independent C0 freeze reviews (PASS)
  -> C1 contracts (010 READY pending exact child; 011-015 BLOCKED)
  -> C2 canonical core (020-025)
  -> C3 adapters/legacy bridges (030-037)
  -> C4 approval + effect Saga (040-044)
  -> C5 shadow/import/reconcile/load/governance/review (050-055)
  -> fresh owner approval -> production cutover (056) -> post-cutover (057)
```

Cross-stream freezes:

- `MAREF-033/034` cannot own dispatcher/scheduler until overlapping QOBS
  dispatcher/scheduler/QA work has frozen and ownership is released.
- `MAREF-042` cannot own `project/hitl_router.py` until
  `TICKET-RELEASE-COMPLETE-20260826-39-ADMIN-HITL-ROUTING`, its mandatory
  metaphysical scope audit/owner sign-off and source QA freeze are complete.
- `MAREF-056` is excluded from the session parent grant and always requires a
  fresh target/session approval after `MAREF-055`.
- MAREF-036 alone owns one bounded `project/main.py` registration hunk;
  MAREF-050 may change only the frozen orchestration bootstrap hunk, never main.
- MAREF-057 live rollback/restoration drill requires its own fresh P4 grant;
  the MAREF-056 cutover grant is not reusable.
- `MAREF-013` freezes EffectLease plus SagaCommand/SagaReceipt before
  `MAREF-041`; `MAREF-052` additionally depends on C2 fault/replay gate 025.
- MAREF-021 owns dependency manifests first; MAREF-035 may touch the same three
  manifests only later, sequentially, and only if optional WS is implemented.
- Compatibility timing starts only after MAREF-057 accepts final authority.

## Authoritative ticket registers

| Checkpoint | Purpose | Register | Current gate |
|---|---|---|---|
| C0 | decisions, CP/AP scope and modular-monolith boundary | [tickets/c0.md](tickets/c0.md) | `DONE — TWO INDEPENDENT REVIEWS PASS` |
| C1 | closed contracts and negative schemas | [tickets/c1.md](tickets/c1.md) | `010 READY — NW-SESSION-001 CHILD REQUIRED; 011-015 BLOCKED` |
| C2 | canonical command/store/lease core | [tickets/c2.md](tickets/c2.md) | `BLOCKED — C1` |
| C3 | platform adapters and bridges | [tickets/c3.md](tickets/c3.md) | `BLOCKED — C2 + legacy freezes` |
| C4 | HITL approval and effect Saga | [tickets/c4.md](tickets/c4.md) | `BLOCKED — C2/C3 + Ticket39` |
| C5 | shadow migration and cutover | [tickets/c5.md](tickets/c5.md) | `BLOCKED — C3/C4` |

## Rule 11 / Rule 18 execution gate

Each ticket register supplies Severity (`CRITICAL/HIGH/MEDIUM/LOW`) and Work
Effort (`XS/S/M/L/XL`) for ordering only. Before any executable lane, the
orchestrator must re-evaluate dependencies, blockers, ownership, session child
grant, QOBS/quota, HITL and a fresh versioned Rule 18 decision. Architecture
planning floor is `gpt-5.6-sol/xhigh`; normal rank-3 implementation/security
floor is `gpt-5.6-sol/high`. Config/model labels are intent, never proof.
The two C0 reviewers returned native collaboration WorkResults; neither result
is claimed as a governed alias/provider ExecutionReceipt. The architecture
handoff alone authorized only plan/reference reconciliation, not
`lifecycle-v1.md` creation. The newer explicit current-session native-fallback
parent waiver `NW-SESSION-001` authorizes separately derived, one-ticket child
grants for `MAREF-010..055` when governed alias execution is unavailable for the
same objective/scope-binding/receipt limitation. It is not itself an execution
grant. Only MAREF-010 is READY, and its planned exact-path child remains
unissued; no lifecycle file or execution result exists.

An issued MAREF-010 native child may supply a native WorkResult without an
alias/provider ExecutionReceipt, but scoped diff/evidence and independent
reviewer `PASS` remain mandatory. After implementation WorkResult `DONE` and
reviewer `PASS`, completion also requires a separately delegated, single-use
local-commit child restricted to the reviewed ticket files/hunks. Never commit
`BLOCKED`/`NEEDS_HITL` or unrelated content; root remains orchestrator-only and
no push is automatic.

One editor owns each exact file/module. An overlapping path, new dirty change,
missing source freeze, invalid metadata, duplicate ticket ID or copied gate
boolean is `BLOCKED`; sorting cannot make it eligible.

The initial package boundary is Domain/Application/Ports/Adapters plus one
composition root and isolated C5 migration modules. PostgreSQL outbox polling
and SSE are sufficient through C5; no broker or internal microservice hop is a
hidden dependency. The design handoff recorded here is not C1 execution
authorization; `NW-SESSION-001` provides only the bounded per-ticket child-grant
route described above and does not imply that any child was issued or run.
