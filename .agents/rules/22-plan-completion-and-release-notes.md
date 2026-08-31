# Rule 22: Plan Completion, Plan Archival & Release Notes Publication Mandate

## Purpose and Authority

Enforce clean plan lifecycle management, workspace hygiene, and transparent release documentation.
Authority: Business System Analyst (`business_analyst`) and Master Orchestrator (`orchestrator`).

## Mandatory Triggers

Whenever all milestones and tickets in an active plan or sprint are executed and verified DONE:

1. **Archive Completed Planning Artifacts**:
   - Move completed sprint and task plans from `plans/` into `plans/archive/YYYY-MM-DD-<sprint-or-release>/`.
   - Preserve immutable test provenance records under `plans/test_provenance/`.
2. **Maintain Clean Plans Workspace**:
   - Keep the `/plans/` root directory clean, containing only active or upcoming specifications.
   - Prohibit stale, executed, or obsolete task/sprint plans from lingering in `/plans/`.
3. **Compile, Update, and Publish `ReleaseNotes.md`**:
   - Update repository root `ReleaseNotes.md` containing the full release inventory:
     - **Executive Summary & Highlights**: High-level achievements, metrics, and architecture status.
     - **Architectural Deliverables**: Key modules, computational engines, and refactorings.
     - **Verification Matrix**: Pytest, E2E, UI button regression, secret scan status.
     - **Milestone Rollup (100% DONE)**: Comprehensive list of completed milestones and tickets.
     - **Live Production Endpoints**: Verified container/deployment URLs and live health check status.
     - **Archived Plans List**: Explicit links to archived plan documents for traceability.

## Fail-Closed Release Gate

No plan or sprint may be declared closed, and no release tag or claim may be issued,
until completed plans are archived and `ReleaseNotes.md` is updated and verified.
