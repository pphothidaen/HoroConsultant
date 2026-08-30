---
name: orchestrator-delegation
description: Use for meaningful mutation, QA, review, operations, or requested multi-agent delegation.
---

# Orchestrator Delegation Skill

Use this skill by default when a request requires meaningful mutation, QA,
review, operations, or multi-agent coordination, including requests to
distribute work, coordinate blockers, or collect specialist results.

Primary owner: `orchestrator`. Supporting agents: `business_analyst`, `developer`, `qa_tester`, `devops`, and `code_reviewer`.

## Default Decision Boundary

Delegate meaningful executable work to the narrowest relevant specialist.
Root may directly answer a trivial no-tool question or perform bounded
read-only orchestration such as intake, scheduling, status synthesis, and result
collection. These exceptions do not permit root implementation, QA mutation,
review closure, deployment, publishing, or another operation. Do not delegate
when a child would only repeat an answer already available to root.
Use `[OK]`, `[ERROR]`, `[WARNING]`, or `[INFO]` for command-facing status/logs.

## Delegation Contract

The orchestrator remains accountable for the final answer, ticket state, and user-facing decision. Sub-agents provide bounded investigation, implementation, QA, DevOps, review, or documentation results; they do not independently widen scope or mark release gates complete.

Before spawning or assigning work, define:

- Objective: the exact outcome the sub-agent owns.
- Ownership: files, systems, or evidence areas the sub-agent may touch.
- Boundaries: files or external actions the sub-agent must not modify or trigger.
- Evidence: command outputs, artifacts, or concise findings expected back.
- Stop condition: when the sub-agent must report `DONE`, `BLOCKED`, or `NEEDS_HITL`.

For executable lanes, first use `adaptive-model-effort-routing`: record the
versioned `DispatchDecision`, preserve its quality floor, and require bound
receipt proof. Static role model/effort values are hints, never runtime proof.
Missing dependency, ownership, quota, HITL, Rule 11, Rule 18, or receipt gates
fail closed before spawn.

For a source-mutation ticket, require a committed test-only baseline and closed
provenance manifest before dispatch. The baseline must be an ancestor of the
source branch, bind exact test hashes, and record red or negative-control
evidence. The source lane remains ineligible until the ticket is
`TEST_BASELINE_VERIFIED`. A split reconstructed after coding is
`NON_TDD_RECONSTRUCTED` and cannot satisfy this gate.

If a frozen test is wrong, stop the source lane. Route a separate QA-owned,
test-only correction for an independently reviewed superseding baseline that
records the prior SHA, correction reason, new hashes, and new evidence. Resume
source work only after the superseding baseline passes the history guard.

## Ticket Scheduling Before Delegation

Rule 11 is authoritative. At every checkpoint, first exclude tickets that are
not `TODO`/`READY`, have missing scheduling fields, unmet dependencies, an
ownership conflict, a quota/HITL failure, an explicit blocker, or an invalid
Rule 18 decision. Sort only the remaining execution-eligible tickets by
`(-severity_rank, work_effort_rank, ticket_id_ascii)`: Severity is
`CRITICAL > HIGH > MEDIUM > LOW`, Work Effort is `XS < S < M < L < XL`, and
an exact tie uses Ticket ID in ASCII ascending order. Select the first ticket;
for parallel work, reserve its ownership and recompute before selecting again.
These eligibility gates override the comparator, and running work is not
preempted. Work Effort is delivery size, not model reasoning effort; model
selection never changes scheduling order. Historical `Priority`-only text is
superseded for scheduling and remains evidence only.

## Full-Capacity Invariant

While actionable session work remains, continuously recompute live capacity and
MUST keep every available collaboration slot assigned to a useful, independent,
evidence-bearing lane. Run this dispatcher loop until terminal session
completion:

```text
observe capacity -> inventory useful work -> decompose -> reserve ownership -> dispatch -> collect -> immediately refill
```

A lane completion, failure, cancellation, or capacity change immediately
re-enters the loop. Decompose current tickets into the smallest coherent bounded
lanes without artificial fragmentation. Select a lane, reserve its file/module
ownership, recompute Rule 11 and capacity, and dispatch again. One editor owns
each file/module; final QA and release wait for source freeze and dependencies.

If primary implementation is dependency-blocked, create useful non-mutating
fallback tickets from independent verification, QA baseline, risk/threat
review, documentation/evidence reconciliation, lifecycle/process audit, test
design, or dependency-resolution analysis. Every fallback lane needs a ticket,
objective, scope/ownership, boundaries, evidence, acceptance criteria, and stop
condition. Do not consume a provider or quota merely to fill a slot unless the
user explicitly authorized it.

Never dispatch duplicate/redundant work, same-file concurrent editors, stale or
fake busywork, dependency bypass, daemons/background quota burn, or work that
could create false completion. If exhaustive decomposition cannot form a useful
safe lane, emit `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE` with the capacity
snapshot, ticket/dependency inventory, rejected candidates/reasons, and
quota/HITL evidence, then immediately escalate to orchestrator replanning. This
is a blocking invariant violation requiring action, not ordinary allowed idle.

Live status must report `active/available` slots, each active lane and its
ownership, plus waits/blockers and any typed capacity exception. A lane may not
bypass quota, HITL, dependency, or ownership gates to occupy capacity.

Registered specialists are on-demand capabilities, never auto-started daemon
or background quota consumers. Spawn one only for a selected ticket with
parent/session/ticket, ownership, timeout/lease, concurrency, and receipt
bindings. Clean up terminal children, detect orphan/zombie state, and return a
typed quota-safe stop rather than detach, persist, or blindly retry.

### Governed short fallback while QA waits

Use an idle slot during an active source edit only for a short fallback that
passes all of these gates:

- Its ticket is `TODO`/`READY`, dependencies are complete, and Rule 11/18,
  quota, HITL, and decision gates pass.
- Its ownership is disjoint from every active source and documentation editor.
- `work_mode` is `READ_ONLY`, `evidence_bearing` and `freeze_independent` are
  true, and current Stage A provider mode is `NONE`.
- Its lease is `1..600` seconds, `natural_termination` is true,
  `preemption_policy` is `NEVER`, and it is neither a daemon nor background
  work.

The normative hard ceiling is `600` seconds. Current Stage A uses an effective
maximum of `300` seconds; a trusted configured limit may be stricter, but a
scan, prompt, ticket, or caller field can never raise either ceiling. Require
exact `started_at`, `deadline_at`, and lease agreement, while keeping trusted
wall-clock and natural-exit enforcement `NOT_PROVEN`.

Do not cancel or preempt a running fallback when source freezes. If QA becomes
eligible and a slot is idle, dispatch QA before any new fallback. When all
slots are busy, record next-slot QA priority; the next completion/refill must
select QA first. A short lease exists so the fallback releases capacity by
itself, not so the orchestrator can force-cancel it.

If no candidate passes, emit `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE`. Include
the exact candidate tickets and typed rejection reasons, plus evidence bound to
the current snapshot digest. Do not create a duplicate or speculative lane to
avoid reporting the exception.

### Governed Stage A capacity checkpoint

Use `full-capacity-governance-v2` as a structural record, not an execution
receipt. Stage A computes and validates:

- The exact capacity and complete `TODO`/`READY` ticket inventory, dependency,
  blocker, quota, HITL, active ownership, and source-to-QA state.
- Rule 11 order from severity, work effort, ASCII ticket ID, eligibility, and
  reservations; a lower-ranked lane cannot bypass the selected ticket.
- Rule 18 by normalizing the full decision against the bound policy and digest;
  a caller `rule18_passed` boolean is not evidence.
- Exact ticket and per-alias rejection reasons derived from that normalized
  state. A reason contradicting its inputs rejects the checkpoint.
- Provider-authorization structure bound across authorization ID, evidence
  digest, provider, alias, session, ticket, role, ownership, Rule 18 decision,
  policy version, and policy digest. The result remains
  `STRUCTURALLY_BOUND_NOT_PROVEN`.

Treat the capacity record as a closed schema: missing, duplicate, omitted,
unknown, or extra controls fail closed. Caller-supplied inventory completeness,
pass/fail declarations, proof booleans, timestamps, aliases, models, hashes, or
receipts cannot establish external truth.

Resolve the event tool identity before classifying its family. Normalize
execution-family names case-insensitively to canonical `Task`, `Bash`,
`run_command`, `shell`, or `terminal*`. Recognize both top-level
`tool_name`/`tool_input` and native `toolCall.name`/`toolCall.args`, including
nested-only events. When both forms are present, require their normalized names
and canonical JSON payloads to be exactly equivalent; reject a partial,
malformed, or contradictory pair with `CAPACITY_TOOL_ENVELOPE_CONFLICT`. Apply
the same exact canonical-equivalence rule when both `tool_response` and
`toolResult` represent a Post response.

Accept only exact governed envelopes for every `Pre` and `Post` event in a
normalized execution family. Do not maintain a command-content or path
allowlist: pathless input, `pwd`, `echo`, `git status`, and absolute binary
paths all remain shell events. Reject a missing envelope with
`CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED`; reject unknown fields, wrapper
translations that drop the envelope, representation conflicts, and
normalized-name mismatches. Unrelated non-execution `Read`, `Grep`, and `Edit`
events may pass this capacity envelope boundary without an envelope, but still
obey their ordinary mutation, ownership, and authorization gates. Require the
Claude full-capacity guard exactly once under matcher `.*` in both `PreToolUse`
and `PostToolUse`, preserving every other hook registration.

A complete shell envelope permits structural validation only. Stage A rejects
every attempted governed-shell dispatch with
`AUTHORITATIVE_SNAPSHOT_NOT_PROVEN` until Stage C / `DSG-009A` proves the
authoritative scheduler and native pre-spawn boundary.

Persist local lifecycle continuity only in a regular non-symlink SQLite file
inside an owner-only `0700` directory, with `0600` file permissions. In one
transaction, bind session and monotonically increasing sequence to the previous
record, exact `PRE` tool-input record, and exact `POST` tool-result record.
Reject replay, fork, duplicate, stale sequence, session mismatch, missing phase,
or digest mismatch. This same-principal local ledger is continuity evidence;
it is neither a trusted external receipt nor native/world-state proof.

Every Stage A checkpoint contains exactly one `EVALUATED` entry for `agy1` and
one for `agy2`. Both MUST be `NOT_ELIGIBLE`, `dispatched: false`, receipt-free,
and carry the exact derived reasons, even when a caller supplies internally
consistent positive-looking authorization. Fairness metadata remains empty and
cannot select an alias. Positive AGY/provider eligibility and actual dispatch
fail closed until the later boundaries below are proven.

Stage A MUST keep authoritative snapshot completeness, native hook/pre-spawn
interception, provider runtime/provenance, actual dispatch, world state, trusted
wall-clock enforcement, and natural-exit enforcement `NOT_PROVEN`. A requested
`gpt-5.6-sol` with `ultra` or `max` effort is advisory routing intent only; it
does not prove effective model, effort, account, quota, or receipt.

- Stage C / `DSG-009A`: authoritative scheduler snapshot and native pre-spawn
  boundary.
- Stage D / `DSG-009B`: trusted provider verifier and positive AGY/provider
  routing, enabled only after Stage C and fresh exact HITL authorization.

The Stage A hook validates submitted structure and owner-local continuity. It
must not claim to be the authoritative scheduler, native interception layer,
trusted provider verifier, or actual dispatcher.

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

For meaningful work, start with the smallest applicable subset of this split;
explicit requests such as "กระจายงาน", "run agents", "continue until done", or
"ตรวจสอบ plans/project tasks" also trigger it:

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

## On-Demand Process Flow

1. Announce the delegation plan to the user with the active agents and ownership.
2. Enter the full-capacity dispatcher loop and spawn only concrete, selected,
   bounded tasks that can progress independently; registration alone never
   starts a specialist.
3. Continue useful root work while sub-agents run, such as monitoring a primary workflow or validating local evidence.
4. Poll for sub-agent results at natural checkpoints, not in a tight loop; clean
   up terminal state or timeout/lease expiry and immediately refill the slot.
5. Merge results by evidence, not by majority. If two agents conflict, inspect the underlying commands/logs before deciding.
6. Update `PROJECT_TASKS.md`, release handoff docs, or plan files only after the evidence is stable and the user has authorized any required external action.

## Context Hygiene and `/clear` Handoff

Use `/clear` or an equivalent context reset when the active thread has accumulated large logs, repeated workflow polling, completed sub-agent transcripts, or stale investigation branches that no longer need full detail in memory. Do not clear immediately before an unresolved destructive action, secret operation, production deploy, or user decision unless the required state has been summarized first.

Before clearing, produce a compact handoff summary that preserves enough state for the next agent turn to continue without redoing work:

- Objective and current phase.
- Latest commit SHA, branch, and push status.
- Active workflow/run ids, job names, and current step.
- Files intentionally changed, files staged, and known dirty files that are out of scope.
- Verification already completed with exact commands/results.
- Remaining blockers, HITL actions, and the next safe command.
- Secret policy notes, including any leaked/rotated token status without repeating values.

After clearing, resume from authoritative current state. Re-check only the minimum necessary evidence, such as `git status`, current workflow state, and relevant task files. Do not treat the pre-clear summary as proof when fresh external state may have changed.

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
Use `/clear` when context becomes large, but first write a handoff summary with objective, latest commit, active run ids, changed files, verified checks, blockers, and next command.

For every sub-agent, define objective, ownership, boundaries, evidence expected, and stop condition.
Keep every available slot assigned while actionable session work remains. Run
the full dispatcher loop, reserve ownership, and recompute Rule 11/capacity
after every selection or terminal lane. One editor owns each file/module; use
bounded non-mutating fallback tickets when implementation is blocked. Report
active lanes, ownership, waits, active/available slots, and any typed capacity
exception in each live status update.
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
- Required dependency, ownership, quota, HITL, Rule 11, Rule 18, and receipt
  gates remain valid.
- No external gate is being inferred from local-only results.

A capacity exception is never completion. Continue replanning until a safe lane
is dispatched or a separately evidenced terminal blocker/HITL condition ends
the session.

Mark the item `BLOCKED` when the same external permission, credential, service availability, or human decision is required and no safe in-scope action remains. Provide the exact next human/operator command or decision needed.
