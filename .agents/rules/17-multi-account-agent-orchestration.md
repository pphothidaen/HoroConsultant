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

## Meaningful orchestration execution requirement

For meaningful multi-agent orchestration, the orchestrator must explicitly select
one configured alias and perform at least one bounded terminal dispatch
through it: `codex1`, `codex2`, `agy1`, or `agy2`. Here, meaningful means a task
that is represented as multi-agent work or has an agent-owned implementation,
QA, review, research, or operations lane; planning-only discussion does not
create an execution claim.

- Select **one** alias appropriate to the bounded task. `or` does not require
  calling every alias, and aliases not selected must not be represented as
  executed.
- The dispatch record must identify the selected alias, bounded objective,
  file/evidence ownership, command start and outcome, safe process or session
  identifier when available, child result contract, and timestamp. A terminal
  command that only renders a prompt is not execution proof.
- A lane may be marked `DONE` only after its actual child result and required
  evidence are retained. A configured alias, shell function, route label,
  model name, or command text alone remains routing intent.
- Never use an alias availability check to inspect, print, or repair
  credentials. Record only safe availability/outcome metadata.

### Alias-unavailable fallback

If the selected alias is unavailable before execution, record the alias,
timestamp, safe failure class (for example `not configured`, `executable
missing`, or `permission/authentication required`), and that no child ran.
Then select one other explicitly configured alias for the same bounded task
only when ownership, scope, and authorization remain unchanged. Record the new
attempt separately; do not relabel it as execution by the unavailable alias.

If no configured alias can execute the task, return `[ERROR] BLOCKED` with a
safe operator command or configuration decision. Return `NEEDS_HITL`
immediately for credentials, permissions, billing, production mutation, or an
ambiguous ownership/alias decision. Do not invent an alias, silently fall back
to the orchestrator session, or claim multi-agent execution without process and
child-result evidence.

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
