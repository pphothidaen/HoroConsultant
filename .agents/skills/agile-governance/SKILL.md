---
name: agile-governance
description: Govern atomic agile tickets, multi-lane capacity leases, and safe concurrent admission.
---

# Agile Governance

Use this skill for a ticket-level capacity decision. Rule 21 is the concise
policy; consult Rules 11, 17, and 18 only for scheduling, receipt, or routing
details respectively. Their authority and the current fail-closed release
policy remain unchanged.

## Admit a lane

1. Confirm `TODO` or `READY`, one editor per resource, bounded ownership,
   dependencies, definition of ready, and useful non-duplicative work.
2. Use a configurable safety cap at or below the native observed ceiling. The
   recorded runtime observation is six admitted native lanes, a platform-denied
   seventh, and successful completion/refill. Host facts are evidence only and
   expire when the environment changes; they are not theoretical capacity or
   provider capacity.
3. Treat quota and availability as admission evidence only. They are not
   execution proof. Keep independent pools; no aggregation. AGY per alias cap
   3 is only an upper bound. Mark an alias unknown without fresh quota proof
   and isolation proof. On uncertainty, fail closed with no silent fallback.

## Run and close

Use the Rule 11 dispatcher loop for completion/refill. Preserve Rule 17’s
bound execution receipt and result contract, and Rule 18’s quality floor.
Move only atomically through `TODO`, `READY`, `DOING`, `BLOCKED`, `NEEDS_HITL`,
or `DONE`. Definition of done requires the complete result contract:
`Status`, `Scope owned`, `Evidence`, `Findings`, `Changed files`, `Residual
risk`, and `Recommended next action`.

Never manufacture work to fill a slot. If no safe, independent, ready ticket
exists, emit `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE` with snapshot,
ownership/dependency inventory, rejected candidates, and typed reasons. The
capacity exception is not completion; replan or hold for owner/HITL action.

## Safe reporting

Use only `[INFO]`, `[OK]`, `[WARNING]`, and `[ERROR]` log tags. Do not include
secret material, credential-store data, or raw provider streams. Do not claim
admission evidence proves execution or release readiness.
