---
description: Plan completion, plan archival, and ReleaseNotes.md publication mandate.
paths:
  - "plans/**/*"
  - "ReleaseNotes.md"
  - "atomic_tasks.md"
---

# Rule 22: Plan Completion, Plan Archival & Release Notes Publication Mandate

## Purpose and Authority

Enforce clean plan lifecycle management, workspace hygiene, and transparent release documentation.
Authority: Business System Analyst (`business_analyst`) and Master Orchestrator (`orchestrator`).

## Mandatory Triggers

Whenever all milestones and tickets in an active plan or sprint are executed and verified DONE:
1. Archive completed planning artifacts from `plans/` to `plans/archive/YYYY-MM-DD-<sprint-or-release>/`
2. Maintain `/plans/` containing only active/upcoming specifications
3. Compile and publish `ReleaseNotes.md` with:
   - Executive Summary
   - Architectural Deliverables
   - Verification Matrix
   - Milestone Rollup (100% DONE)
   - Live Production Endpoints
   - Archived Plans List
