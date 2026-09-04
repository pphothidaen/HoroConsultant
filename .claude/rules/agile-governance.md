---
description: Agile governance, broker capacity admission, and AI Studio 4-lane quota orchestration.
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

## Google AI Studio 4-Lane Quota Orchestration

The system maintains 4 dedicated lanes for Google AI Studio:
- GOOGLE_AI_STUDIO_API_KEY1 (Lane 1)
- GOOGLE_AI_STUDIO_API_KEY2 (Lane 2)
- GOOGLE_AI_STUDIO_API_KEY3 (Lane 3)
- GOOGLE_AI_STUDIO_API_KEY4 (Lane 4)

### Orchestrator Conductor Authority

The orchestrator conductor coordinates work across all lanes. Each lane is
granted read/write/update/execute permissions bounded strictly by:
- Active ticket assignment
- Single-editor file ownership
- Dynamic effort assignment by orchestrator for Gemini 3.7 Flash

### Halt & Decide Protocol

On ambiguity or scope overlap between lanes, the orchestrator must immediately
invoke halt & decide. No lane may proceed until the conflict is resolved.

### Non-Disclosing Secret Isolation

- Zero compromised keys in repository history
- 4 distinct keys in .env (never tracked in git)
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

## Strict Definition of Done (DoD) Mandate

All related jobs, CI/CD, and release notes must be verified, tagged with a release
version referencing ReleaseNotes.md, and all commits/tags pushed to origin/main with
nothing left in local worktree (100% clean and up to date with origin/main).

A ticket, sprint, or release reaches DONE only when all criteria are satisfied:
1. 100% green tests & zero secret leaks (clean test suite and parallel secret scan).
2. Release notes compiled and published referencing all deliverables and verification proofs.
3. Git release tag created referencing ReleaseNotes.md.
4. All commits and tags pushed to `origin/main`.
5. Zero uncommitted/unpushed files left in local worktree ("nothing in local", 100% clean).
