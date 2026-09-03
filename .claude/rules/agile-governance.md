---
description: Agile governance, broker capacity admission, and AI Studio 3-lane quota orchestration.
paths:
  - ".agents/**/*"
  - ".claude/**/*"
  - ".agy/**/*"
  - "atomic_tasks.md"
  - "plans/**/*"
---

# Rule 21: Agile Governance & Broker Capacity Admission

## Authority and Capacity Truth

Enforce fail-closed Agile lifecycle governance and broker capacity admission.
Distinguish three capacity levels: theoretical capacity (configured ceiling),
policy-admitted capacity (passed quota, isolation, and circuit gates), and
runtime-proven capacity (verified by execution receipt).

## Google AI Studio 3-Lane Quota Orchestration

The system maintains 3 dedicated lanes for Google AI Studio:
- GOOGLE_AI_STUDIO_API_KEY (Lane 1)
- GOOGLE_AI_STUDIO_API_KEY2 (Lane 2)
- GOOGLE_AI_STUDIO_API_KEY3 (Lane 3)

### Orchestrator Conductor Authority

The orchestrator conductor coordinates all work across lanes. Each lane is
granted read/write/update/execute permissions bounded strictly by:
- Active ticket assignment
- Single-editor file ownership
- Dynamic effort assignment by orchestrator for Gemini 3.7 Flash

### Halt & Decide Protocol

On ambiguity or scope overlap between lanes, the orchestrator must immediately
invoke halt & decide. No lane may proceed until the conflict is resolved.

### Non-Disclosing Secret Isolation

- Zero compromised keys in repository history
- 3 distinct keys in .env (never tracked in git)
- Keys are referenced by name only, never by value

## Lifecycle States

- TODO: Initial state
- READY: Approved for work
- DOING: Active implementation (only state allowing source mutation)
- BLOCKED: Awaiting external resolution
- NEEDS_HITL: Requires human-in-the-loop approval
- DONE: Complete and verified

## Single-Editor Ownership

Each writable path is assigned to exactly one ticket. No concurrent edits
to the same path across different tickets.
