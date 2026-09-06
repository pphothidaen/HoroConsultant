---
name: metaphysical-domain-engine
description: Compatibility router for deterministic request routing, HITL gate, and finetune handoff.
owner: orchestrator
sunset: Sunset upon full migration to focused metaphysical skills in v2.0.0; no focused-profile activation.
---

# Metaphysical Domain Engine Compatibility Router

Workflow-free compatibility router delegating to focused metaphysical architecture skills.

## Governance and Metadata

- **Owner**: `orchestrator`
- **Sunset Condition**: Retained strictly for backwards-compatible routing; scheduled for sunset in v2.0.0 after full migration to focused metaphysical skills.
- **Activation Restriction**: No focused-profile activation permitted; this is a workflow-free router.
- **Source Domain**: All operations require `source_domain=metaphysical-domain-engine`.

## Mandatory HITL Gate Rule

Any condition involving ambiguity, solar boundary hour, severe chart conflict, low consensus (< 0.75), force review, or training promotion strictly binds a validated HITL audit plus owner sign-off before implementation or training handoff. Calculation, training, and API behavior must remain unaltered.

## Routing Targets

Inquiries and tasks mapped to this router are forwarded to the appropriate focused skill:

1. **`metaphysical-request-router`**:
   - Routes inquiries to deterministic calculation engines (`project/core/bazi.py`, `project/core/suriyayart.py`, etc.).
   - Decomposes multi-tradition inquiries and forbids LLM prose hallucination of astronomical facts.

2. **`metaphysical-hitl-scope-gate`**:
   - Evaluates boundary conditions, chart conflicts, and consensus scores.
   - Emits structured scope audit receipts requiring human review when risk thresholds fire.

3. **`metaphysical-finetune-handoff`**:
   - Enforces the distillation quality checklist and PII redaction for fine-tuning datasets.
   - Requires confirmed master approval before dataset promotion.

## Reporting Protocol

- All status reports from routed tasks must use pure ASCII logs only:
  - `[OK]`: Sub-task routed and verified.
  - `[ERROR]`: Routing failure or target contract breach.
  - `[WARNING]`: Compatibility router invoked instead of direct focused skill.
  - `[INFO]`: Delegation target identified.
