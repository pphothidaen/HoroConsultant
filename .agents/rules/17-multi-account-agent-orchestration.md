# Rule 17: Multi-Account Agent Orchestration & Quota Evidence

## Purpose

Govern ownership-scoped dispatch across Codex, AGY, and Hermes accounts without
mistaking an alias, configuration, or rendered command for execution proof.

## Scope and ownership

- The orchestrator owns decomposition, account selection, retry decisions,
  conflict resolution, and final closure.
- The assigned agent owns only the files and evidence named in its ticket.
- The BSA owns `PROJECT_TASKS.md`, `plans/plan.md`, governance rules/skills, and
  prompt templates; generated mirrors are changed only by the sync workflow.
- No concurrent agents may edit the same file. Reviewers of a shared file are
  read-only.

## Dispatch contract

Every prompt must state objective, ownership, boundaries, evidence expected, and
stop condition, include the non-reversion coordination warning, and require the
standard result fields: `Status`, `Scope owned`, `Evidence`, `Findings`,
`Changed files`, `Residual risk`, and `Recommended next action`.

PromptCommand is dry-run by default. An alias, Hermes route, model label,
configured CLI home, or rendered command proves routing intent only. Execution
proof requires the child process result plus provider/session telemetry where
available; never record tokens, cookies, account-home secrets, or credential
values.

## Quota and account evidence

Record quota/account state only as non-secret metadata: account alias, provider,
remaining-quota band or status, route/session identifier when safe, command
outcome, and timestamp. Below 10% remaining, stop broad work, update
`TICKET-META-008`, preserve a safe resume command, and run the quota guard.

## Retry and HITL policy

- Retry the same bounded task only when the failure is actionable and ownership
  remains unambiguous; record attempt number and the exact failure evidence.
- After three consecutive unsuccessful remediation attempts, pause and escalate
  to HITL with the blocker, evidence, decision required, and next safe command.
- Escalate immediately for credentials, platform permissions, billing,
  production mutation, conflicting ownership, or unresolved high-impact
  decisions. Investigation approval does not authorize mutation.
- Do not mark a parent ticket `DONE` while a required child is pending or while
  execution proof is inferred from configuration alone.

## Completion gate

Close PROMPT-GOV or a child dispatch only when ownership boundaries are met,
required evidence is attached, all retries/HITL decisions are recorded, no
secret values appear, generated mirrors are synchronized, and the final
closure checklist is complete. Use only `[OK]`, `[ERROR]`, `[WARNING]`, and
`[INFO]` status tags in command-oriented records.
