# Rule 12: Claude Code Three-Level Command Governance

## Purpose

This rule maps the project’s agent-governance model onto Claude Code so prompts, hooks, and context rules stay separated and enforceable.

## Level 1: Hooks (`.claude/settings.json`) — hard constraints

Hooks block high-risk actions before normal agent reasoning continues.

Use hooks for:

- Secret file access prevention (`.env`, `credentials*`, `*secret*`, `*token*`, `id_rsa`, `*.pem`).
- Destructive command prevention (`rm -rf`, `mkfs`).
- Git history protection (`git push --force`, `git push -f`, `git push --force-with-lease`).
- CI compatibility enforcement such as disallowing `pip --no-progress-bar`.
- Quota/status continuity checks via `scripts/agent_quota_status_guard.py` when `/status` or runtime quota env signals show account quota near exhaustion.

Do not rely on `CLAUDE.md` alone for these controls. If violation would be critical, it belongs in hooks.

## Level 2: Rules (`.claude/rules/*.md`) — context-aware rules

Rules load by path or workstream and keep the prompt context small.

Use rules for:

- API structure.
- Frontend standards.
- Test standards.
- CI/CD release rules.
- Sub-agent delegation and result collection.

Rules should contain concrete behaviors and examples. Avoid copying all global project context into every rule.

### Quota handoff rule

If `/status` reports less than 10% quota remaining, or an environment signal such as `AGENT_QUOTA_REMAINING_PERCENT`/`CODEX_QUOTA_REMAINING_PERCENT` is below 10, agents must:

1. Stop nonessential exploration and avoid large log dumps.
2. Write a concise handoff summary for the next AI agent/account.
3. Update `atomic_tasks.md` ticket `TICKET-META-008`.
4. Update `plans/plan.md` only if the account-migration process or blocker set changed.
5. Run `python3 scripts/agent_quota_status_guard.py --remaining-percent <percent> --enforce`.
6. Run `python3 project/core/code_reviewer.py --scan-secrets`.

The handoff must record credential state only as `present`, `missing`, or `invalid`; never include secret values.

## Level 3: `CLAUDE.md` — global baseline context

`CLAUDE.md` should stay short and stable.

Use it for:

- Project identity and stack.
- Primary command list.
- Non-negotiable project norms.
- Links to rules, skills, task board, and handoff docs.

Do not use it as the only place for safety controls or detailed workstream rules.

## Delegation application

When the user asks to distribute work to sub-agents, the orchestrator must:

1. Load `orchestrator-delegation`.
2. Choose one owner per file group.
3. Assign read-only reviewers where file overlap exists.
4. Require the standard result format.
5. Collect evidence before status changes.
6. Escalate HITL for credentials, production actions, or unresolved external gates.

## Prompt template

```text
Apply HoroConsultant Claude Code command governance.
Level 1 hooks are hard constraints and must not be bypassed.
Level 2 rules apply only to relevant paths.
Level 3 CLAUDE.md provides global context only.

Delegate the work into bounded sub-agent tasks.
For each task, define objective, ownership, boundaries, evidence expected, and stop condition.
Do not assign two editors to the same file.
Return all results using Status, Scope owned, Evidence, Findings, Changed files, Residual risk, and Recommended next action.
```
