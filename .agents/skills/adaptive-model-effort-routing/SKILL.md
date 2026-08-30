---
name: adaptive-model-effort-routing
description: Assess and record fail-closed model and effort choices for agent lanes.
---

# Adaptive Model and Effort Routing

Use this skill before an orchestrator creates or executes a meaningful
multi-agent lane. It provides the human judgment input for Rule 18; it does
not replace the policy validator, dispatch receipt, quota guard, or HITL.

## Decision workflow

1. State the lane objective, one-editor ownership, exclusions, expected
   evidence, and stop condition.
2. Rank `scope`, `complexity`, `risk`, `ambiguity`, and `evidence` from 0 to 3.
   Use 0 for bounded, deterministic, tool-grounded work and 3 for
   cross-domain, irreversible, security-critical, or materially uncertain work.
3. Set the floor from the highest rank: 0 requires `gpt-5.6-luna` / `low`,
   1 requires `gpt-5.6-luna` / `medium`, 2 requires `gpt-5.6-terra` / `high`,
   and 3 requires `gpt-5.6-sol` / `high`. Rank-3 planning and solution work
   use the cataloged `gpt-5.6-sol` / `xhigh` exception.
4. Select only a provider/model/effort supported by the versioned capability
   catalog. Role metadata is a fallback hint, not effective runtime proof.
5. Record the v1 `DispatchDecision` schema fields: schema version, ticket,
   phase, all five ranks, quota band, work mode, selected alias/model/effort,
   rationale, policy version, root-medium state, and HITL approval. The
   dispatcher derives the normalized decision digest and receipt binding.
6. For execution, require the dispatcher to bind the digest and policy version
   to the route and `ExecutionReceipt`; retain the child `WorkResult` too.

## Non-negotiable gates

- Root planning-to-execution requires fresh proof that root effort is `medium`.
  This does not cap a child lane: the child's independent decision can select
  approved `high` or `xhigh`.
- Critical risk, unresolved high ambiguity, required human review, unsupported
  provider capability, unknown quota for broad work, or a lower-than-floor
  selection is `BLOCKED` or `NEEDS_HITL` before executable dispatch.
- Quota can reroute only to an approved profile at or above the floor. Never
  silently downgrade quality. Below 10% follow the quota handoff rule.
- A rendered route, alias, model label, config, or dry-run is intent only.
  Effective runtime proof requires the bound provider/subprocess receipt and
  child result.
- For `TICKET-ALIAS-RC2-004-QOBS-01`, a local-native QOBS v1 band is planning
  input only and remains non-executable for provider dispatch. Require fresh
  authorization and bound execution evidence before a provider or alias action.

## Provider catalog discipline

Treat the versioned policy catalog as authoritative for provider capabilities:
model availability, supported efforts, fallback order, and deprecation status.
Do not invent capability from a static agent definition. Ask for HITL when the
catalog cannot support the floor or the requested provider override.

## Required output

```text
DispatchDecision: v1
Ranks: scope=?, complexity=?, risk=?, ambiguity=?, evidence=?
Quality floor: ?
Selected profile: provider/model/effort
Quota band: ?
Root medium gate: confirmed | blocked
Decision digest: ?
Status: READY_TO_VALIDATE | BLOCKED | NEEDS_HITL
Rationale and next action: ?
```

Use ASCII log tags in any command-facing report: `[OK]`, `[ERROR]`,
`[WARNING]`, or `[INFO]`. For delegation mechanics and execution proof, apply
`orchestrator-delegation` and `multi-account-agent-orchestration` as well.

## Completion gate

The classification is complete only when all semantic inputs, quality floor,
catalog-compatible selection, root gate, and receipt-binding requirements are
explicit. The dispatcher/hook/QA tickets remain responsible for enforcement.
