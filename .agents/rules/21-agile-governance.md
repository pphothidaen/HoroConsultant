# Rule 21: Agile Capacity Governance

## Purpose and authority

Provide a small, fail-closed capacity layer for atomic agile tickets. This
rule preserves Rule 11 as the authority for useful-work scheduling and refill,
Rule 17 for dispatch and execution receipts, Rule 18 for model/effort quality,
and the current fail-closed release policy. It does not authorize a route,
provider, release, fallback, or concurrency increase.

## Evidence boundary and safe cap

The runtime-observed native capacity snapshot is: six concurrent lanes were
admitted; a seventh was denied by the platform agent-thread limit; completion
and refill succeeded. The host snapshot is evidence only, is not capacity
truth, and expires when the environment changes. It is neither theoretical
capacity nor provider capacity.

Set a configurable safety cap no greater than the native observed ceiling.
Admission requires a current capacity snapshot and records only quota and
availability admission evidence; neither proves execution. A lane is proven
only by Rule 17 execution proof and its bound result. Unknown, stale, or
contradictory evidence fails closed; there is no silent fallback.

Each alias is an independent pool: do not aggregate, borrow, or infer spare
capacity across aliases. AGY per alias cap 3 is an upper safety bound, not an
availability claim. An alias is unknown without fresh quota proof and isolation
proof.

## Atomic ticket contract

Use the lifecycle `TODO -> READY -> DOING -> DONE`, with `BLOCKED` and
`NEEDS_HITL` terminal holds. State transitions are atomic and require one
editor per resource, declared ownership, and satisfied dependency evidence.

Definition of ready: a ticket has one owner, bounded scope and exclusions,
dependencies resolved, acceptance evidence, safe-cap admission evidence, and
the applicable Rule 11/17/18 gates.

Definition of done: the result contract contains `Status`, `Scope owned`,
`Evidence`, `Findings`, `Changed files`, `Residual risk`, and `Recommended next
action`; acceptance is evidenced; and the ticket stayed within ownership.

Do not create duplicate work, filler, or no fake full capacity busywork. When
no independently useful, safe ticket is eligible, raise a typed capacity
exception (`CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE`) with the snapshot,
dependency inventory, rejected candidates, and reason codes. A capacity
exception is not `DONE`; replan or hold for the required owner/HITL action.

## Security and release boundary

Never record secret material, credential-store data, or raw provider streams.
Keep provider execution, external actions, and release decisions fail closed
under their existing authorities. Logs use only `[INFO]`, `[OK]`, `[WARNING]`,
or `[ERROR]` tags.
