# Project tickets

> **Current ticket index (2026-08-22)**
>
> The authoritative Kanban details live in [`PROJECT_TASKS.md`](PROJECT_TASKS.md). This file is a lightweight navigation/index document so work can be resumed without loading the full historical plan.

## Active release-closure tickets

| Ticket | Status | Immediate next checkpoint |
|---|---|---|
| `TICKET-META-001` | DOING | `CP-01-LOCAL`, then close only after the complete release matrix is green |
| `TICKET-META-005` | BLOCKED | `CP-02-HF` and `CP-03-AZURE` |
| `TICKET-META-006` | BLOCKED | `CP-01-LOCAL`, `CP-04-PW`, then `CP-05-RELEASE` |
| `TICKET-META-008` | NEEDS_HITL | CP-00-DOCS complete; owner actions remain for quota/account handoff; never store secret values |

## Completed implementation tickets

`TICKET-META-002`, `TICKET-META-003`, `TICKET-META-004`, and `TICKET-META-007` remain DONE unless new evidence demonstrates regression.

## Checkpoint contract

Each checkpoint must record owner, scope, command/artifact, timestamp, result, blocker, and next checkpoint. One checkpoint should be completed per work session to reduce quota risk. See the full checkpoint matrix in [`PROJECT_TASKS.md`](PROJECT_TASKS.md#-decoupled-release-closure-checkpoints).

This is a compatibility pointer for workflows that refer to `project_tickets.md`.

The canonical ticket registry and operational handoff are maintained exclusively in [`PROJECT_TASKS.md`](PROJECT_TASKS.md). Do not add or maintain ticket state in this pointer; edit the canonical board instead.

Current plan links and release-gate evidence are listed in the canonical board:

- [`plans/plan.md`](plans/plan.md)
- [`plans/metaphysics_learning_roadmap.md`](plans/metaphysics_learning_roadmap.md)
- [`plans/question_forecast_alignment_spec.md`](plans/question_forecast_alignment_spec.md)
- [`plans/todo_tasks_plan.md`](plans/todo_tasks_plan.md)
