---
name: metaphysical-domain-engine
description: Route 8 metaphysics specialists, then route HITL-conflict cases to human review and finetune data.
responsible_agents:
  - ming_xue_master
  - san_shi_master
  - pu_shi_master
  - xiang_xue_master
  - ze_ji_master
  - numerology_master
  - thai_vedic_master
  - western_astro_master
  - business_analyst
  - hermes
  - orchestrator
  - default
  - devops
owner: orchestrator
responsibility: cross-domain-metaphysics-routing
---

# 🧭 Metaphysical Domain Engine Skill

## Purpose
Route each metaphysical request to the most relevant specialist set and preserve context
across linked traditions.

## Domain Coverage
- Zi Wei Dou Shu
- Qi Men Dun Jia
- Da Liu Ren
- I Ching & Liu Yao
- Xuan Kong & San He
- Ze Ji auspicious-timing
- Thai/Vedic astrology
- Western/Uranian astrology
- Numerology, Tai Yi, Mei Hua, and Mian Xiang

## Coordination Rule
- Prefer one specialist for narrow requests; escalate to 2+ specialists for mixed-domain queries.
- If a cross-domain synthesis is ambiguous (`consensus_score < 0.75`, `conflict_detected`, or `force_human_review`), route to HITL without returning final answer.
- Always include for HITL queue items:
  - `required_human_review`, `conflict_detected`, `conflicting_domains`, `consensus_score`, and `hitl_routing`.
- Before planning implementation, run a scope gate check:
  1. confirm scope boundary and explicit exclusions,
  2. list unresolved requirement assumptions, constraints, and owner approvals,
  3. verify acceptance criteria and rollback condition.
- During execution, enforce HITL gate:
  - For any pending item with `conflict_detected`, `force_human_review`, low consensus (< 0.75), or queued HITL routing, require `required_human_review=True`.
  - Run `GET /hitl/scope-audit?source_domain=metaphysical-domain-engine`.
  - Require `scope-audit.summary.pass_gate_check === true` before implementing or triggering training.
  - If `summary.missing_required_human_gate > 0`, hold model surfacing and trigger; escalate unresolved IDs to `business_analyst` and `hermes` owners.
- Backoffice/model update handoff:
  - only promote HITL-approved items to finetune dataset,
  - keep queue telemetry visible (`pending`, `required_by_domain`),
  - include `scope_domain`, `summary`, and `items` (`required_review_sample`, `conflicts_sample`, `gap_samples`) from scope-audit.
