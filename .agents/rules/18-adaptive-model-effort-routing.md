# Rule 18: Adaptive Model and Effort Routing

## Purpose

Make every executable multi-agent lane use an auditable, quality-preserving
model and reasoning-effort decision. This rule governs classification and its
contract; the versioned policy and dispatcher are the enforcement authority.

## Required `DispatchDecision` (v1)

Before rendering an executable lane, the orchestrator records the v1 schema
fields: `schema_version`, `ticket`, `phase`, the five semantic ranks
(`scope_rank`, `complexity_rank`, `risk_rank`, `ambiguity_rank`, and
`evidence_burden_rank`), `quota_band`, `work_mode`, `selected_alias`,
`selected_model`, `selected_effort`, `rationale`, `policy_version`,
`planning_to_medium_confirmed`, and `hitl_approved`. A `quality_exception` is
allowed only for catalog-supported `max` or `ultra` selections. The dispatcher
derives the normalized decision digest; the execution receipt binds that
digest, policy version, actual model/effort, route identity, and normalized
result digest. Missing, changed, or mismatched bindings fail closed.

## Assessment and quality floor

Rank each semantic input from 0 (bounded/tool-grounded) to 3
(cross-domain, irreversible, or safety-critical). The maximum of the five
ranks establishes the minimum quality floor; quota may choose another approved
provider only at or above that floor, never silently downgrade it.

| Maximum rank | Minimum profile | Typical lane |
|---|---|---|
| 0 | `gpt-5.6-luna` / `low` | one fact/file, mechanical read-only work |
| 1 | `gpt-5.6-luna` / `medium` | bounded module, standard/reversible work |
| 2 | `gpt-5.6-terra` / `high` | multi-module, novel, security/schema/data/CI work |
| 3 | `gpt-5.6-sol` / `high` | cross-system/domain, high-impact or release evidence |

Rank-3 planning, architecture, solution discovery, and ticket synthesis use
the cataloged `gpt-5.6-sol` / `xhigh` exception; normal rank-3 executable
lanes require `high` unless a catalog-supported quality exception is recorded.

The policy catalog is the sole provider-capability authority. It must list
providers, models, supported efforts, availability status, and fallback order;
unlisted pairs or provider-specific unsupported efforts are rejected.

## Mandatory gates

- Static role metadata and rendered routes are default hints, never proof of
  effective runtime model, effort, provider, or execution.
- The root planning-to-execution gate requires a fresh owner-confirmed
  `medium` root effort. It is independent of the selected child lane, which
  may require `high` or `xhigh` under its own decision.
- Critical risk, unresolved high ambiguity, required human review, unknown
  quota for broad work, provider mismatch, or an attempt to reduce the floor
  is `NEEDS_HITL`/`BLOCKED` before execution.
- Quota is a planning input, not a quality exception. Record only a safe band;
  below 10% stops broad work under the quota handoff rule.

## Overrides and proof

Overrides may strengthen a valid decision only when supported by the catalog
and recorded with rationale. They must not weaken model, effort, capability,
or receipt binding. Prompt text, config, model labels, aliases, and dry-runs
are intent only. Effective runtime proof is the bound subprocess/provider
receipt plus the child `WorkResult`.

## Handoff and completion

The orchestrator supplies the semantic assessment and decision; the dispatcher
revalidates it immediately before process creation; the hook adds defense in
depth without duplicating scoring; QA tests reject bypasses. See
`adaptive-model-effort-routing` and Rules 11 and 17. This rule stays below the
Rule 14 single-concern size limit.

## Completion Gate

Close an executable lane only when a valid decision, provider-compatible route,
bound receipt, and child result agree. Otherwise return a typed blocker or
HITL action; never infer success from static configuration or prose.
