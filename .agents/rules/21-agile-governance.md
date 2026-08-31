# Rule 21: Agile Governance & Broker Capacity Admission

## Authority and Capacity Truth

Enforce fail-closed Agile lifecycle governance and broker capacity admission.
Distinguish three capacity levels: theoretical capacity (configured ceiling),
policy-admitted capacity (passed quota, isolation, and circuit gates), and
runtime-proven capacity (verified by execution proof). Safe capacity is the
minimum of theoretical, policy-admitted, runtime-proven, host, and ticket counts.

Each alias is an independent pool: do not aggregate, borrow, or infer spare
capacity across aliases. AGY per alias cap 3 is an upper safety bound, not an
availability claim. An alias is unknown without fresh quota proof and isolation
proof. Unknown, stale, or contradictory state fails closed with no silent fallback.

## Six-State Lifecycle and One-Editor Ownership

Tickets transition atomically across six canonical states: `TODO`, `READY`, `DOING`,
`BLOCKED`, `NEEDS_HITL`, and `DONE`. Direct jumps (such as `TODO` to `DONE`) are
forbidden. Enforce strict one editor per resource (one editor per file); concurrent
`DOING` tickets must have disjoint writable paths. All dependency tickets must be `DONE`.

## Definition of Ready (DoR) Gate

A ticket may enter `READY` or `DOING` only after passing Definition of Ready:
1. Test baseline verified (signed provenance reference).
2. Exactly one editor assigned with bounded declared ownership.
3. All dependency tickets in `DONE` status.
4. Verified quota band (healthy or constrained).
5. Closed circuit breaker on allocated broker pool.
6. File permissions verified (0700 home, 0500 wrapper).
7. Valid broker capacity lease ID acquired.
8. Valid Rule 18 model/effort decision.
9. Exact evidence path specified.

## Definition of Done (DoD) Gate

A ticket may enter `DONE` only after passing Definition of Done:
1. Typed `WorkResult` containing all 7 required headings: `Status`, `Scope owned`,
   `Evidence`, `Findings`, `Changed files`, `Residual risk`, `Recommended next action`.
2. Independent QA verdict `PASS`.
3. Independent review verdict `PASS`.
4. Rollback status verified.
5. Capacity classification explicit (theoretical, policy-admitted, runtime-proven).
6. Zero out-of-bounds file modifications.

## Capacity Exceptions and No Fake Busywork

Do not create duplicate work, filler, or no fake full capacity busywork. When
no safe critical-path lane exists, emit typed capacity exception:
`CAPACITY_EXCEPTION: NO_SAFE_CRITICAL_PATH_LANE` (or `NO_SAFE_USEFUL_LANE`) with
snapshot digest and rejected candidate reason codes, leaving the slot unused.
Logs use only `[INFO]`, `[OK]`, `[WARNING]`, `[ERROR]`.
