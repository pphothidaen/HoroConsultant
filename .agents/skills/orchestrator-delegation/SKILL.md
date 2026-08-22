---
name: orchestrator-delegation
description: Coordinate sub-agent delegation with ownership, monitoring, result collection, and HITL gates.
---

# Orchestrator Delegation Skill

Use this skill when the user asks the orchestrator to distribute work to sub-agents, run background agent work, coordinate blockers, or collect results from parallel specialist roles.

Primary owner: `orchestrator`. Supporting agents: `business_analyst`, `developer`, `qa_tester`, `devops`, and `code_reviewer`.

## Delegation Contract

The orchestrator remains accountable for the final answer, ticket state, and user-facing decision. Sub-agents provide bounded investigation, implementation, QA, DevOps, review, or documentation results; they do not independently widen scope or mark release gates complete.

Before spawning or assigning work, define:

- Objective: the exact outcome the sub-agent owns.
- Ownership: files, systems, or evidence areas the sub-agent may touch.
- Boundaries: files or external actions the sub-agent must not modify or trigger.
- Evidence: command outputs, artifacts, or concise findings expected back.
- Stop condition: when the sub-agent must report `DONE`, `BLOCKED`, or `NEEDS_HITL`.

Every delegated task must include this coordination sentence:

```text
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

## Role Routing

Choose the narrowest role that matches the work:

- `business_analyst`: requirements, plan/task-board sync, skill/rule governance, handoff documentation.
- `developer`: scoped implementation or code fixes with explicit file/module ownership.
- `qa_tester`: pytest, browser/E2E readiness, failure triage, report extraction.
- `devops`: secrets by name only, deployment workflows, CI/CD, Docker, cloud verification, release evidence.
- `code_reviewer`: safety audit, secret scan, release-readiness risk review.
- Domain masters: metaphysical calculation, interpretation, or validation only when the task is domain-specific.

Do not assign two agents to edit the same file. If multiple agents need the same file, assign one editor and make the others read-only reviewers.

## Background Process Flow

1. Announce the delegation plan to the user with the active agents and ownership.
2. Spawn only concrete, bounded tasks that can progress independently.
3. Continue useful root work while sub-agents run, such as monitoring a primary workflow or validating local evidence.
4. Poll for sub-agent results at natural checkpoints, not in a tight loop.
5. Merge results by evidence, not by majority. If two agents conflict, inspect the underlying commands/logs before deciding.
6. Update `PROJECT_TASKS.md`, release handoff docs, or plan files only after the evidence is stable and the user has authorized any required external action.

## External Action Guardrails

Sub-agents may investigate external systems when the user placed them in scope. They must not perform high-impact external writes unless the root orchestrator or user explicitly authorized the exact class of action.

Examples requiring explicit authorization before execution:

- Publishing or uploading payloads to Hugging Face, Vercel, Azure, Docker Hub, or similar platforms.
- Creating, rotating, or syncing secrets in Doppler, GitHub Actions, or cloud providers.
- Pushing commits to `main`.
- Running production browser tests with sensitive or user-like payloads.

Secrets must never be printed. Prefer commands that pipe secrets directly between tools. If any tool prints a secret value, immediately treat that value as compromised, stop using it, and require rotation before further propagation.

## Result Collection Format

Ask sub-agents to report in this shape:

```text
Status: DONE | BLOCKED | NEEDS_HITL
Scope owned:
Evidence:
Findings:
Changed files:
Residual risk:
Recommended next action:
```

For long logs, require concise snippets with job id, step name, timestamp, and the exact error message. Do not paste full logs unless the full content is necessary and free of secrets.

## Completion Rules

The orchestrator may mark a delegated item `DONE` only when:

- The assigned evidence exists and matches the acceptance criteria.
- Any changed files are within the assigned ownership.
- Required checks have passed or a documented waiver exists.
- No external gate is being inferred from local-only results.

Mark the item `BLOCKED` when the same external permission, credential, service availability, or human decision is required and no safe in-scope action remains. Provide the exact next human/operator command or decision needed.
