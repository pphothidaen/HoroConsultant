# HoroConsultant Handoff

Updated: 2026-08-28 (base admission and local pressure controls evidenced; provider proof remains absent)
Branch: `hotfix/prod-version-e2e-contract`
Status: S3 LOCAL ADMISSION AND PRESSURE CONTROLS COMPLETE — no runtime/provider capacity proof

## Objective

Retain the completed local S3 four-pool contract, admission, and pressure
controls. Do not duplicate that local work. The only separately authorized
remaining S3 work is provider-native proof, which requires a fresh exact
decision/HITL record.

The intended pools are independent quota accounts:

- `agy1` and `agy2`: Google AI Pro through AGY CLI.
- `codex1` and `codex2`: independent Codex quota accounts.

The intended topology is Codex Root A sending typed requests to AGY Root B.
Root B owns AGY account queues, workers, leases, and aggregate responses.

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

## What has been done

### Earlier repository work

The branch already contains these commits:

- `943bdd8` — freeze QOBS dispatcher and scheduler sources.
- `8a5ab77` — record vault sync timestamp.
- `8d29f73` — centralize `project_tickets.md` as a pointer to
  `PROJECT_TASKS.md`.
- `dabb491`, `1515380`, `165a825`, `9847234`, `21f8a92` — QOBS governance,
  contract, test-baseline, and planning history.

QOBS dispatcher/scheduler focused evidence previously passed `67` tests, but
QOBS remains open behind the probe and QA/governance synchronization gates.
Do not claim release readiness from that evidence.

### S3 documentation and governance work

The documentation child created:

- `.agents/rules/19-agy-capacity-governance.md`
- `.agents/skills/agy-capacity-orchestration/SKILL.md`
- S3 entries in `PROJECT_TASKS.md` and `plans/plan.md`

The documentation child reported skill validation and `git diff --check`
passed. This governance-resumption record then ran the prescribed ecosystem
`--sync` and `--check`; both passed, including the Antigravity/Gemini/AGY and
Codex/OpenAI synchronization checks. The separate
`TICKET-S3-AGY-CAPACITY-RUNTIME-20260827` completed its base local lease
contract/policy/tests plus scheduler and dispatcher admission integration.
Attributed evidence: the contract worker passed 7 focused tests, the admission
worker passed a 201-test suite, and independent QA ran the capacity/scheduler/
dispatcher command with `201 passed` plus a scoped diff check. This establishes
filesystem-backed base local admission only. A later implementation audit found
the claimed per-account burn-rate, S4 backpressure, and S5 circuit-breaker
controls absent, so this ticket was superseded for pressure behavior. The
disjoint pressure extension has now completed filesystem-backed local controls:
per-account burn rate, S4 typed block/queue, S5 typed circuit cooldown/manual
reset, isolation/no fallback, and scheduler/dispatcher pre-spawn no-subprocess
enforcement. There is still no runtime quota,
provider concurrency, route execution, account-capacity, or provider-native
receipt proof, and no provider action or commit occurred.

### S3 runtime work

An implementation child completed the local-only admission work:

- `scripts/multiagent_capacity.py`

The local contract, policy, and tests cover atomic lease consumption and the
scheduler plus final dispatcher pre-process admission boundary on governed
CLI/bound invocation paths. The disjoint
pressure extension completed local per-account burn rate, S4 backpressure, and
S5 circuit breaker behavior. Its attributed evidence is: focused capacity
`12 passed` plus `py_compile`; pressure-admission combined suite `213 passed`;
independent QA `214 passed` and a clean scoped tracked/untracked S3 diff check.
Final independent gates passed: governance regression `16`; workspace-root
secret scan `1,994` files / `0` findings, including current modified/untracked
S3 artifacts; tracked/untracked S3 diff checks remained clean.

No external AGY/Codex command was run for this S3 work. No runtime quota or
provider concurrency limit was independently verified.

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

Use four isolated queues and start with one lane per account. Increase to two
lanes per account only after observed burn-rate and latency are within budget.
The AGY account ceiling is three; S4/S5 must reduce or stop admission rather
than silently fail over or downgrade quality.

Recommended role split:

- `codex1`: single writer/integration owner.
- `codex2`: isolated QA or contract review.
- `agy1`: Flash triage, retrieval, and test planning.
- `agy2`: independent review on a frozen diff or high-risk evidence.

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
