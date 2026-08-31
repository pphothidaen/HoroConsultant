---
description: Plan completion, plan archival, and ReleaseNotes.md publication mandate.
paths:
  - "plans/**/*"
  - "ReleaseNotes.md"
  - "PROJECT_TASKS.md"
---

# Plan Completion, Archival & Release Notes Mandate

- Whenever all milestones or tickets in an active plan or sprint are executed and verified DONE:
  - Archive completed planning artifacts from `plans/` to `plans/archive/YYYY-MM-DD-<sprint-or-release>/`.
  - Maintain `/plans/` directory clean, containing only active or upcoming specifications.
  - Compile, update, and publish `ReleaseNotes.md` with Executive Summary, Architectural Deliverables, Verification Matrix, Milestone Rollup (100% DONE), Live Production Endpoints, and Archived Plans list.
- Release closure fails closed without verified plan archival and updated `ReleaseNotes.md`.
- Authority: Business System Analyst (`business_analyst`) and Master Orchestrator (`orchestrator`).
