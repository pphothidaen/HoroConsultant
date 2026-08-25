# Rule 11: Orchestrator Sub-Agent Delegation & Background Work Governance

## Purpose

This rule governs safe, evidence-bearing parallel work. The `orchestrator`
remains accountable for scheduling, user updates, conflict resolution, and the
final decision.

## Eligibility and Scheduling

Before rendering an executable lane, apply Rule 18 and record its versioned
`DispatchDecision`; static role hints are not runtime proof. At each scheduling
checkpoint, exclude tickets that are not `TODO`/`READY`, lack valid `Severity`
or `Work Effort`, have unmet dependencies, an explicit blocker, ownership
conflict, quota/HITL failure, or invalid Rule 18 decision. Missing/invalid
metadata or duplicate IDs fail closed as `BLOCKED: INVALID_SCHEDULING_METADATA`.

Sort only the eligible set by `(-severity_rank, work_effort_rank,
ticket_id_ascii)`: `CRITICAL > HIGH > MEDIUM > LOW`, then `XS < S < M < L <
XL`, then exact ASCII ticket ID. `Work Effort` is delivery size, not model
reasoning effort; model selection never changes the order. Historical
`Priority` is evidence only. Do not preempt `DOING` work.

## Maximum Useful Parallelism

Use available concurrency whenever there are useful, independent,
evidence-bearing lanes. This is a standard, not a requirement to create work:
do not fill slots with redundant, stale, speculative, or dependency-blocked
lanes. A role may have multiple instances and children may create further
bounded lanes, but total active work must stay within the available slot limit.

Decompose to the smallest coherent ownership unit without artificial
fragmentation. Permit one editor per file or module; reserve each selected
lane's ownership, recompute Rule 11 eligibility, then select the next lane.
Reuse a freed slot for the next eligible independent lane (rolling reuse).
For single-file work, prefer one source editor plus a parallel read-only
QA-prep or reviewer lane; final QA and any release verdict wait for source
freeze and every declared dependency.

## Delegation Contract

Every lane must state objective, ownership, boundaries/exclusions, expected
evidence, and stop condition (`DONE`, `BLOCKED`, or `NEEDS_HITL`), and include:

```text
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

No concurrent editors may own the same file or module. Make additional agents
read-only reviewers. Never bypass quota, HITL, dependencies, ownership, or
external-mutation authorization gates. Sub-agents must never print secrets;
unexpected disclosure is a compromise requiring rotation and HITL.

## Monitoring and Results

Announce and maintain live status with active lanes, their ownership, waits or
blockers, and `active/available` slot utilization. Poll only for meaningful
changes. Merge by verified evidence, not seniority or majority.

Each result must contain:

- `Status`: `DONE`, `BLOCKED`, or `NEEDS_HITL`
- `Scope owned`
- `Evidence`
- `Findings`
- `Changed files`
- `Residual risk`
- `Recommended next action`

## Completion Gate

Close a delegated item only when its evidence meets acceptance criteria and its
changes stay within ownership. Close a parent only when every lane is `DONE`
with evidence or `BLOCKED` with the exact operator/HITL action. Local checks
cannot replace pending CI, production, deployment, or live-endpoint evidence.
