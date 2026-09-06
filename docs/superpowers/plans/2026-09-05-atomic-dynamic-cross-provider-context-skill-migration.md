# Atomic Skill, Governance, and Documentation Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task. Use superpowers:writing-skills for every skill and retain the frozen eval baseline.

**Goal:** Split only the eight approved focused skills, migrate canonical role bindings, and correct lifecycle/quota/handoff governance without weakening release closure.

**Architecture:** Frozen test fixtures define eval expectations; real eval files are E1 source/manifest inputs and must exact-match them. Registry roles become the sole binding map; canonical governance gains `VERIFIED_LOCAL` while Rule 21 `DONE` remains unchanged in strength. Lead BA writes canonical docs before a separate operator derives HANDOFF.

**Spec:** `docs/superpowers/specs/2026-09-05-atomic-dynamic-cross-provider-context-design.md`

## Task E1: Focused skills and canonical role bindings

**Ticket/state:** `TICKET-CONTEXT-OPT-001-E1`, blocked by D and frozen skill RED
**Owner:** `business_analyst`

**Create SKILL.md files:**

- `.agents/skills/qa-regression-provenance/SKILL.md`
- `.agents/skills/qa-api-ui-e2e/SKILL.md`
- `.agents/skills/five-elements-ui-palette/SKILL.md`
- `.agents/skills/wcag-apca-color-audit/SKILL.md`
- `.agents/skills/ui-color-token-handoff/SKILL.md`
- `.agents/skills/metaphysical-request-router/SKILL.md`
- `.agents/skills/metaphysical-hitl-scope-gate/SKILL.md`
- `.agents/skills/metaphysical-finetune-handoff/SKILL.md`

**Modify compatibility SKILL.md files:**

- `.agents/skills/qa-e2e-testing/SKILL.md`
- `.agents/skills/web-color-design/SKILL.md`
- `.agents/skills/metaphysical-domain-engine/SKILL.md`
- `.agents/skills/orchestrator-delegation/SKILL.md`

**E1 source allowlist and manifest inputs (real evals, not baseline content):**

- `.agents/skills/qa-regression-provenance/evals/evals.json`
- `.agents/skills/qa-api-ui-e2e/evals/evals.json`
- `.agents/skills/five-elements-ui-palette/evals/evals.json`
- `.agents/skills/wcag-apca-color-audit/evals/evals.json`
- `.agents/skills/ui-color-token-handoff/evals/evals.json`
- `.agents/skills/metaphysical-request-router/evals/evals.json`
- `.agents/skills/metaphysical-hitl-scope-gate/evals/evals.json`
- `.agents/skills/metaphysical-finetune-handoff/evals/evals.json`
- `.agents/skills/qa-e2e-testing/evals/evals.json`

**Frozen read-only baseline expectation fixtures:**

- `tests/fixtures/context_profiles/evals/qa-regression-provenance.json`
- `tests/fixtures/context_profiles/evals/qa-api-ui-e2e.json`
- `tests/fixtures/context_profiles/evals/five-elements-ui-palette.json`
- `tests/fixtures/context_profiles/evals/wcag-apca-color-audit.json`
- `tests/fixtures/context_profiles/evals/ui-color-token-handoff.json`
- `tests/fixtures/context_profiles/evals/metaphysical-request-router.json`
- `tests/fixtures/context_profiles/evals/metaphysical-hitl-scope-gate.json`
- `tests/fixtures/context_profiles/evals/metaphysical-finetune-handoff.json`
- `tests/fixtures/context_profiles/evals/qa-e2e-testing.json`

**Modify canonical role JSON files:**

- `.agents/agents/ba_auditor/agent.json`
- `.agents/agents/ba_intake/agent.json`
- `.agents/agents/business_analyst/agent.json`
- `.agents/agents/code_reviewer/agent.json`
- `.agents/agents/default/agent.json`
- `.agents/agents/developer/agent.json`
- `.agents/agents/devops/agent.json`
- `.agents/agents/hermes/agent.json`
- `.agents/agents/ming_xue_master/agent.json`
- `.agents/agents/numerology_master/agent.json`
- `.agents/agents/orchestrator/agent.json`
- `.agents/agents/prediction_validator/agent.json`
- `.agents/agents/pu_shi_master/agent.json`
- `.agents/agents/qa_tester/agent.json`
- `.agents/agents/san_shi_master/agent.json`
- `.agents/agents/thai_vedic_master/agent.json`
- `.agents/agents/ui_visual_tester/agent.json`
- `.agents/agents/ux_ui_designer/agent.json`
- `.agents/agents/western_astro_master/agent.json`
- `.agents/agents/xiang_xue_master/agent.json`
- `.agents/agents/ze_ji_master/agent.json`

**Other modified canonical files:**

- `.agents/config/scope_skill_registry.v1.json` role/binding sections only, after D releases it
- `.agents/AGENTS.md`
- `.agents/rules/13-ai-agent-ecosystem-sync.md`

- [ ] Verify the nine frozen fixture hashes and documented deterministic RED before the first SKILL.md edit. Exact-compare every real eval source to its corresponding fixture; reject missing, extra, reordered, or weakened cases. The fixtures cannot authorize or enable a skill. At 27% AMBER, preparation requires fresh reassessment; provider-backed pressure execution remains unauthorized and must be recorded as not run, never fabricated. Missing no-guidance evidence is an explicit block, not a waiver.
- [ ] Implement one focused skill at a time, rerun its deterministic eval contract, and stop before the next skill if the current contract is not GREEN. Each skill has trigger-only frontmatter description `<=100` characters, body `<=300` lines, one responsibility, no copied release/domain workflow, and pure ASCII logs.
- [ ] Convert `qa-e2e-testing`, `web-color-design`, and `metaphysical-domain-engine` to workflow-free compatibility routers with owner, sunset condition, and no focused-profile activation. Do not split any other skill.
- [ ] For metaphysics skills, require `source_domain=metaphysical-domain-engine`; ambiguity/boundary hour/severe conflict/low consensus/force review/training promotion binds a validated HITL audit plus owner sign-off before implementation or training handoff. Do not alter calculation/training/API behavior.
- [ ] Populate registry roles only from literal frozen role fixtures. Default is the exact four-skill bootstrap; BSA skill is BA-only; reviewer receives read-only QA/release verification and never `devops-deployment`; DevOps alone owns deployment capability; optional plugins are absent.
- [ ] Update all 21 nested canonical role JSON files to one `capability_profile` reference after the registry consumer is ready. During the compatibility window, any legacy `tools` value must exactly equal the registry projection; final local verification requires its removal.
- [ ] Update `orchestrator-delegation`, `.agents/AGENTS.md`, and Rule 13 to bind ticket ID, lane ID, approved-context digest, role/actions/all paths, and resolver result. Generated mirrors and mtimes are never authority.
- [ ] Run the frozen context skill/budget tests and `project/tests/test_skill_configurations.py`; verify fixtures/tests/provenance are unchanged and every real eval still exact-matches its fixture.

## Task E2: Test-first governance, lifecycle, docs, and ownership release

**Ticket/state:** `TICKET-CONTEXT-OPT-001-E2`, blocked by E1 and governance RED
**Canonical owner:** `lead_ba` / `business_analyst`

**Modify only in the Lead BA lane:**

- `.agents/rules/17-multi-account-agent-orchestration.md`
- `.agents/rules/20-context-handoff.md`
- `.agents/rules/21-agile-governance.md`
- `.agents/skills/multi-account-agent-orchestration/SKILL.md`
- `README.md`
- `HOWTO.md`
- `ATOMIC_TICKET.md`
- `plans/plan.md`

**Derived continuity owner after Lead BA releases canonical docs:** authorized handoff operator; only `HANDOFF.md` through `python3 scripts/context_handoff.py snapshot --output HANDOFF.md`. QA, developer, DevOps, and reviewers may request this checkpoint but never write the ticket, plan, or handoff.

- [ ] Confirm frozen `tests/test_context_profile_budget_handoff.py` fails for the old Rule 17/20/21 and orchestration semantics before editing governance.
- [ ] Rule 17 and the orchestration skill define quota thresholds only as remaining percentage: `<=40%` reassess before each bounded lane, `<=20%` at most one lane plus snapshot before material action, and `<10%`, HTTP 429, `usageLimitExceeded`, missing/contradictory signal before high-cost work as freeze-and-handoff. `UNKNOWN` is never GREEN.
- [ ] Preserve pool isolation: host 27%, codex1 96% five-hour, agy1 96% five-hour, and agy2 75.21% weekly/100% five-hour are independent owner observations and never averaged/substituted. Auxiliary work requires alias/config isolation validation, a fresh pool-specific receipt, and a receipt-backed decision; failure is UNKNOWN.
- [ ] Prohibit `codex_quota_workaround.py --mode summary` unless separately authorized for both login-status calls and rollout JSONL reads. It is never exact quota proof. Preserve existing multi-account admission/HITL/least-privilege rules; do not invent executable aliases.
- [ ] Rule 20 names `ATOMIC_TICKET.md` plus `plans/plan.md` as canonical, and `HANDOFF.md` as derived. Lead BA updates ticket/plan first; only then may the operator regenerate handoff with objective, HEAD/worktree, all task states, decisions/constraints, plan paths, exact commands/results, failures/risks, next action, owners/skills, and sanitized quota evidence.
- [ ] Rule 21 retains all existing `DONE`, sprint/release closure, release notes, tag, push-to-`origin/main`, clean-tree, and verification requirements. Add `VERIFIED_LOCAL` as a separate non-release terminal state that cannot satisfy or weaken `DONE`, authorize release, or bypass integration. It may unlock only fresh read-only release-QA audits.
- [ ] Replace every baseline-gate attribution with `qa-e2e-testing`. Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted. Use “no unauthorized commit,” never a blanket no-commit DoD that contradicts the gate.
- [ ] Update `README.md` and `HOWTO.md` with canonical registry/approved context, resolver usage, pure check, local Codex `debug prompt-input` adapter, probe result semantics, `VERIFIED_LOCAL`, and explicit non-release/no-secret/no-account boundary.
- [ ] Bind task 19 SHA-256 `52c191c36b42a8cfefd047e24924fdce34789164896c75a6f1611e4e9c163276`: `TICKET-SKILL-BUDGET-002` is `BLOCKED_NONREPRODUCIBLE / VERIFIED_LOCAL_CODE_CONTRACT / LIVE_CONFIG_DRIFT`, never `DONE`. It releases exclusive future ownership of `scripts/sync_codex_account_configs.py` to Context F at 23,004 bytes, SHA-256 `4d37513698a48f400e71e0e113c69e073aa9c74e6b2479494c89e76758aaee79`, blob `9d9e9f0f4988a9f58063082b259836b8cb114d96`. Its 44 focused tests pass, but three current checks exit 1 because codex3 lacks eight disable registrations; the old green receipt is stale. Any codex3 config remediation is separately authorized and sequential, with no account sync during F.
- [ ] Rerun governance/handoff tests and confirm Rule 21 `DONE` negative fixtures still require full release closure. Lead BA then updates context states/checklists. The operator derives and validates `HANDOFF.md` afterward; on lock/contention failure, canonical ticket/plan remain authoritative and execution stops.

## Generated mirrors and stop conditions

E1/E2 never edit generated mirrors. Task F renders expected bytes; Task G writes only manifest-listed repository outputs after source-snapshot and ownership checks. Stop on fixture/eval mismatch, missing pressure evidence, scope-HITL failure, workflow duplication, catalog expansion, reviewer deployment capability, alias/capacity/application change, unsafe quota route, premature HANDOFF write, concurrent account sync, or any unauthorized commit/push/tag/deploy/publish/secret/provider/account action.
