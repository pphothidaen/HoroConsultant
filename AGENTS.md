# HoroConsultant — Codex Instructions

## Codex compatibility boundary

- `.agents/` and `.antigravity/` remain the legacy multi-agent configuration. Do not rename, delete, or manually rewrite those definitions for Codex work.
- `.agents/skills/*/SKILL.md` are native Codex skills and are discovered from this repository.
- `.agents/agents/*/agent.json` is the compatibility-layer source. `.codex/agents/*.toml` is generated output and must not be edited manually.
- After changing legacy agent definitions, skills, Claude rules, or routing config, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`. Use `python3 scripts/sync_ai_agent_ecosystem.py --check` for read-only validation.

## Working with Codex subagents

- Decompose work into atomic tasks/tickets (`atomic_tasks.md`), select a matching specialist from `.codex/agents/` / Specialist List, and explicitly bind the required modular skills before dispatching. Unbound dispatches fail closed.
- Generated role prompts preserve legacy responsibilities. Provider/model allocations inside those legacy prompts are historical context; each Codex subagent inherits the active Codex model.
- Keep parallel work isolated by file ownership. Do not assign concurrent agents to edit the same file.

## Project safeguards

- Apply the relevant `.agents/rules/` documents and skills for the task at hand.
- Kaggle synchronization, deployment, publishing, external messages, and secret operations are opt-in: perform them only when the user requests them or the current task requires them.
- Before release claims, run the relevant tests and `python3 scripts/sync_ai_agent_ecosystem.py --check`.
- Plan Completion, Archival & Release Notes Mandate (Core Rule 16 / Rule 22): Whenever all milestones or tickets in an active plan or sprint are executed and verified DONE, archive completed planning artifacts from `plans/` to `plans/archive/YYYY-MM-DD-<sprint-or-release>/`, maintain `/plans/` containing only active/upcoming specifications, and compile/publish `ReleaseNotes.md` with Executive Summary, Architectural Deliverables, Verification Matrix, Milestone Rollup (100% DONE), Live Production Endpoints, and Archived Plans list. Governed by `business_analyst` and `orchestrator`. See `.agents/rules/22-plan-completion-and-release-notes.md`.
