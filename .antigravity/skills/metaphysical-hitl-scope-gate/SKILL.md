---
name: metaphysical-hitl-scope-gate
description: Validate metaphysical boundary, ambiguity, and conflict risk gates for HITL review.
---

# Metaphysical HITL Scope Gate

Enforce fail-closed human-in-the-loop review for boundary, ambiguity, and conflict conditions.

## Purpose

Detect metaphysical risk conditions in consultation charts and enforce certified human
master review before releasing autonomous interpretations or predictions.

## Risk Triggers

The HITL scope gate halts autonomous output and triggers `required_human_review=true` when:
1. **Boundary Hour Conditions**:
   - Birth recorded exactly at solar boundary transitions (e.g. 23:00 Zi hour transition).
   - Equinox/solstice border timestamp ambiguity.
2. **Severe Chart Conflict**:
   - Clashing heavenly stems and earthly branches (e.g. Fan Yin, Fu Yin, Six Clashes).
   - Extreme elemental imbalance lacking clear mediating factors.
3. **Low Consensus & Ambiguity**:
   - Multi-tradition consensus score `< 0.75`.
   - Conflicting traditional text interpretations.
   - User or operator `force_human_review` flag set.

## Scope Audit Receipt Contract

Every gate evaluation must emit a structured audit receipt containing:
- `source_domain`: Must be `metaphysical-domain-engine`.
- `required_human_review`: Boolean flag (`true` when triggers met).
- `pass_gate_check`: Boolean flag (`false` when review required, `true` only when verified).
- `auditor_role`: Distinct auditor role signature.
- `owner_sign_off`: Explicit recorded human master approval.

## Protocol Workflow

1. Evaluate consultation inputs against boundary hour, harmony, and consensus rules.
2. If any risk trigger fires:
   - Halt autonomous prediction generation fail-closed.
   - Emit audit receipt with `required_human_review=true` and `pass_gate_check=false`.
   - Queue case for certified master review.
3. If all criteria pass cleanly:
   - Emit audit receipt with `pass_gate_check=true`.
4. Status reporting:
   - `[OK]`: Gate passed without risk triggers.
   - `[ERROR]`: Gate blocked; human review required.
   - `[WARNING]`: Borderline harmony score detected.
   - `[INFO]`: Scope audit receipt generated.

## Gotchas

- Must bind `source_domain=metaphysical-domain-engine`.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
