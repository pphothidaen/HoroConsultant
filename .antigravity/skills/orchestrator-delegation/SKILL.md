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

## Standard Delegation Round

When the user asks to "กระจายงาน", "run background agents", "continue until done", or "ตรวจสอบ plans/project tasks", start with this default split unless the task is smaller:

| Lane | Sub-agent | Ownership | Default stop condition |
|---|---|---|---|
| BSA/status | `business_analyst` | `PROJECT_TASKS.md`, `plans/**`, governance docs, skill/rule catalog | `DONE` when task board and plan state match verified evidence; `BLOCKED` when evidence is missing |
| DevOps/release | `devops` | `.github/workflows/**`, deployment scripts, cloud workflow logs, secret names only | `DONE` when workflow/deployment evidence is green; `NEEDS_HITL` for credentials, platform permissions, billing, or production approval |
| QA/evidence | `qa_tester` | pytest, API contract, UI regression, Playwright readiness and reports | `DONE` when pass/fail evidence is captured; `BLOCKED` when live backend/browser/authorization is unavailable |
| Implementation | `developer` | explicitly assigned source/test modules only | `DONE` when patch and targeted tests pass; `BLOCKED` when file ownership overlaps or product decision is missing |
| Safety review | `code_reviewer` | secret scan, safety audit, release-readiness review | `DONE` when scan/audit evidence supports closure; `NEEDS_HITL` when a leaked secret or unsafe release condition remains |

The root orchestrator should continue integration work while sub-agents investigate. Merge by evidence, not by role seniority or majority.

## Claude Code Three-Level Governance

When the user asks to adapt delegation into Claude Code prompts, apply this structure:

1. **Hooks (`.claude/settings.json`) are hard constraints.** Use them for critical blocks such as secret-file reads, destructive deletion, force push, and other pre-tool safety controls.
2. **Rules (`.claude/rules/*.md`) are context-aware.** Load narrow rules by path or workstream to avoid context overload.
3. **`CLAUDE.md` is global baseline context.** Keep it short, stable, and limited to project identity, primary commands, and links to detailed rules/skills.

Do not put hard safety controls only in `CLAUDE.md`; if an action must be blocked before reasoning, put it in hooks.

## Background Process Flow

1. Announce the delegation plan to the user with the active agents and ownership.
2. Spawn only concrete, bounded tasks that can progress independently.
3. Continue useful root work while sub-agents run, such as monitoring a primary workflow or validating local evidence.
4. Poll for sub-agent results at natural checkpoints, not in a tight loop.
5. Merge results by evidence, not by majority. If two agents conflict, inspect the underlying commands/logs before deciding.
6. Update `PROJECT_TASKS.md`, release handoff docs, or plan files only after the evidence is stable and the user has authorized any required external action.

## Claude Code Governance Mapping

When the user asks to apply this delegation model to Claude Code, map controls into three layers:

1. **Hard constraints**: `.claude/settings.json` hooks, especially `PreToolUse`, block critical actions before the model decides to proceed. Use this for secret-file reads, plaintext token output, force pushes, recursive destructive deletes, and production-impacting operations that must require explicit authorization.
2. **Context-aware rules**: `.claude/rules/*.md` files use frontmatter `paths` to scope instructions to relevant source areas. Split API, frontend, testing/release, secrets/devops, and orchestrator/sub-agent guidance so routine tasks do not overload context.
3. **Global context**: `.claude/CLAUDE.md` or root `CLAUDE.md` stays short and project-wide. Keep only operating priorities, generated-file boundaries, release-truth requirements, and the standard sub-agent result contract.

For practical prompt examples, use `docs/CLAUDE_CODE_COMMAND_GOVERNANCE.md`.

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

## Prompt Examples

### Root orchestrator prompt

```text
Apply HoroConsultant orchestrator-delegation.
Create a new delegation round for BSA, DevOps, QA, Developer, and Code Reviewer.
Use Claude Code three-level command governance:
1. Hooks are hard constraints.
2. Rules load only by relevant paths.
3. CLAUDE.md is short global context.

For every sub-agent, define objective, ownership, boundaries, evidence expected, and stop condition.
Do not assign two agents to edit the same file.
Collect all results in the standard result format before changing PROJECT_TASKS.md status.
```

### DevOps release investigation prompt

```text
Objective: Investigate the latest deployment or CI workflow failure.
Ownership: GitHub Actions logs, workflow files if explicitly assigned, deployment scripts read-only by default.
Boundaries: Do not print, rotate, or sync secrets. Do not deploy or push unless root has authorized that target.
Evidence expected: run id, job name, failing step, exact error line, and recommended operator command.
Stop condition: DONE with evidence, or NEEDS_HITL if credentials/platform permissions are required.
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

### QA production Playwright prompt

```text
Objective: Determine whether authorized production Playwright can run.
Ownership: Playwright readiness checks, endpoint health evidence, existing test reports.
Boundaries: Do not run sensitive production E2E unless authorization is explicit and current.
Evidence expected: backend health, browser availability, command to run, artifact path or blocker reason.
Stop condition: DONE when runnable evidence is available; BLOCKED when live backend or authorization is missing.
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

### BSA project-task sync prompt

```text
Objective: Reconcile PROJECT_TASKS.md and plans with the current verified gate status.
Ownership: PROJECT_TASKS.md, plans/*.md, docs/rules/skills assigned by root.
Boundaries: Do not edit source code, workflows, secrets, or generated .codex files.
Evidence expected: changed task states, remaining blockers, HITL actions, and links to evidence.
Stop condition: DONE when task board matches evidence; BLOCKED when evidence is not available.
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

## Completion Rules

The orchestrator may mark a delegated item `DONE` only when:

- The assigned evidence exists and matches the acceptance criteria.
- Any changed files are within the assigned ownership.
- Required checks have passed or a documented waiver exists.
- No external gate is being inferred from local-only results.

Mark the item `BLOCKED` when the same external permission, credential, service availability, or human decision is required and no safe in-scope action remains. Provide the exact next human/operator command or decision needed.
