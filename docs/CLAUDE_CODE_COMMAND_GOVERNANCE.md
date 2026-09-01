# Claude Code Command Governance and Sub-Agent Delegation

This guide turns the HoroConsultant command-control model into a practical Claude Code prompt and repo structure.

## Current Delegation Round

| Workstream | Agent role | Ownership | Stop condition | Result expected |
| --- | --- | --- | --- | --- |
| Governance docs | `business_analyst` | `atomic_tasks.md`, `plans/`, `.agents/rules/`, delegation skills as read-only review | `DONE` or `NEEDS_HITL` | Task/doc update recommendations |
| Claude governance structure | `developer` | `.claude/`, `CLAUDE.md`, `AGENTS.md` as read-only design input | `DONE` or `BLOCKED` | Exact hook/rule/global-context patch plan |
| Guardrail QA | `qa_tester` | `.claude/`, `.agents/rules/`, sync/test scripts as read-only review | `DONE` or `BLOCKED` | Safe validation commands and acceptance criteria |
| Integration owner | `orchestrator` | Final patch, conflict resolution, user-facing status | `DONE` only after evidence matches criteria | Merged governance artifacts and handoff |

Sub-agent tasks must include:

```text
You are not alone in the codebase; do not revert edits made by others.
Work only within your assigned ownership and adapt to visible changes from other agents.
```

## Level 1: Hooks - hard constraints

File: `.claude/settings.json`

Purpose: block critical actions before tool execution.

Current project hook:

- runs on `PreToolUse`;
- matches `Bash`, `Read`, `Edit`, `Write`, `MultiEdit`, `Glob`, and `Grep`;
- calls `.claude/hooks/pre_tool_guard.py`;
- denies secret path access and destructive/token-retrieval shell commands.

Use Level 1 for:

- `.env`, credential, key, and token file access;
- force push or hard reset;
- broad recursive deletion;
- secret-token retrieval commands that could print credentials.

Do not use Level 1 for ordinary style preferences. Put those in rules.

## Level 2: Rules - context-aware rules

Directory: `.claude/rules/`

Purpose: load the right guidance only for the files being changed.

Examples:

- `api-contract.md` applies to FastAPI routers and API tests.
- `frontend-contract.md` applies to static UI and browser regression scripts.
- `testing-and-release.md` applies to pytest, Rust tests, CI, and verification scripts.
- `secrets-and-devops.md` applies to secret/deployment-sensitive paths.
- `orchestrator-subagents.md` applies to task planning, sub-agent result collection, and governance docs.

Recommended rule frontmatter:

```yaml
---
description: Context-aware testing rules for Python, Rust, CI, and E2E validation.
paths:
  - project/tests/**
  - rust_core/tests/**
  - .github/workflows/**
---
```

## Level 3: CLAUDE.md - global context

File: `CLAUDE.md`

Purpose: project-wide facts that should be visible in every Claude Code session.

Keep here:

- what the product is;
- core stack;
- highest-level safety principles;
- common commands.

Move out of `CLAUDE.md`:

- long release runbooks;
- task-specific policies;
- per-folder coding standards;
- transient blocker status.

## Practical prompt examples

### Example 1: distribute a CI failure investigation

```text
Use orchestrator delegation.

Goal: investigate failed Unified CI run without changing production secrets.

Spawn:
1. devops: read-only GitHub Actions log triage; own .github/workflows as investigation scope only.
2. qa_tester: reproduce failing pytest locally with targeted command; own project/tests read-only unless root approves patch.
3. code_reviewer: run secret scan and summarize release risk.

Each agent must report DONE/BLOCKED/NEEDS_HITL with evidence, changed files, residual risk, and next action.
Root owns any final patch and push.
```

### Example 2: implement a backend API change

```text
Use Level 2 API rules.

Goal: add a new deterministic endpoint while preserving /health.

Constraints:
- Do not edit .env or secrets.
- Developer owns project/routers and project/tests API files.
- QA owns test execution and regression evidence.
- Orchestrator merges results and decides whether docs need BSA update.
```

### Example 3: rotate a leaked token safely

```text
Use Level 1 hard guardrails and HITL.

Goal: rotate GH_TOKEN after exposure.

Agent constraints:
- Do not run gh auth token.
- Do not read .env.
- Provide human commands that pipe token values directly into Doppler/GitHub.
- Treat any displayed secret as compromised.

Human executes the token generation/update steps and returns only status, not the token.
```

### Example 4: production Playwright gate

```text
Use QA E2E rules.

Goal: run production Playwright only after live backend health is green.

Gate:
- Verify /health and deterministic API first.
- If backend returns 404/5xx, mark BLOCKED and provide the exact endpoint evidence.
- Run production browser tests only after explicit authorization and healthy backend evidence.
```

## Verification commands

Run these after changing governance files:

```bash
python3 -m json.tool .claude/settings.json
python3 .claude/hooks/pre_tool_guard.py < /tmp/sample-pretooluse.json
python3 scripts/sync_codex_agents.py --check
python3 project/core/code_reviewer.py --scan-secrets
```

For hook spot checks, create temporary JSON payloads outside the repo that represent Claude Code `PreToolUse` input and confirm the hook denies unsafe calls without opening secret files.
