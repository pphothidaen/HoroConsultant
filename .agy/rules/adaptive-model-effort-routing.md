---
description: Require an auditable model and effort decision before agent dispatch.
paths:
  - "PROJECT_TASKS.md"
  - "plans/**"
  - ".agents/rules/**"
  - ".agents/skills/**"
  - "docs/templates/**"
  - "scripts/multiagent_prompt_command.py"
  - ".claude/hooks/**"
---

# Adaptive model and effort routing

Before executable multi-agent dispatch, create a v1 `DispatchDecision` with
ticket/phase, lane ownership, semantic ranks for scope, complexity, risk,
ambiguity, and evidence, a non-secret quota band, selected provider/model/
effort, quality floor, policy version, root-medium state, rationale, and
decision digest.

The highest semantic rank sets the minimum quality profile. Quota may reroute
only to a catalog-approved equal-or-stronger profile; it never silently lowers
quality. Critical risk, high unresolved ambiguity, required human review,
unknown quota for broad work, unsupported capability, missing digest, or an
unconfirmed root-medium gate must block executable dispatch or require HITL.

Static agent metadata, aliases, rendered commands, and dry-runs are hints or
intent, not effective runtime proof. Bind policy version and decision digest to
the actual route, receipt, and child result. The hook is defense in depth; the
policy/dispatcher remains authoritative. See Rule 18 and the specialist skill.
