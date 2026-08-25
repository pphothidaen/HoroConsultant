---
name: multi-account-agent-orchestration
description: Route bounded agent work across accounts with quota evidence and HITL gates.
---

# Multi-Account Agent Orchestration

Use this skill when work must be dispatched across Codex, AGY, Hermes, or
multiple provider accounts and the result must be auditable. It governs
planning and evidence; it does not authenticate accounts, print secrets,
deploy, publish, or alter provider configuration.

## Required dispatch record

Before dispatch, record:

- objective and acceptance criteria;
- one editor and explicit file ownership per lane;
- out-of-scope files and external actions;
- account alias/provider and non-secret quota band or status;
- evidence expected and stop condition.

Every prompt must include:

```text
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

Require the result contract: `Status`, `Scope owned`, `Evidence`, `Findings`,
`Changed files`, `Residual risk`, and `Recommended next action`.

## Routing and execution proof

Use `scripts/multiagent_prompt_command.py` through
`docs/templates/MULTIAGENT_PROMPT_COMMAND.md`. Render first; execution is an
explicit, separately authorized action. A rendered command, alias, Hermes
label, model name, YAML home path, or route is not proof that an account ran.
For execution proof, retain the child result and safe provider/session
telemetry. Never print or store tokens, cookies, passwords, emails, raw home
paths, or credential values.

## Quota, retries, and HITL

- Re-check quota before a large dispatch and record only a safe band/status.
- At below 10%, stop broad work, update `TICKET-META-008` and the account
  continuity section in `plans/plan.md`, then run:

```bash
python3 scripts/agent_quota_status_guard.py --remaining-percent <percent> --enforce
```

- Retry only the same bounded failure, recording attempt number and evidence.
- After three consecutive failed remediation attempts, or immediately for
  credentials, permissions, billing, production mutation, conflicting ownership,
  or high-impact judgment, return `NEEDS_HITL` with the exact decision or safe
  operator command required.

## Closure

Return `DONE` only when evidence matches acceptance criteria, ownership is clean,
all required children are closed, and sync checks pass. Return `BLOCKED` when a
safe in-scope action cannot resolve missing evidence. Return `NEEDS_HITL` when a
human authorization or decision is required. Use only ASCII log tags:
`[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.
