# HoroConsultant Handoff

Updated: 2026-08-29 (BSA governance sealed; local baseline & multiagent test suite verified PASS)
Branch: `hotfix/prod-version-e2e-contract`
Status: VERIFIED LOCAL BASELINE — 100% ECOSYSTEM SYNC, 0 SECRET LEAKS, IDQ-MVP DETERMINISTIC PASS

## Documentation authority

`PROJECT_TASKS.md` is the canonical source for ticket status, ownership,
dependencies, acceptance criteria, and release gates. This file is only the
current-session resume brief. The decision history is in
[`plans/plan.md`](plans/plan.md); the retired TODO traceability index is in
[`plans/todo_tasks_plan.md`](plans/todo_tasks_plan.md); and
[`project_tickets.md`](project_tickets.md) is a compatibility pointer only.
Do not copy ticket definitions or historical sprint logs into this handoff.

## Verified Multiagent & IDQ-MVP Baseline Status (2026-08-29)

- **Spark Model Governance Suite (`TICKET-SPARK-GOV`)**: `DONE — VERIFIED` — 15/15 Spark governance tests passed (`tests/test_spark_model_governance.py`, `tests/test_multiagent_prompt_command.py`), 799/799 total tests passing across `tests/`, policy version `2026-08-29.1` with backwards-compatible support for `2026-08-26.1`, role restriction (`devops`, `code_reviewer`), phase restriction (`qa`, `review`, `release`, `operations`), and `reference_profile` support across quality floors.
- **Five-Pool Capacity & Multiagent Suite (`TICKET-CODEX3-SUPPORT`)**: `DONE — VERIFIED` — 392/392 multiagent & IDQ tests passed (`tests/test_multiagent*.py`, `tests/test_idq*.py`, `tests/test_inter_root_dispatch_contract.py`), 5-pool dual-root capacity architecture (`codex1`, `codex2`, `codex3`, `agy1`, `agy2`) fully implemented and verified with 0 py_compile errors.
- **IDQ Core Test Suite**: 106/106 tests passed (`tests/test_multiagent_durable_queue.py`, `tests/test_multiagent_root_worker.py`, `tests/test_multiagent_root_supervisor.py`, `tests/test_multiagent_bootstrap_dispatch.py`).
- **Scheduling & Contract Tests**: 221/221 tests passed (`tests/test_multiagent_prompt_command.py`, `tests/test_multiagent_ticket_scheduler.py`, `tests/test_multiagent_capacity.py`, etc.).
- **Comprehensive Multiagent Suite**: 515/515 tests passed across all multiagent modules.
- **AI Agent Ecosystem Sync**: 100% synchronized and validated (`python3 scripts/sync_ai_agent_ecosystem.py --check` PASS).
- **Security & Secret Leak Audit**: 0 security leaks detected across 2,178 scanned repository files.
- **Formatting & Style**: `git diff --check` passed with 0 formatting errors.
- **Release Verification (Gate 1-3)**: Pre-release validation passed in `docs/RELEASE_HANDOFF_CHECKLIST.md` (55 release regression tests pass, version `1.0.0.e06b224` immutable digest verified, HF Docker backend dry-run verified).

### Exact Resume Status for Next Session

1. **Sprint ZERO-COST-PIPELINE Status**:
   - `TICKET-ZERO-001` through `TICKET-ZERO-007`: `DONE — VERIFIED` (51/51 zero-cost unit & integration tests passed in `project/tests/test_zero_cost_pipeline.py` & `project/tests/test_semantic_cache.py`, 1782 full regression tests passed, 2,183 files scanned with 0 leaks, 100% ecosystem sync verified). Fail-closed $0 zero-cost routing, 4-tier fallback hierarchy, 60s circuit breakers, multi-tier rate limiting (IP/User/Admin/Daily budget), DDoS micro-burst guard, input/output clamping, and deterministic safe net (<1ms) fully operational.

2. **Sprint SPARK-GOV Status**:
   - `TICKET-SPARK-GOV`: `DONE — VERIFIED` (15/15 Spark tests pass, 799/799 tests pass, policy 2026-08-29.1 backwards compatible, 0 formatting errors, ecosystem sync verified).

3. **Sprint CAPACITY-5POOL Status**:
   - `TICKET-CODEX3-SUPPORT`: `DONE — VERIFIED` (392/392 multiagent & IDQ tests pass, 5-pool architecture complete, 0 py_compile errors, ecosystem sync verified).

4. **Sprint IDQ-MVP Status**:
   - `IDQ-MVP-000-GOV` through `IDQ-MVP-070-QA`: `DONE`.
   - `IDQ-MVP-080-FOUR-ALIAS`: `AUTHORIZED — CONDITIONAL / READY FOR DISPATCH` under single-use authorization `IDQ-MVP-080-AUTH-01` (expires 2026-08-29T04:57:56+07:00 or root restart; requires 1 attempt per alias, read-only, provider-native receipt bound to `WorkResult`, no retry/fallback).
   - `IDQ-MVP-090-SEAL-GOV`: `BLOCKED` on `IDQ-MVP-080-FOUR-ALIAS`.

5. **Sprint RELEASE-RECOVERY-20260829 Status**:
   - `RELEASE-RECOVERY-20260829-PROV-AUDIT`: `DONE`.
   - `RELEASE-RECOVERY-20260829-QA-BASELINE`: `DONE` (106 IDQ core tests, 221 scheduling tests, 515 comprehensive multiagent tests, 0 secret leaks).
   - `RELEASE-RECOVERY-20260829-GATE-VERIFY`: `TODO / next eligible` (Gate 1-3 local verification passed; Gate 4-5 await separate production deployment and live monitoring evidence).

6. **Quota & Runtime Posture**:
   - `codex1`: below 10% remaining (non-secret handoff required).
   - `codex2`: unauthenticated.
   - `agy1` / `agy2`: conservative fallback capacity mode (1 worker floor per account, local burn-rate ledger, pool-local circuit breaker).
   - Ordinary activation remains `CLOSED` and `S5`.

## Active narrow authorization — `IDQ-MVP-080-AUTH-01`

Recorded `2026-08-29T00:57:56+07:00` (Asia/Bangkok): the owner authorized
exactly one read-only provider test each for `codex1`, `codex2`, `agy1`, and
`agy2` under `IDQ-MVP-080`, with no retry, fallback, substitution, or routing
change. The sole allowed evidence is a provider-native `ExecutionReceipt`
bound to a typed `WorkResult`; raw streams, prompts, outputs, credentials,
account IDs, paths, and cookies must never be retained.

`RISK-IDQ-MVP-080-20260829-01` is non-secret. The authorization ends at the
earlier of `2026-08-29T04:57:56+07:00`, root-session/control-process restart,
or terminal disposition of all four aliases; then seal it. Before each process
start, require fresh safe quota, safe identity/executable confirmation,
effective enforced read-only isolation, fresh Rule 18 decision and real Rule
11 snapshot, an unexpired one-use lease/risk record, and unused nonce. Validate
all bindings before atomically consuming that nonce at start. Any failed or
ambiguous gate is terminal `BLOCKED`/`NEEDS_HITL` for that alias and preserves
ordinary `S5`/`CLOSED`/activation-prohibited operation.

This is a narrow supersession only of the former authorization hold for
`IDQ-MVP-080-FOUR-ALIAS`. It does not reopen ordinary activation or authorize
secrets, billing, mutation, Git, deployment, publication, or a readiness
claim. No provider action has been taken by this documentation update. The
canonical detailed record and green dispatch gates are in `PROJECT_TASKS.md`
and `plans/plan.md`.

## Current session handoff — Phase 3 closure and Option C handoff

This section is the authoritative draft resume point for parent/orchestrator
review. Provider probing is stopped for this cycle and older execution notes
below must not be interpreted as permission to repeat a probe.

### Accepted phases

- Phase 1 (`HITL-1-code-and-local-tests`): complete and accepted.
- Phase 2 (`HITL-2-policy-freeze-and-integration`): complete and accepted.
- Phase 3 (`HITL-3-provider-evidence-and-activation-readiness`):
  `BLOCKED / NEEDS_HITL` because it duplicated the consumed Option F JSON
  probe and supplied no new evidence or parser change.

### Frozen safety state

```yaml
quota_status: unknown
concurrency_status: unknown
daily_request_limit: configured_placeholder
reserve_ratio: unverified_entitlement
provider_execution: S5
dispatcher_execution: CLOSED
activation_prohibited: true
```

The configured daily limit is not provider entitlement. The reserve ratio may
only be applied to verified quota; while quota is unknown, any configured
budget is a conservative placeholder and must not be represented as provider
proof. Local admission is S3-capable only for non-provider work.

### `/clar` continuation contract

`/clar` may resume from this handoff only for clarification and evidence
collection. The sole active next path is Option C:

- receive a human-supplied, sanitized interactive `/usage` schema with paths,
  credentials, account identifiers, and raw output removed;
- derive a parser from that real sanitized shape only after parent review.

Until new evidence exists, `/clar` must not run `agy`, request HITL-5 for the
same command or a version-only sanitizer change, repeat Option F, create a
provider probe, activate the dispatcher, or change S5/CLOSED/PROHIBITED.
Human-provided material must be sanitized before entering the repository; raw
output, credentials, paths, tokens, and account identifiers are prohibited.

### Conservative fallback capacity mode

Until provider quota and concurrency are proven, operate only in conservative
fallback mode: one worker floor per account, with the completed local
burn-rate ledger, backpressure, and pool-local circuit-breaker controls. This
is a local admission posture, not a quota entitlement or concurrency claim.

### Latest provider evidence closure

HITL-4 ran exactly one tmux invocation for each of `agy1` and `agy2` using the
approved command and sanitizer v1.3.0. Both sanitized captures were empty;
both quota and concurrency remain unknown. No retry or fallback occurred.

### Option C — human-supplied sanitized schema (approved)

Parent approval covers recording the following human-supplied, sanitized,
time-bound usage observations. The source contained no retained email,
credential, path, account-home value, or raw terminal artifact:

```yaml
source: human_sanitized_interactive_usage
observed_at: "2026-08-28T06:47:29Z"
agy1:
  gemini_weekly_remaining_percent: 63.39
  gemini_5h_remaining_percent: 99.67
  claude_gpt_weekly_remaining_percent: 0.00
agy2:
  gemini_weekly_remaining_percent: 63.39
  gemini_5h_remaining_percent: 99.67
  claude_gpt_weekly_remaining_percent: 0.00
concurrency_status: unknown
```

These observations are human-supplied and time-bound; they are not portable
provider receipts and do not prove concurrency or entitlement.

### Parent-review DRAFT — metadata-only reconciliation

This reconciliation is pending independent parent review. It records only
sanitized, metadata-only facts from a user-supplied structured capture
observed at `2026-08-28T06:47:29Z`; it retains no raw provider response,
account identifier, credential, path, or conversation identifier.

- For each of two aliases, the parsed metadata reports: Gemini weekly
  `remaining_fraction: 0.6338797807693481`, reset
  `2026-08-29T17:33:23Z`; Gemini five-hour
  `remaining_fraction: 0.9966928958892822`, reset
  `2026-08-28T10:29:09Z`; third-party weekly
  `remaining_fraction: 0`, reset `2026-08-30T14:11:52Z`; and third-party
  five-hour `disabled: true`.
- Concurrency remains unknown. This is validated in-process only and is not
  portable or offline receipt evidence.
- Sanitizer v1.4.0 recognizes the nested structured bucket metadata,
  including remaining fraction, reset time, and disabled state. There is no
  authorized lossless bridge into strict QOBS v1: its complete, non-derived
  `usedPercent`, `remainingPercent`, `reached`, `limit`, `spend`, and
  `remaining` fields are absent and must not be inferred or fabricated.
- A local dispatch-validation repair now rejects fabricated empty scheduling
  snapshot digests across dispatch, direct-identity, and receipt-binding
  checks; invalid attempts do not consume a nonce and valid reuse remains
  replay-protected. Delegated local verification reported 81 passing tests,
  compilation, and a scoped diff check. The local repair was independently
  reviewed PASS; this documentation remains a DRAFT pending parent review and
  acceptance.

The existing S5/CLOSED/activation-prohibited block remains unchanged. No new
provider retry is authorized. The sole future provider path is a separate,
exact HITL with a genuine complete contract; this handoff neither drafts an
invocation nor authorizes activation. Continue only the local one-worker
floor per account with the existing ledger, backpressure, and circuit breaker;
it is not quota or concurrency entitlement.

### Conservative fallback capacity mode — approved

Use only the completed local burn-rate ledger, backpressure, and pool-local
circuit-breaker controls with a floor of one worker per account. Do not treat
the Option C observations as authorization to probe, reroute, open the
dispatcher, or activate provider execution.

### Parent handoff decision

Parent/orchestrator should treat the current provider-native evidence attempt
as terminal for this cycle. A future activation request is a separate HITL
after evidence review; finding quota evidence alone never opens the dispatcher.

## Objective

Retain the completed local S3 capacity contract, admission, and pressure
controls. Do not duplicate that local work. The five-pool dual-root capacity
architecture (`TICKET-CODEX3-SUPPORT`) organizes five independent quota
pools across two roots:

- `agy1` and `agy2`: Google AI Pro through AGY CLI (Root B).
- `codex1`, `codex2`, and `codex3`: independent Codex quota accounts (Root A).

The intended topology is Codex Root A sending typed requests to AGY Root B.
Root B owns AGY account queues, workers, leases, and aggregate responses;
Root A does not directly spawn AGY.


## User-attested limits

These values were supplied by the user and are planning inputs only. They are
not runtime proof and must not be copied into an execution receipt as verified
capacity:

- `1,500 requests/day/account`.
- `2 requests/second/account` priority/rate ceiling.
- Context ceiling of `1,000,000 tokens`.
- Main quota reset described as every `5 hours`; the per-window budget is not
  specified, so do not multiply the daily quota by `24/5`.
- Maximum `3` concurrent AGY sub-agents per account.
- Maximum nesting depth `10`; operational target should remain depth `2-3`.
- MCP/tool ceiling `100` per AGY sub-agent.
- Parallel sub-agents use isolated worktrees/context windows.
- `/usage` and `/agents` are available in the AGY CLI for operator inspection.

Derived planning facts:

- `1,500 / 30 = 50` heavy prompts/day/account at the high end of the stated
  `2-30+ requests/prompt` range.
- `1,500 / 2 = 750` prompts/day/account at the low end, before overhead.
- Running at `2 req/s` continuously would burn `1,500` requests in about
  `12.5 minutes`; it is a burst ceiling, not a sustainable lane rate.
- Theoretical AGY worker ceiling is `3 x 2 = 6`, but six workers are not an
  entitlement. Start with `1-2` lanes/account and increase only from telemetry.

## Completed work and authoritative evidence

The current S3 status, ticket IDs, acceptance criteria, and evidence links are
maintained in the S3 section of
[`PROJECT_TASKS.md`](PROJECT_TASKS.md#sprint-s3-agy-capacity-governance-refactor-2026-08-27)
and the matching decision record in
[`plans/plan.md`](plans/plan.md#grill-report--s3-agy-capacity-governance-refactor).
Those records supersede copied historical summaries in this handoff.

In brief: local lease admission and pressure controls are complete and
filesystem-backed. Provider quota, concurrency, account capacity, route
execution, and provider-native receipt proof remain unverified. No external
AGY/Codex command or provider action was performed for this work.

## Current worktree state

Do not reset, checkout, clean, or overwrite the following existing user files:

- Modified: `PROJECT_TASKS.md`
- Modified: `plans/plan.md`
- Modified protected data: `project/data/bazi_bazi_manual_chatml.jsonl`
- Modified protected data: `project/data/distillation_checklist.json`
- Modified QOBS source: `scripts/agent_quota_status_guard.py`
- Modified S3 admission/pressure integration: `scripts/multiagent_prompt_command.py`,
  `scripts/multiagent_ticket_scheduler.py`, `tests/test_multiagent_prompt_command.py`,
  and `tests/test_multiagent_ticket_scheduler.py`
- Untracked QOBS/release evidence under
  `project/tests/artifacts/priority_scheduling/`

New S3 files are untracked:

- `.agents/rules/19-agy-capacity-governance.md`
- `.agents/skills/agy-capacity-orchestration/`
- `.agents/config/s3_capacity_policy.json`
- `scripts/multiagent_capacity.py`
- `tests/test_multiagent_capacity.py`

There was no `HANDOFF.md` before this file was created. No S3 implementation
commit exists.

## Current bounded implementation plan

1. Do not reopen or duplicate local S3 contract/admission/pressure work.
2. Retain the local-only evidence boundary: no provider quota, concurrency,
   account capacity, route execution, or provider-native receipt is proven.
3. Use only `multiagent_model_policy.yaml` as the executable PromptCommand/AGY
   model catalog. `gemini_parity.yaml` is Hermes parity configuration only;
   its legacy/broader Gemini IDs must not enable a route.
4. Treat SHA-256 lease digests as local integrity hashes, not secret-keyed
   adversarial authentication or provider identity/authorization proof.
5. Do not extend local evidence into a provider quota/concurrency/execution or
   release claim. Any provider probe or execution remains separately authorized.
6. Before any future governance change, use the prescribed sync script; never
   manually edit generated `.codex/agents` output.

## Suggested S3 policy

Use five isolated queues and start with one lane per account. Increase to two
lanes per account only after observed burn-rate and latency are within budget.
The AGY account ceiling is three; S4/S5 must reduce or stop admission rather
than silently fail over or downgrade quality.

Recommended role split:

- `codex1`: single writer/integration owner (Root A).
- `codex2`: isolated QA or contract review (Root A).
- `codex3`: overflow, specialized reasoning, and dedicated evaluation lane (Root A).
- `agy1`: Flash triage, retrieval, and test planning (Root B).
- `agy2`: independent review on a frozen diff or high-risk evidence (Root B).

For governed CLI/bound invocation paths, a per-account `CapacityLease` is
required before admission. It binds account/pool, request ID, owner/lane,
request budget, TTL, model quality floor, and policy integrity. Per-account
burn rate, circuit breaker, and backpressure are policy/ledger admission state,
not lease fields. A lease is not proof that a provider executed; the existing
native receipt and WorkResult requirements still apply.

## Known blockers and risks

- Base admission plus local pressure controls have attributed local test
  evidence, but remain provider-proof-limited.
- `multiagent_model_policy.yaml` is the sole executable route catalog;
  `gemini_parity.yaml` is a non-executable Hermes parity config.
- User-attested quota/capacity is not runtime evidence.
- Filesystem-backed lease admission does not prove provider quota/concurrency,
  account capacity, route execution, or provider-native receipt validity.
- `Invocation.capacity_required=False` remains explicit programmatic
  dry-run/legacy optionality; it is neither provider/runtime proof nor
  governed admission. Future programmatic execute paths must bind the same
  governed admission contract before being treated as such.
- SHA-256 lease digests are integrity-only and not secret-keyed adversarial
  authentication.
- The `healthy` user label does not match QOBS v1 executable observation, which
  intentionally emits `constrained`, `below_10_percent`, or `unknown`.
- Existing AGY smoke remains blocked behind fresh decision, snapshot, quota,
  HITL, and read-only gates.
- Existing protected data provenance changes remain unresolved blockers for
  the separate ticket45/release reconciliation.
- Governance mirror/catalog synchronization has passed; local runtime contract,
  admission integration, pressure controls, and focused verification are done.
- Current branch has unrelated dirty files; preserve them and use disjoint
  ownership.

## Safe resume commands

Run these first from the repository root:

```bash
git status --short
python3 scripts/sync_ai_agent_ecosystem.py --check
python3 -m pytest -q tests/test_multiagent_durable_queue.py tests/test_multiagent_root_worker.py tests/test_multiagent_root_supervisor.py tests/test_multiagent_bootstrap_dispatch.py
sed -n '1,260p' scripts/multiagent_capacity.py
sed -n '1,240p' .agents/rules/19-agy-capacity-governance.md
sed -n '1,260p' .agents/skills/agy-capacity-orchestration/SKILL.md
```

Do not delegate duplicate local implementation or QA lanes. Do not run an
external AGY probe or provider execution merely to reopen local work; a
provider-native proof attempt requires a fresh exact decision/HITL record and
must remain one-shot when the ticket says so.

## Handoff acceptance

This handoff is complete when a fresh agent preserves existing dirty files,
accepts the local S3 contract/admission/pressure work as complete without
duplicating it, and keeps provider-native proof as the only separately
authorized remaining work.
