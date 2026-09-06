# Atomic Dynamic Cross-Provider Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task. Checkboxes are canonical admission gates, not progress guesses.

**Goal:** Implement Corrected Approach B with approved ticket/lane context, immutable closures, lean Horo skill depth, deterministic provider rendering, and fail-closed local evidence.

**Architecture:** The registry and one code-selected `ApprovedTicketContextV1` feed a strengthen-only resolver. Frozen RED precedes source; pure rendering is separate from native local probes; independent receipts can reach only `VERIFIED_LOCAL`, not Rule 21 `DONE` or release.

**Tech Stack:** Python 3.12 standard library, closed JSON Schema, SHA-256, pytest, repository-contained atomic files, supported local Codex/Claude/AGY inspection.

**Spec:** `docs/superpowers/specs/2026-09-05-atomic-dynamic-cross-provider-context-design.md`

## Current state

- Parent: `DOING -- A only`.
- Spec: `APPROVED_FOR_RED_PREPARATION`.
- A: `DOING -- DRAFT_REBUILD_REQUIRED`; the provenance file is absent under current authority and cannot be called refreshed/current until QA creates and validates `DRAFT_RED_NOT_COMMITTED`.
- B: `BLOCKED_SECURITY_CONTRACT_CORRECTION` pending A completion and independent acceptance of corrected B1-B7/containment/ownership contracts.
- C-H: dependency blocked; source mutation is `BLOCKED_PENDING_TEST_BASELINE_VERIFIED`.
- Quota: `AMBER`, 27% remaining at `2026-09-05T04:19:20Z`; guard exit 0, `signal_present=true`, `source=argument`, `handoff_required=false`, `docs_ok=true`. This is not provider execution proof; reassess before every bounded dispatch/deterministic pressure-preparation step/long task. Provider-backed pressure sampling is unauthorized.
- Separate owner observations, never aggregated: codex1 five-hour 96% (reset 14:44 Asia/Bangkok, `2026-09-05T11:20:48+07:00`); agy1 five-hour 96% in the same window; agy2 weekly 75.21% (about 133h58m to refresh) and five-hour 100% this phase. Each remains non-execution evidence pending local alias/config isolation validation and receipt-backed dispatch.

## Global constraints

- Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted. Tag, deploy, publish, release, destructive Git, secret/account/plugin/cache mutation, provider jobs, and external messages remain denied.
- The baseline-commit gate is from `qa-e2e-testing`, not current Rule 21. Rule 21 `DONE`, release notes, tag, push, clean-tree, and release requirements stay intact.
- `VERIFIED_LOCAL` is the sole non-release terminal target. It may unlock fresh read-only release-QA audits, never release/source remediation or DONE.
- Exact root Horo bootstrap: `requirement-grill-gate`, `agile-governance`, `orchestrator-delegation`, `anti-cognitive-decay`; BSA skill is BA-only. Optional plugin request fields are rejected.
- No alias/capacity/broker/quota-pool/model/effort/application/API/metaphysics behavior migration. Freeze current bytes and parsed semantics.
- Canonical JSON recursively rejects non-NFC strings, duplicate keys, and non-finite values, then uses `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")` with no newline and the five exact spec prefixes.
- Check paths are calculation-only and byte-pure. Native probes occur only in G with OS-enforced no-network or return nonzero `UNAVAILABLE`/`UNKNOWN`.

## Dependency-ordered work

| Order | Atomic task | Owner / exact lane | Dependency | State |
|---|---|---|---|---|
| 1 | DOC-C3 canonical freeze | `business_analyst`: canonical ticket/plan, spec, four context plans, two architecture docs | Owner approval | `DONE` |
| 2 | `TICKET-CONTEXT-OPT-001-A` provenance frame | `qa_tester`: `plans/test_provenance/ticket-context-opt-001.json` only | DOC-C3 frozen | `DOING -- DRAFT_REBUILD_REQUIRED` |
| 3 | Derived continuity checkpoint | authorized operator: `HANDOFF.md` only | A validated | `BLOCKED_BY_A` |
| 4 | Independent contract re-review | `code_reviewer`, read-only | Corrected spec/plans/QA map + A + derived HANDOFF current | `BLOCKED_BY_A` |
| 5 | `TICKET-CONTEXT-OPT-001-B` 29-path frozen RED packet and durable pressure receipt | `qa_tester`: exact registry-plan allowlist | Accepted review | `BLOCKED_SECURITY_CONTRACT_CORRECTION` |
| 6 | `TICKET-CONTEXT-OPT-001-C` RED review and one-commit gate | reviewer -> QA one authorized commit -> reviewer | B | `BLOCKED_BY_B` |
| 7 | `TICKET-CONTEXT-OPT-001-D` registry, approved context, evidence, resolver | `developer`: six exact registry-plan paths | `TEST_BASELINE_VERIFIED` | `BLOCKED_PENDING_TEST_BASELINE_VERIFIED` |
| 8 | `TICKET-CONTEXT-OPT-001-E1` eight skills, three routers, roles/bindings | `business_analyst`: exact skill-plan files | D + skill RED | `BLOCKED_BY_D` |
| 9 | `TICKET-CONTEXT-OPT-001-E2` governance/lifecycle/docs/ownership release | `lead_ba`, then separate HANDOFF operator | E1 + governance RED | `BLOCKED_BY_E1` |
| 10 | `TICKET-CONTEXT-OPT-001-F` renderer/check/adapter/probes | `developer`: ten exact provider-plan scripts | D + E1 + E2 + Task-19 pinned Skill Budget ownership release | `BLOCKED_BY_DEPENDENCY` |
| 11 | `TICKET-CONTEXT-OPT-001-G` manifest-owned sync/budget/probe evidence | `devops`: manifest outputs + six exact receipts | F GREEN and no target owner collision | `BLOCKED_BY_F` |
| 12 | `TICKET-CONTEXT-OPT-001-H` independent local verification | QA -> reviewer -> BA auditor; three exact receipts | G | `BLOCKED_BY_G` |
| 13 | State/continuity transition | Lead BA ticket/plan, then operator HANDOFF | unanimous H | `BLOCKED_BY_H` |
| 14 | Resume release-QA read-only audits | existing owners | `VERIFIED_LOCAL` + fresh HEAD/worktree/HANDOFF validation | `TODO_AFTER_VERIFIED_LOCAL` |

After documentation freeze only: codex1 is reserved for the bounded read-only security re-audit; agy1 for bounded hierarchy/parity audit; agy2 preferably for bounded cross-provider semantic QA. Every reservation requires pool-specific recheck, local alias/config isolation validation, and a receipt-backed dispatch decision; any failure is UNKNOWN and leaves the dependency blocked.

## Definition of Ready checklist

- [x] Owner selected Corrected Approach B and retained explicit safety exclusions.
- [x] Canonical spec and four plan files exist with exact owners/dependencies.
- [x] Fresh quota observation is `AMBER` at 27% remaining and is not provider proof.
- [x] Root Horo bootstrap and namespace boundary are literal.
- [x] Approved-ticket/evidence/canonical-JSON/filesystem/subprocess contracts are specified.
- [x] Exact 29-path context portion, 10-path dispatch portion, and three H receipt paths are specified.
- [ ] A provenance frame is complete and independently checked.
- [ ] Independent reviewer accepts corrected B1-B7 and containment test handoff.
- [ ] B produces assertion-level RED with immutable hashes.
- [x] Owner authority permits exactly one QA-owned combined 39-path baseline commit after review; no other commit and no push.
- [ ] Reviewer records `TEST_BASELINE_VERIFIED` before source.
- [ ] Fresh metaphysics scope audit/sign-off exists before metaphysics skill changes.

Only the first six checked items and A's active lane are admitted now. Unchecked items block their dependent tasks.

## Local completion and release boundary

`VERIFIED_LOCAL` requires A-H complete; the authorized committed frozen baseline predating source; all context and neighbor tests GREEN; strict registry/context/evidence identities; immutable closure and containment negatives; deterministic complete manifest; pure checks; exact Codex adapter; fresh `PASS` receipts for Codex/Claude/AGY; static Antigravity parity; all budgets numeric `<=8000` with zero warning/truncation; README/HOWTO current; no alias/application/exclusion drift; three independent H receipts; and final canonical ticket/plan then derived HANDOFF checkpoint.

No unauthorized commit may occur; the sole allowed commit is the owner-authorized QA combined 39-path baseline commit. Every source/config/generated/runtime-evidence change remains uncommitted, and no push is authorized. `VERIFIED_LOCAL` is not Rule 21 `DONE`, release evidence, a tag/push/clean-tree claim, or deployment authorization.

After `VERIFIED_LOCAL`, existing release-QA owners revalidate HEAD, dirty worktree, ownership, and `HandoffSnapshotV1`; discard interrupted results as `UNKNOWN`; then resume only the capacity/UI-runtime/governance read-only audits. Release inventory, source successors, release preflight, DONE, tag, push, deploy, and publish stay dependency blocked.

## Plans

- Registry/RED/baseline/resolver: `docs/superpowers/plans/2026-09-05-atomic-dynamic-cross-provider-context-registry-resolver.md`
- Skills/governance/docs: `docs/superpowers/plans/2026-09-05-atomic-dynamic-cross-provider-context-skill-migration.md`
- Provider/runtime/evidence/review: `docs/superpowers/plans/2026-09-05-atomic-dynamic-cross-provider-context-provider-runtime.md`

## Current audit authority

- Task 17 security re-review SHA-256: `bbc84f46516b023d1b24d40604319f8688ad4415c679e7d907f8ea91e6b0f176`.
- Task 18 plan re-audit SHA-256: `c7ae2047d2d6bef138f05d20a38227e43d96fdf2630fab83e35c33511ca4f6bd`.
- Task 19 ownership-release SHA-256: `52c191c36b42a8cfefd047e24924fdce34789164896c75a6f1611e4e9c163276`. It leaves `TICKET-SKILL-BUDGET-002` at `BLOCKED_NONREPRODUCIBLE / VERIFIED_LOCAL_CODE_CONTRACT / LIVE_CONFIG_DRIFT` while releasing exclusive future ownership of `scripts/sync_codex_account_configs.py` to Context F at 23,004 bytes, SHA-256 `4d37513698a48f400e71e0e113c69e073aa9c74e6b2479494c89e76758aaee79`, blob `9d9e9f0f4988a9f58063082b259836b8cb114d96`. Codex3 remediation is a separate sequential operational lane; no account sync may overlap F.

## Stop and handoff

At ticket start, phase boundaries, before high-cost/long work, and before handoff, record safe quota evidence. `<=40%` remaining means reassess each bounded lane; `<=20%` means at most one lane plus snapshot before material action; `<10%`, HTTP 429, `usageLimitExceeded`, or `UNKNOWN`/contradictory state before high-cost work freezes broad work.

Lead BA updates `ATOMIC_TICKET.md` and `plans/plan.md` first. The authorized operator then derives `HANDOFF.md` with objective, HEAD/worktree, all states, decisions/constraints, plan paths, exact commands/results, failures/risks, next safe action, owners/skills, and non-secret quota evidence. No unauthorized commit, source/config/generated mutation, provider/account action, or false DONE/release claim is allowed.
