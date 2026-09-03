# HoroConsultant — Master Agile Plan & Architecture Specifications

> **Repository**: `pphothidaen/HoroConsultant`  
> **Authority**: Master Orchestrator (`orchestrator`) & Business System Analyst (`business_analyst`)  
> **Governance Enforcement**: Rule 21 (Agile Governance) & Rule 22 (Plan Completion & Archival Mandate)  
> **Last Synchronized**: 2026-09-04T01:05:00+07:00 (Asia/Bangkok)  

---

<!-- GOV-ROADMAP-20260904:START -->
## GRILL REPORT -- GOV-ROADMAP-20260904: Architectural Roadmap (Rule 24, Subdirectory Scoped AGENTS.md Context Chunking & Ecosystem Parity)

**Recorded**: `2026-09-04T01:05:00+07:00` (Asia/Bangkok)
**Status**: `APPROVED`
**Requirement-change authority**: Owner instruction dated `2026-09-04` explicitly approving the architectural roadmap for Program `GOV-ROADMAP-20260904`.
**Authorized current phase**: `TICKET-GOV-025` Spec & Planning Lead (Status: `DONE`). Downstream tickets `TICKET-GOV-026` and `TICKET-GOV-027` are `READY` for dispatch.

### Scope and Decision Record

**IN**:
1. **Rule 24 Codification & TIA Selective Testing Matrix**:
   - Adversarial Dual-Team architecture:
     - Blue Team (The Builders): `developer`, `devops`, `business_analyst`, `orchestrator`, `ux_ui_designer` with Analytical & Critical Thinking mindset (First Principles, Modular Architecture, Contract-Driven, Clean Code).
     - Red Team (The Adversaries / Auditors): `qa_tester`, `code_reviewer`, `ui_visual_tester`, `prediction_validator` with Inversion Thinking mindset ("Assume code is broken until proven otherwise", find edge cases, surrogate crashes, secret leaks).
   - 4-Tier Testing Paths:
     1. Atomic Path: micro calculation formulas, Julian Day, BaZi 4-Pillars, PyO3 Math Core.
     2. System Path: system compatibility, API Gateways, FAISS RAG, Multi-Provider Router Failover.
     3. Smoke Path: rapid critical readiness (/health gate, Cloudflare Worker proxy < 5s).
     4. Happy Path: complete user flow, Playwright E2E UI Button Regression, Five Elements Themes.
   - Test Impact Analysis (TIA) Selective Testing Matrix:
     - Docs / Rules Only: `python3 scripts/sync_ai_agent_ecosystem.py --check` only (< 3s).
     - UI / CSS Only: `python3 scripts/run_button_regression.py` only (< 20s).
     - Rust Core Only: `cargo test` and BaZi Unit tests only (< 15s).
     - API Routers Only: Gateway contract tests only (< 20s).
     - Pre-Release / PR to main: Full regression on CI.
     - Fail-Fast flags: `pytest -x` (stop on first failure) and `--lf` (rerun only failed tests) during bug fixing.
   - Normative rule artifacts:
     - `.agents/rules/24-red-blue-team-and-selective-testing.md` (length <= 80 lines).
     - `.claude/rules/selective-testing-and-red-blue.md` (length <= 40 lines).
     - Parity sync to `.agy/rules/`.
   - Update `project/core/code_reviewer.py` or selective runner to support `--selective` / TIA mode.
2. **5 Subdirectory Scoped AGENTS.md Context Chunking**:
   - Create 5 scoped context files (length <= 30-50 lines per file):
     1. `rust_core/AGENTS.md`: PyO3 FFI Boundary, Rayon Parallelism, Zero Panic.
     2. `project/core/AGENTS.md`: BaZi Math, True Solar Time, Canonical Texts (Di Tian Sui, Zi Ping Zhen Quan), HITL Routing.
     3. `project/routers/AGENTS.md`: FastAPI Endpoints, OpenAPI Golden Snapshots, Zero-Cost AI Multi-Router.
     4. `project/static/AGENTS.md`: Five Elements CSS Palette, WCAG 2.1 AA Contrast, 5 Canonical Viewports.
     5. `scripts/AGENTS.md`: DevOps Hygiene, Pure ASCII Logging, 2-Tier Secrets, Fail-Closed Release.
   - Hierarchy and precedence: Root Universal Safeguards > Subdirectory Scoped Rules (scoped rules cannot relax core safeguards or secret leak protections).
   - Ecosystem Parity and Validation:
     - Update `scripts/sync_ai_agent_ecosystem.py` to enforce existence and validation of these 5 files.
3. **Ecosystem Parity & Quality Gates**:
   - Synchronize across Claude, AGY, and Codex agent configs.
   - Enforce Pure ASCII logging and 100% test pass rate.

**OUT**:
- Direct mutation of files outside owned tickets.
- Unreviewed production releases, credential changes, or external mutations.
- Weakening of Root Universal Safeguards or secret leak protections.

### Nine-Dimension Decision Matrix

| ID | Result and evidence state | Decision / stop threshold |
|---|---|---|
| D1 Scope boundary | `[CONFIRMED]` Scope strictly covers Rule 24 (Red/Blue team, 4-tier test paths, TIA matrix), 5 Subdirectory Scoped AGENTS.md files, and ecosystem parity verification. | Any expansion into unrelated features, unreviewed production deployments, or credential modifications is rejected. |
| D2 Requirement delta | `[CONFIRMED]` Formalizes the upcoming architectural roadmap from `HANDOFF.md` into active governance under Program `GOV-ROADMAP-20260904` with 5 atomic tickets. | Retains existing TDD lifecycle and capacity controls while optimizing verification through TIA and chunked context. |
| D3 Acceptance and stop | `[CONFIRMED]` Persist GRILL report and architecture spec in `plans/plan.md`, register 5 atomic tickets in `atomic_tasks.md` with explicit specialist and skill assignments. | Stop on any syntax error, missing ticket metadata, non-ASCII characters, or unowned file mutation. |
| D4 Inputs, constraints, dependencies | `[AUTO]` Inputs: `HANDOFF.md` roadmap sections, existing rules (Rule 1, Rule 11, Rule 21, Rule 22), ecosystem sync scripts. | Tickets follow strict dependency graph: `GOV-025` leads planning, followed by parallel `GOV-026` & `GOV-027`, then `GOV-028` QA audit, then `GOV-029` safety & release gate. |
| D5 Architecture, ownership, handoff | `[CONFIRMED]` Single-editor file ownership per ticket. `TICKET-GOV-025` owned by `business_analyst` (`plans/plan.md`, `atomic_tasks.md`). Downstream tickets assigned to specific specialists with required skills. | No overlapping file edits across concurrent tickets. Hand-offs must be serial and verified. |
| D6 Assumption register | `[CONFIRMED]` Subdirectory `AGENTS.md` reduces token context by 70-85% for localized agent tasks. TIA reduces test execution from 8-9 min to < 30s for focused changes. | If TIA misses regressions, fallback to full CI suite on PR/pre-release. Root safeguards always take precedence. |
| D7 Risk and recovery | `[AUTO]` Risks: Context fragmentation, rule drift, skipped tests on breaking changes. Recovery: Fail-closed fallback to root rules, mandatory full CI regression on release/PR, pure ASCII logging. | If a test fails under TIA or parity breaks, revert candidate commit and block release. |
| D8 Budget and evidence strategy | `[AUTO]` Token-efficient context chunking, minimal execution time via TIA, zero secret leaks, pure ASCII evidence logs. | Stop on secret leaks, missing evidence receipts, or unbounded test runs. |
| D9 Domain and HITL | `[NOT-APPLICABLE]` No metaphysical calculation formula changes. `[CONFIRMED]` Owner HITL approval confirmed by explicit instruction for Program `GOV-ROADMAP-20260904`. | Production deployment and secret actions retain separate HITL checkpoints. |

### Dependency Graph

```text
TICKET-GOV-025 (DONE: Spec & Planning Lead)
  |--> TICKET-GOV-026 (READY: Rule 24 & TIA Selective Testing Matrix)
  |--> TICKET-GOV-027 (READY: Subdirectory Scoped AGENTS.md Chunking)
        \            /
         v          v
   TICKET-GOV-028 (TODO: Red Team Inversion QA Audit)
         |
         v
   TICKET-GOV-029 (TODO: Pre-Deploy Safety & Release Gate)
```

<!-- GOV-ROADMAP-20260904:END -->

---

<!-- TDD-GOV-BSA-001:START -->
## GRILL REPORT -- TDD-GOV-BSA-001: Mandatory Atomic TDD Lifecycle Gate

**Recorded**: `2026-09-03` (owner instruction)
**Status**: `APPROVED`
**Requirement-change authority**: The owner instruction dated `2026-09-03` explicitly requires a mandatory atomic TDD lifecycle: verified test-only baseline before source work, independent QA before DONE, and immutable baseline correction only through a recorded requirement change plus independently reviewed supersession.
**Authorized current phase**: the owner-approved `TDD-GOV-BSA-021`
requirement-change record in `atomic_tasks.md` and this plan only. After that
two-file commit, `TDD-GOV-QA-022` test-only sequence-4 baseline work is the
only authorized next phase.

### Scope and decision record

**IN**: a fail-closed governance rule, read-only pre-tool hook, governance documentation, skill instructions, ecosystem synchronization, baseline and negative tests, independent post-development QA, final review, and only then integration to `release/provenance-remediation-20260903`.

**OUT**: implementation in this ticket; test/hook/rule/skill changes in this ticket; push, deployment, release, secret or credential actions, and all other external mutations.

| Dimension | Decision / measurable evidence |
|---|---|
| Lifecycle | Each ticket must progress `TODO -> READY -> DOING -> DONE`; dependency or evidence failure is `BLOCKED`/`NEEDS_HITL`, never a bypass. No source `DOING` until the current QA baseline is committed and `TEST_BASELINE_VERIFIED` and its current independent review returns `PASS`. After REVIEW-018 blocked sequence 3, only QA-022 sequence 4 plus REVIEW-023 can satisfy this gate. |
| QA baseline | QA-010, QA-017, and QA-019 are immutable retained sequence-1/2/3 history and cannot admit source. QA-022 must add exactly one v4 test and one closed sequence-4 provenance manifest. It binds the clean BSA-021 parent, the new test hash, exact RED command/fingerprint, sequence-4 permitted future implementation paths, ownership, and the sequence-3 supersession reason. A provenance/history guard must verify it. |
| Frozen tests | Baseline tests, manifest, SHA, hashes, RED/negative receipt, and original evidence cannot change. Source commits must descend from it and carry `Test-Baseline: <baseline SHA>`. Mixed source/test history, a missing trailer, or hash drift is a fail-closed negative case. |
| Requirement-change exception | A new recorded owner requirement change is the only authority to open a QA-owned correction/superseding baseline. It preserves old SHA/reason and captures new hashes plus fresh RED/negative proof. Independent review must pass before source resumes; the original baseline is never rewritten. |
| DEV-025 delivery | Implement rule and read-only pre-tool hook, governance docs and relevant skills, execute required ecosystem sync, incorporate Google AI Studio 3-lane quota orchestration governance, and cover source-before-baseline, mixed commit, frozen-test tamper, trailer drift, and unreviewed supersession negative cases. Freeze the candidate for QA; DEV-025 cannot become `DONE` before QA-030 `PASS`. |
| Independent verification | QA-030 independently verifies a frozen DEV-025 candidate before DEV-025 `DONE`: focused/applicable regression, provenance/history, hook negatives, documentation/skill behavior, and ecosystem `--check`, yielding a candidate- and baseline-bound `PASS`/`FAIL`. REVIEW-040 independently checks safety/governance and a rollback reference. |
| Integration | Only after QA-030 `PASS` and REVIEW-040 `PASS` may INTEGRATE-050 integrate the exact reviewed candidate into `release/provenance-remediation-20260903`. No push/deploy/secrets are authorized by this plan. |

### Dependencies and admission

```text
BSA-001 DONE
  -> QA-010 sequence-1 baseline -> TEST_BASELINE_VERIFIED (retained)
  -> REVIEW-015 independent verdict FAIL (all source blocked)
  -> BSA-016 owner-approved requirement-change record DONE
  -> QA-017 sequence-2 baseline retained; self-audit BLOCKED
  -> BSA-019 owner-approved manifest-tamper correction DONE
  -> QA-019 sequence-3 baseline retained; TEST_BASELINE_VERIFIED
  -> REVIEW-018 independent verdict FAIL (FROZEN_SUITE_CONTRACT_UNSATISFIABLE)
  -> BSA-021 owner-approved sequence-4 supersession and AI Studio quota governance DONE
  -> QA-022 test-only sequence-4 superseding baseline -> TEST_BASELINE_VERIFIED
  -> REVIEW-023 independent sequence-4 PASS
  -> DEV-025 source/governance implementation (candidate freeze; still DOING)
  -> QA-030 independent post-development PASS -> DEV-025 DONE
  -> REVIEW-040 independent final PASS
  -> INTEGRATE-050 provider-release remediation branch only
```

`TDD-GOV-DEV-025` is not `READY` until QA-022 is
`TEST_BASELINE_VERIFIED` and REVIEW-023 returns `PASS`; none of the retained
sequences can admit it. It is never `DOING` before both gates. Normal
one-editor, exact-path, capacity, and evidence admission remain mandatory. The
task board is the canonical status authority.

### Risks, recovery, and stop condition

- **Risks**: retrospective or mixed-history TDD claims, mutable tests tailored to implementation, cross-sequence requirement contradictions, bypassable local-hook claims, source-before-baseline work, quota starvation, key leakage, and integration without independent verdicts.
- **Recovery**: preserve immutable evidence; fail closed; return the affected ticket to `BLOCKED`. For a genuinely changed requirement, record new owner authority and create a separate QA-owned, independently reviewed superseding baseline instead of editing history.
- **Waivers**: `NONE`.
- **Current-ticket stop**: commit only these two planning documents. Do not implement or execute the future rule, hook, tests, skills, sync, integration, or external action.

### Historical GRILL REPORT -- TDD-GOV-BSA-016: Sequence-2 Baseline Correction

This approved sequence-2 decision is retained as audit history. Its current
admission instruction is superseded after QA-017 self-audit and later reviews;
none of its frozen identities or acceptance coverage is weakened.

**Request**: record the owner's `2026-09-03` approval of a requirement change
after REVIEW-015 failed, preserve sequence-1 history unchanged, and authorize
only a QA-owned test-only superseding baseline that corrects the independent
review gaps before any implementation resumes.

**Status**: `APPROVED`
**Authorized next phase**: `TDD-GOV-QA-017` test-only sequence-2 baseline.
**Waivers**: `NONE`.
**Blockers**: DEV and every later ticket remain blocked until superseding baselines are
verified and independent review returns `PASS`.

#### Nine-dimension decision matrix

| ID | Result and evidence state | Decision / stop threshold |
|---|---|---|
| D1 Scope boundary | `[CONFIRMED]` IN is the two-document authority record followed by one separately owned QA test/manifest pair correcting only REVIEW-015 gaps. OUT is any change now to tests, manifests, rules, hooks, skills, source, generated files, runtime, branches outside this worktree, remotes, secrets, push, deploy, or other external system. | Stop BSA-016 on any path beyond `atomic_tasks.md` and `plans/plan.md`. After its commit, only QA-017 may start. |
| D2 Requirement delta | `[CONFIRMED]` The owner answered `อนุมัติ` after the explicit proposal to preserve the old baseline and create a new test-only superseding baseline limited to review findings. | Sequence 1 remains structurally verified but rejected as DEV authority; sequence 2 must be new history, not an edit or relabel. |
| D3 Acceptance and stop | `[CONFIRMED]` BSA-016 records exact SHAs/hashes, gaps, ownership, receipts, dependencies, allowlist, and stop gates in exactly two files. QA-017 must create deterministic dynamic positive/negative tests and a closed sequence-2 manifest, then pass provenance and independent REVIEW-018. | Any baseline drift, static/string-only substitute, permanent-denial-only implementation target, unbound receipt, extra path, nondeterministic RED, or review FAIL stops all source work. |
| D4 Inputs, constraints, dependencies | `[AUTO]` Inputs are sequence-1 commit `b38d5077057c3852a7e2e21af37376567231f810`, test hash `ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642`, its closed manifest, the read-only REVIEW-015 result, current registries/adapters, and the existing conflict marker. `[CONFIRMED]` Owner approval is available. | QA-017 depends on BSA-016 DONE; REVIEW-018 depends on QA-017 verified; DEV depends on REVIEW PASS. Credentials/network/production are neither inputs nor authorized dependencies. |
| D5 Architecture, ownership, handoff | `[CONFIRMED]` BSA owns only the two plans; QA-017 owns only the new v2 test and manifest; REVIEW-018 owns only its repository receipt; developer owns only the manifest allowlist after review; QA-030 and REVIEW-040 own separate receipt paths; integration remains serial. | One editor per path. Shared state/governance paths are reserved only when the predecessor has reached its terminal gate. |
| D6 Assumption register | `[CONFIRMED]` A provenance-valid baseline can still be contract-insufficient; a caller claim is untrusted; valid admission must be repository-backed and generic; current Codex project hooks expose no native PreToolUse interception and must not be represented as one. `[NOT-APPLICABLE]` No metaphysics behavior is involved. | Conflicting platform evidence or a newly required path reopens the requirement gate; no silent allowlist or protocol expansion. |
| D7 Risk and recovery | `[AUTO]` Risks are a deny-all implementation passing weak tests, mismatched trailer acceptance, unreviewed supersession, hard-coded ticket admission, fictitious runtime registration, stale mirrors, and the syntax-invalid existing capacity hook. | Recovery preserves both immutable baselines and receipts, blocks descendants, and seeks new owner authority for any further correction. Never rewrite Git evidence. |
| D8 Budget and evidence strategy | `[AUTO]` Evidence is bounded to exact Git SHAs, SHA-256 values, commands, exit codes, failure fingerprints, registry/protocol fixtures, parity output, and ASCII-safe receipts. | No token, credential, provider, or secret value is read or stored. Stop on unbounded logs or unverifiable runtime claims. |
| D9 Domain and HITL | `[NOT-APPLICABLE]` No astrological calculation, metaphysical source, prediction, training data, or domain conflict changes. `[CONFIRMED]` Owner HITL is satisfied only for this baseline correction. | Push/deploy/release and any further requirement change retain separate authority gates. |

#### Immutable history and correction contract

Sequence 1 is retained exactly:

- baseline commit: `b38d5077057c3852a7e2e21af37376567231f810`;
- parent: `932d1de8974a7f8b9fb7b29cbb4457dc2639891e`;
- frozen test: `tests/test_atomic_tdd_lifecycle_governance.py` with SHA-256
  `ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642`;
- frozen manifest:
  `plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json`;
- REVIEW-015 conclusion: ancestry, exact two-file scope, hash, and provenance
  passed, but contract sufficiency failed. This is not a source-admission PASS.

QA-017 added:

- `tests/test_atomic_tdd_lifecycle_governance_v2.py`;
- `plans/test_provenance/ticket-tdd-gov-qa-017-baseline.json`.

The manifest used `schema_version: test-provenance-v1`, `sequence: 2`,
`supersedes: b38d5077057c3852a7e2e21af37376567231f810`, a non-null correction reason
binding the `2026-09-03` owner approval and REVIEW-015, the BSA-016 commit as
its parent, new test hashes, exact RED argv/exit/fingerprint, QA/reviewer roles,
and the future-path allowlist in `atomic_tasks.md`.

#### Sequence-2 behavioral test matrix

| Contract | Required dynamic proof | Fail-closed result |
|---|---|---|
| Generic valid admission | Build a temporary Git repository with an arbitrary (not hard-coded TDD-GOV) source ticket in the admitted lifecycle state, closed baseline manifest, exact descendant/trailer, allowed target path, requirement-change record when applicable, and independently bound PASS receipt. Invoke the real core/adapters and prove one mutation is allowed. | A deny-all implementation cannot pass. Missing repository evidence denies even when caller booleans claim success. |
| Lifecycle/state | Exercise at least TODO, READY/transition, DOING, BLOCKED, NEEDS_HITL, and DONE using repository-backed fixtures and exact dependency receipts. | Source mutation is admitted only in the policy-defined reviewed state; direct skips and stale/conflicting state deny. |
| Git provenance | Create source-before-baseline, mixed test/source, frozen-test tamper, missing-trailer, and different-full-SHA trailer histories. | Each is rejected with a distinct stable result code, including exact missing versus mismatch errors. |
| Supersession | Exercise sequence 2 with and without a recorded owner requirement change, `supersedes` ancestry/correction reason, and an independent PASS receipt bound to the candidate baseline and manifest hash. | Unapproved or unreviewed supersession denies; valid fully bound supersession participates in the positive admission case. |
| Runtime protocols | Parse registries and invoke actual adapters. Claude deny output uses `hookSpecificOutput.hookEventName=PreToolUse` and `permissionDecision`; AGY consumes its nested `toolCall.args` event and emits decision JSON with deny exit semantics. Legacy registry shape is parsed, not substring-matched. | Missing/duplicate matcher, malformed event, adapter/core disagreement, or unsupported protocol denies. Codex has no fabricated PreToolUse registration; Codex enforcement remains dispatch/CI/provenance based. |
| Mirror and sync | Compare canonical skill content to `.antigravity/skills` mirrors, Claude/AGY rule parity, and deterministic outputs from `sync_ai_agent_ecosystem.py`, `sync_claude_agy_parity.py`, and `sync_sdlc_agents.py`. | Drift, unlisted generated output, or direct generated-file editing fails. |
| Existing hook blocker | Parse `.agents/hooks/full_capacity_guard.py` before runtime registry claims and require conflict-free syntax in the implementation candidate. | The existing conflict marker blocks DEV completion until resolved in its explicitly allowed path and covered by regression. |

#### Receipts, source admission, and downstream stop conditions

REVIEW-018 created receipt `plans/evidence/tdd-governance/tdd-gov-review-018.json`
at `e940d07...` and recorded `FAIL` due to the cross-sequence Codex contradiction.

### Historical GRILL REPORT -- TDD-GOV-BSA-019: Sequence-3 Manifest-Tamper Correction

This approved sequence-3 decision is retained as audit history. Its current
admission instruction was blocked by REVIEW-018 due to the cross-sequence
contradiction in Codex registry assertions; its artifacts remain immutable.

**Request**: record the owner's explicit `approve` after QA-017 self-audit
blocked sequence 2, preserve sequences 1 and 2 unchanged, and authorize only a
new QA-owned test-only baseline that adds the missing dynamic frozen-manifest-
tamper case while retaining all v2 and REVIEW-015 coverage.

**Status**: `APPROVED`
**Authorized next phase**: `TDD-GOV-QA-019` sequence-3 test-only baseline.
**Waivers**: `NONE`.
**Blockers**: REVIEW-018, DEV-020, QA-030, REVIEW-040, and INTEGRATE-050 remained
blocked until sequence 3 was verified.

| ID | Evidence state and decision | Measurable acceptance / stop |
|---|---|---|
| D1 Scope | `[CONFIRMED]` BSA-019 changes only the two governance documents. QA-019 may add only `tests/test_atomic_tdd_lifecycle_governance_v3.py` and `plans/test_provenance/ticket-tdd-gov-qa-019-baseline.json`. | Stop on any edit to old tests/manifests, implementation, rule, hook, skill, config, generated output, other worktree/branch, remote, secret, deploy, or external system. |
| D2 Delta | `[CONFIRMED]` The owner explicitly approved sequence 3 solely for the missing dynamic frozen-manifest-tamper proof discovered by QA-017 self-audit. All v2 and REVIEW-015 cases remain requirements. | No general rewrite, new product behavior, weakened prior assertion, or retrospective relabel is authorized. |
| D3 Acceptance | `[CONFIRMED]` Sequence 3 must have a closed sequence-3 manifest, deterministic RED/fingerprint, dynamic post-baseline manifest mutation with otherwise valid admission evidence, stable fail-closed error, v2 suite execution, provenance PASS, then independent REVIEW-018. | GREEN-at-creation, missing v2 run, string-only assertion, nondeterminism, unbound receipt, extra path, or any old hash drift blocks source. |
| D4 Inputs/dependencies | `[AUTO]` Inputs are owner `approve`, QA-017 self-audit, retained SHAs/hashes, immutable v2 coverage, provenance tooling, and the existing future implementation allowlist. | QA-019 depends on BSA-019; REVIEW-018 depends on QA-019; DEV depends on both. Credentials, network, and production are not inputs. |
| D5 Ownership/handoff | `[CONFIRMED]` BSA owns two docs; QA owns the two new baseline paths; REVIEW-018 keeps its existing single receipt path; later DEV/QA/review/integration ownership remains serial and unchanged. | Any ownership overlap or premature successor activity stops the program. |
| D6 Assumptions | `[CONFIRMED]` REVIEW-018 never ran against sequence 2 and no receipt exists, so it may review sequence 3 without rewriting review history. New QA artifacts are baseline paths and need not enter `allowed_source_paths`. | Conflicting evidence reopens the gate; no inferred path or protocol expansion. |
| D7 Risk/recovery | `[AUTO]` Main risk is a guard that protects test hashes but accepts a changed frozen manifest. Recovery is to retain all baseline histories, block descendants, and require new owner authority for any further correction. | Never amend, squash, delete, or edit a frozen baseline or receipt. |
| D8 Evidence | `[AUTO]` Evidence is limited to full Git SHAs, SHA-256 values, exact argv/exit/fingerprint, dynamic disposable-Git outcomes, provenance output, and ASCII-safe receipts. | Stop on secrets or unsupported runtime/release claims. |
| D9 Domain/HITL | `[NOT-APPLICABLE]` No metaphysical behavior is changed. `[CONFIRMED]` Owner HITL covers only this narrow correction. | Push/deploy/release and further requirement changes remain separately gated. |

#### Frozen identity and sequence-3 contract

Sequence 1 remains commit
`b38d5077057c3852a7e2e21af37376567231f810`, with frozen test hash
`ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642`
and frozen manifest hash
`f161308ce0edbec280989cee25f3715ae82b2767fd90fe55fe012a85475ad963`.

Sequence 2 remains commit
`441a7ed3bddb27110b219df0ee1ffd58e3e547e5`, with frozen v2 test hash
`8ba0d5a89b3b3053f7532ae2623265777ac29de5baa0c783b8ef91d8d36f1dd7`
and frozen manifest hash
`cffa10368b8bc2968c031cc1f78d383cc8dab15ee7af10cc151a068aff9f2899`.

Sequence 3 remains commit
`5ca05d879ca85cf6687772ad9ad7f3ad9fd78928`, with frozen v3 test hash
`c6d05b2cf37a065ff2aa896a24c2d3c154f0748d1c61664d66bd4c20c232672c`
and frozen manifest hash
`b5b29de7909e6ec6f29f33c3ffb4fe098f225ababbb6b50f868fe9f4d5ed8148`.

REVIEW-018 executed against sequence 3 and failed closed with verdict `FAIL`
and finding `FROZEN_SUITE_CONTRACT_UNSATISFIABLE` at commit `e940d07...`
(`plans/evidence/tdd-governance/tdd-gov-review-018.json`), blocking DEV-020.

### GRILL REPORT -- TDD-GOV-BSA-021: Sequence-4 TDD Supersession and Google AI Studio 3-Lane Quota Governance

**Request**: record the owner's explicit requirement change approval after independent
`REVIEW-018` blocked sequence 3 with `FROZEN_SUITE_CONTRACT_UNSATISFIABLE`, preserve
sequences 1, 2, and 3 unchanged in immutable history, resolve the contradiction
between v1 and v2/v3 regarding `.codex/hooks.json`, retain all v2 contracts and v3
dynamic manifest-tamper tests, embed the Google AI Studio 3-lane quota orchestration
governance, and authorize only a new QA-owned sequence-4 test-only superseding baseline.

**Status**: `APPROVED`
**Authorized next phase**: `TDD-GOV-QA-022` sequence-4 test-only baseline.
**Waivers**: `NONE`.
**Blockers**: REVIEW-023, DEV-025, QA-030, REVIEW-040, and INTEGRATE-050 remain
blocked until sequence 4 is verified and the dependency chain passes.

| ID | Evidence state and decision | Measurable acceptance / stop |
|---|---|---|
| D1 Scope boundary | `[CONFIRMED]` BSA-021 changes only the two governance documents. QA-022 may add only `tests/test_atomic_tdd_lifecycle_governance_v4.py` and `plans/test_provenance/ticket-tdd-gov-qa-022-baseline.json`. OUT is any change to old tests/manifests, implementation, rule, hook, skill, config, generated output, other worktree/branch, remote, secret, deploy, or external system. | Stop BSA-021 on any path beyond `atomic_tasks.md` and `plans/plan.md`. After this commit, only QA-022 may start. |
| D2 Requirement delta | `[CONFIRMED]` The owner explicitly approved a Requirement Change to create a sequence-4 test-only superseding baseline resolving the Codex registry contradiction, retaining all v2 contracts and v3 dynamic manifest-tamper tests, and embedding Google AI Studio 3-lane quota orchestration governance. | Sequences 1, 2, and 3 remain immutable history; sequence 4 is a new superseding baseline, never an edit or relabel of prior commits. |
| D3 Acceptance and stop | `[CONFIRMED]` Sequence 4 must have a closed sequence-4 manifest, deterministic RED/fingerprint, dynamic resolution of Codex registry contradiction (asserting no fake PreToolUse registration in `.codex/hooks.json`), all v2 positive/negative/lifecycle contracts, v3 dynamic manifest-tamper proof, provenance PASS, then independent REVIEW-023 PASS. | GREEN-at-creation, unresolved contradiction, nondeterminism, unbound receipt, extra path, or any old hash drift blocks source. |
| D4 Inputs, constraints, dependencies | `[AUTO]` Inputs are owner approval, REVIEW-018 failure receipt (`plans/evidence/tdd-governance/tdd-gov-review-018.json`), retained SHAs/hashes for seq 1, 2, 3, v2/v3 test contracts, AI Studio quota governance requirements, provenance tooling, and sequence-4 allowlist. | QA-022 depends on BSA-021; REVIEW-023 depends on QA-022; DEV-025 depends on both. Credentials, network, and production are not inputs. |
| D5 Architecture, ownership, handoff | `[CONFIRMED]` BSA owns only the two docs; QA owns the two new baseline paths; REVIEW-023 owns only `plans/evidence/tdd-governance/tdd-gov-review-023.json`; developer owns only sequence-4 allowlist after review; QA-030 and REVIEW-040 own separate receipt paths; integration remains serial. | Strict single-editor file ownership per atomic ticket. Any overlap or premature activity halts and escalates. |
| D6 Assumption register | `[CONFIRMED]` Codex has no native PreToolUse interception; `.codex/hooks.json` must not declare a fake PreToolUse interception hook, resolving the v1 vs v2 contradiction. AI Studio 3 lanes are granted read, write, update, execute bounded strictly by the atomic ticket and single-editor file ownership assigned by orchestrator. Ambiguity/overlap halts and escalates to orchestrator. Model is Gemini 3.7 Flash with dynamic effort per ticket. Secret isolation: 0 compromised keys in repo, 3 uncompromised keys in `.env`. | Conflicting evidence reopens the gate; no inferred path or protocol expansion. |
| D7 Risk and recovery | `[AUTO]` Risks include cross-sequence contradiction re-emergence, quota starvation, key leakage, unauthorized cross-ticket writes. Recovery preserves all four baseline histories and receipts, enforces strict single-editor boundaries and zero repo secrets, blocks descendants on any failure, and seeks new owner authority if requirements change. | Never amend, squash, delete, or edit a frozen baseline or receipt. |
| D8 Budget and evidence strategy | `[AUTO]` Google AI Studio 3 lanes (`GOOGLE_AI_STUDIO_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY2`, `GOOGLE_AI_STUDIO_API_KEY3`) dispatched via direct Google API with separate keys. Model: Gemini 3.7 Flash with dynamic effort specified by orchestrator. Evidence is bounded to Git SHAs, SHA-256 hashes, commands, exit codes, fingerprints, and ASCII-safe receipts. Zero key material logged or stored. | Stop on secrets or unsupported runtime/release claims. |
| D9 Domain and HITL | `[NOT-APPLICABLE]` No astrological calculation or metaphysical domain engine behavior changed. `[CONFIRMED]` Owner HITL is confirmed for sequence-4 supersession and AI Studio quota orchestration governance. | Push/deploy/release and secret operations remain separate HITL gates. |

#### Frozen identity and sequence-4 contract

Sequence 1 remains commit
`b38d5077057c3852a7e2e21af37376567231f810`, with frozen test hash
`ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642`
and frozen manifest hash
`f161308ce0edbec280989cee25f3715ae82b2767fd90fe55fe012a85475ad963`.

Sequence 2 remains commit
`441a7ed3bddb27110b219df0ee1ffd58e3e547e5`, with frozen v2 test hash
`8ba0d5a89b3b3053f7532ae2623265777ac29de5baa0c783b8ef91d8d36f1dd7`
and frozen manifest hash
`cffa10368b8bc2968c031cc1f78d383cc8dab15ee7af10cc151a068aff9f2899`.

Sequence 3 remains commit
`5ca05d879ca85cf6687772ad9ad7f3ad9fd78928`, with frozen v3 test hash
`c6d05b2cf37a065ff2aa896a24c2d3c154f0748d1c61664d66bd4c20c232672c`
and frozen manifest hash
`b5b29de7909e6ec6f29f33c3ffb4fe098f225ababbb6b50f868fe9f4d5ed8148`.

REVIEW-018 receipt remains committed at `e940d07...` in
`plans/evidence/tdd-governance/tdd-gov-review-018.json`, recording verdict `FAIL`
with finding `FROZEN_SUITE_CONTRACT_UNSATISFIABLE`.

QA-022 must add only the two declared v4 paths:
- `tests/test_atomic_tdd_lifecycle_governance_v4.py`
- `plans/test_provenance/ticket-tdd-gov-qa-022-baseline.json`

Its manifest must contain:
- `schema_version: test-provenance-v1`
- `sequence: 4`
- `supersedes: 5ca05d879ca85cf6687772ad9ad7f3ad9fd78928`
- `baseline_parent: <BSA-021 commit SHA>`
- QA/reviewer roles (`qa_tester` / `code_reviewer`)
- New v4 test hash
- Exact fresh RED evidence
- Non-null correction reason binding the owner's `2026-09-03` requirement change approval,
  REVIEW-018 failure resolution, and Google AI Studio 3-lane quota orchestration governance
- `allowed_source_paths` exactly matching the sequence-4 list recorded in `atomic_tasks.md`

#### Sequence-4 behavioral requirements

The v4 test suite must:
1. **Resolve Codex Registry Contradiction**: Enforce that `.codex/hooks.json` honestly
   reflects Codex's lack of native PreToolUse interception, forbidding fake hook
   registration while satisfying repo-backed governance.
2. **Retain All v2 Contracts**: Generic repository-backed admission, positive admission
   fixture, lifecycle state transitions, commit separation, missing/mismatched trailers,
   approved/unapproved supersession, Claude/AGY native deny protocols, mirror parity,
   and syntax-clean full capacity guard.
3. **Retain v3 Dynamic Manifest-Tamper Rejection**: Dynamically commit a changed frozen
   provenance manifest after its baseline and require fail-closed rejection.
4. **AI Studio 3-Lane Quota Orchestration Governance**:
   - 3 Google AI Studio lanes (`GOOGLE_AI_STUDIO_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY2`,
     `GOOGLE_AI_STUDIO_API_KEY3`).
   - Current account acts as orchestrator conductor.
   - 3 Google AI Studio lanes are granted read, write, update, execute permissions
     strictly bounded by the atomic ticket and single-editor file ownership assigned
     by the orchestrator.
   - Any ambiguity, overlap, or requirement decision must halt and ask orchestrator to
     decide (no duplicate/conflicting work).
   - Model: Gemini 3.7 Flash, with effort dynamically specified by orchestrator per
     atomic ticket/task.
   - Non-disclosing secret isolation: 0 compromised keys in repo, 3 distinct uncompromised
     keys in `.env` dispatched via direct Google API with separate keys.

After QA-022 provenance verification, independent REVIEW-023 writes only
`plans/evidence/tdd-governance/tdd-gov-review-023.json`. It binds BSA-021 and
all four baseline SHAs/manifest hashes, v4 command outcomes, Codex contradiction
resolution, dynamic manifest-tamper evidence, reviewer identity, and explicit
verdict; its commit descends from sequence 4 and carries `Test-Baseline: <sequence-4 SHA>`.
Only PASS admits DEV-025. QA-030 and REVIEW-040 keep their existing receipt paths
and must bind sequence 4. Integration remains limited to the existing provider
remediation branch gate; no push, deploy, secret, or external action is authorized.

**BSA-021 stop condition**: commit exactly `atomic_tasks.md` and
`plans/plan.md`, verify whitespace and frozen hashes, leave a clean worktree,
then stop without creating QA-022 artifacts or beginning implementation.

<!-- TDD-GOV-BSA-001:END -->

<!-- ADMIN-REMED-BSA-015:START -->
## GRILL REPORT -- ADMIN-REMED-BSA-015: Privileged Admin Action Scope and Superseding Baseline

**Recorded**: `2026-09-01T13:25:21+07:00` (Asia/Bangkok)
**Status**: `APPROVED`
**Authorized next phase**: `ADMIN-REMED-QA-025` TEST-ONLY baseline creation. No source, review, operations, push, deployment, release, secret, or external-system action is authorized by this gate.
**Request**: Persist the owner-approved privileged Admin ingress boundary, classify the prior candidate lineage truthfully, and hand off an exact test-only superseding baseline before any new source lane can be admitted.

### Context evidence

- `[CONFIRMED]` The owner approved the exact IN/OUT route boundary below and creation of a new baseline. UI controls for excluded write actions must not be removed or hidden in this governance ticket; their future UX treatment is separate scope.
- `[AUTO]` Git metadata identifies prior candidate lineage `d95783eeff26e85874477146db2ccb0a61d24ce8 -> d11b8f30cdf969a87b0efa1c02325ec04f05bd1a -> 5b261c532c4ea59246d23f095f605ddb22da354c`. The intermediate source commit `d11b8f3` has no `Test-Baseline:` trailer; only the later `5b261c5` commit carries `Test-Baseline: d95783eeff26e85874477146db2ccb0a61d24ce8`.
- `[AUTO]` The existing baseline assets are `tests/admin_production_ingress_contract.test.mjs` and `plans/test_provenance/ticket-admin-remed-qa-001-baseline.json`. They predate this narrower owner decision and therefore remain historical evidence rather than the authorized baseline for new source work.
- `[AUTO]` The pre-existing worktree changes shown by `git status --short` are outside `plans/plan.md` and `atomic_tasks.md`; this ticket does not claim or modify them.

### Nine-dimension matrix

| ID | Result | Evidence state | Decision / remaining issue |
|---|---|---|---|
| D1 Scope boundary | Allow only the authenticated Admin reads/downloads and the single Google credential-verification POST enumerated below; all listed mutations and every other `/admin/*` or `/hitl/*` path remain fail-closed. | `[CONFIRMED]` | Resolved. No UI-control removal/hiding, source, test, manifest, runtime, external, deployment, push, release, or secret action occurs in BSA-015. |
| D2 Requirement delta | Supersede the broader prior ingress baseline with an explicit least-privilege allowlist. Reclassify `d95783e -> d11b8f3 -> 5b261c5` as `NON_TDD_RECONSTRUCTED` because the intermediate source commit lacks the required trailer. | `[CONFIRMED]` / `[AUTO]` | Resolved. Prior artifacts remain immutable historical evidence and cannot satisfy the new source gate. |
| D3 Acceptance and stop conditions | QA-025 must create exactly one new test contract and one new manifest, prove RED plus negative/fail-closed behavior for the approved boundary, and earn `TEST_BASELINE_VERIFIED` without source changes. | `[CONFIRMED]` | Resolved. Stop on path drift, source mutation, missing provenance/trailer controls, secret output, or any ambiguous route admission. |
| D4 Inputs, constraints, and dependencies | Inputs are the owner-approved route matrix, historical commit metadata, existing baseline assets, a clean immutable QA parent, and provenance tooling. QA-025 is the mandatory dependency for all new source/review/ops tickets. | `[CONFIRMED]` / `[AUTO]` | Resolved. Deployment credentials, tokens, secret values, production access, and external writes are neither inputs nor authorized dependencies. |
| D5 Architecture, ownership, and handoff | BSA-015 owns only this plan and `atomic_tasks.md`; QA-025 owns only its new test and manifest; downstream developer/reviewer/ops tickets remain blocked in strict serial order. | `[CONFIRMED]` | Resolved. One-editor ownership is explicit; no downstream lane may treat the prior baseline as admission evidence. |
| D6 Assumption register | Owner authority and route intent are confirmed. `:source_id` is a path parameter; gray-zone read coverage includes the supported `answered` query forms while preserving the same GET path. Existing UI controls remain present pending separate UX scope. | `[CONFIRMED]` | No pending material assumption. No permission is inferred for implementation or release. |
| D7 Risk and recovery | Risks are accidental privileged-write exposure, wildcard admission, false TDD provenance, UI scope creep, and status inflation. Recovery is documentation-only: retain historical records, block downstream tickets, and amend this decision only with a new owner-approved scope record. | `[CONFIRMED]` / `[AUTO]` | Resolved. Any uncertain path fails closed and returns the affected ticket to `BLOCKED`. |
| D8 Budget and evidence strategy | DispatchDecision v1: phase `governance-scope`; ranks scope=3, complexity=2, risk=3, ambiguity=1, evidence=3; floor and selected intent `codex1/gpt-5.6-sol/high`; quota constrained/Tier 2 Amber; `WRITE_GOVERNANCE`; policy v1; `root-medium=true`; HITL=true from current owner approval. | `[CONFIRMED]` | Native route intent is not provider/runtime proof. Evidence is bounded to route names, hashes, paths, provenance state, and ASCII-safe results; never secret material. |
| D9 Domain and HITL check | No metaphysical calculation, interpretation, canonical-source choice, or `metaphysical-domain-engine` behavior changes. Current owner approval resolves the privileged-action scope decision. | `[NOT-APPLICABLE]` / `[CONFIRMED]` | No metaphysical scope audit is required. Separate HITL approval remains mandatory for any later push/deploy/release or secret operation. |

### Approved privileged route contract

**IN -- authenticated operation required for Admin dashboard operation**

| Method | Exact path | Boundary |
|---|---|---|
| `GET` | `/admin/auth/config` | Read authentication configuration only. |
| `POST` | `/admin/auth/google` | Google credential verification only; no mock-email request or fallback path. |
| `GET` | `/admin/catalog/summary` | Read summary only. |
| `GET` | `/admin/catalog` | Read catalog only. |
| `GET` | `/admin/catalog/source/:source_id` | Read one path-parameter-selected catalog source only. |
| `GET` | `/admin/grayzone` | Read gray-zone data, including supported `answered` query forms; query use does not widen the path or method. |
| `GET` | `/admin/finetune/status` | Read status only. |
| `GET` | `/admin/finetune/download` | Authenticated download only. |
| `GET` | `/admin/finetune/download-grayzone` | Authenticated gray-zone download only. |
| `GET` | `/admin/provider-pools` | Read provider-pool status only. |
| `GET` | `/hitl/stats` | Read HITL statistics only. |

**OUT -- must remain fail-closed**

- `POST /admin/grayzone/answer`
- `DELETE /admin/grayzone/answer`
- `POST /admin/finetune/export-grayzone`
- `POST /admin/finetune/merge`
- `POST /admin/finetune/trigger`
- Every other `/admin/*` or `/hitl/*` method/path, including wildcard, alias, prefix-confusion, and method-substitution admissions.
- Removing or hiding the corresponding UI controls in BSA-015 or QA-025. Future disabled-state, explanation, or removal UX requires a separately approved scope decision.

### Provenance decision and dependency graph

- The prior `d95783e -> d11b8f3 -> 5b261c5` candidate is `NON_TDD_RECONSTRUCTED` and blocked as admission evidence. `d11b8f3` is a source commit between the baseline and later candidate but lacks the exact `Test-Baseline: d95783eeff26e85874477146db2ccb0a61d24ce8` trailer. A trailer added only to `5b261c5` cannot repair that chain retrospectively.
- The old test/manifest may be referenced for history, but neither may be relabeled `TEST_BASELINE_VERIFIED` for this approved scope.

```text
ADMIN-REMED-BSA-015 (DONE: approved governance scope only)
  -> ADMIN-REMED-QA-025 (TODO: TEST-ONLY superseding baseline)
     -- must reach TEST_BASELINE_VERIFIED before any downstream admission
  -> ADMIN-REMED-DEV-035 (BLOCKED on QA-025 TEST_BASELINE_VERIFIED)
  -> ADMIN-REMED-REVIEW-045 (BLOCKED on QA-025 TEST_BASELINE_VERIFIED and DEV-035 DONE)
  -> ADMIN-REMED-OPS-055 (BLOCKED on QA-025 TEST_BASELINE_VERIFIED, REVIEW-045 DONE,
                          and separate owner authorization; push/deploy/release excluded now)
```

### QA-025 acceptance and stop contract

| Criterion | Required evidence | Stop threshold |
|---|---|---|
| Test-only ownership | New `tests/admin_production_ingress_scope_contract.test.mjs` and new `plans/test_provenance/ticket-admin-remed-qa-025-baseline.json` only; manifest names QA-025 and supersedes the old baseline without rewriting it. | Stop on any source, existing test/manifest, config, generated, runtime, worktree, remote, or external-system mutation. |
| Exact positive allowlist | Tests enumerate every IN method/path above, treat `:source_id` as a bounded segment, and cover supported `/admin/grayzone?answered=...` query forms. Google POST proves credential verification only and explicitly rejects any mock-email mode. | Stop if an IN path is omitted, broadened, or admitted without the required authentication contract. |
| Exact negative/fail-closed matrix | Tests enumerate the five named OUT mutations and representative method substitution, wildcard, alias, prefix-confusion, unknown `/admin/*`, and unknown `/hitl/*` cases; expected behavior has no backend forwarding or privileged response. | Stop if any excluded or unenumerated privileged path is forwarded/admitted, or if tests achieve coverage by hiding/removing UI controls. |
| Honest RED and negative evidence | From the clean parent, focused test execution returns the manifest-declared RED exit/fingerprint for the intended missing source behavior; a bounded negative-control run proves the test detects route widening or auth weakening. | Stop on GREEN-at-creation without an explained test-first failure, nondeterministic fingerprint, missing negative control, or evidence captured against a dirty/unbound parent. |
| Closed provenance | Manifest binds parent SHA, test SHA-256, command, expected exit, failure fingerprint, allowed future source paths, roles, and superseded artifact. The immutable test-only baseline commit passes the repository provenance guard and is recorded as `TEST_BASELINE_VERIFIED`. | Stop on hash/ancestry/path drift, co-committed source, schema/guard failure, or missing immutable baseline SHA. |
| Downstream trailer enforcement | QA handoff states that every later source commit in the candidate lineage must carry exact `Test-Baseline: <QA-025 immutable baseline SHA>` provenance and must descend from that baseline. | Stop/reclassify the candidate `NON_TDD_RECONSTRUCTED` if any intervening source commit lacks or mismatches the trailer. |

### Risks, recovery, waivers, blockers, and current stop

- **Waivers**: `NONE`.
- **Blockers**: QA-025 has not yet produced an immutable test-only SHA, RED/negative evidence, or verified manifest. Therefore DEV-035, REVIEW-045, and OPS-055 remain `BLOCKED`; OPS-055 additionally lacks current push/deploy/release authority.
- **Recovery**: preserve the old lineage as historical `NON_TDD_RECONSTRUCTED`; do not edit it into compliance. If QA-025 drifts from the exact matrix, discard only its unverified candidate artifacts and restart from the bound clean parent.
- **Current-ticket acceptance**: this record and the matching atomic handoff are the only changes; all nine dimensions carry evidence states; scope, dependencies, assumptions, acceptance, and stop conditions are exact; no implementation or production claim is made.
- **Current-ticket stop condition**: stop after persisting and diff-checking these two governance files. The only authorized next phase is QA-025 TEST-ONLY work under separate one-editor admission.

<!-- ADMIN-REMED-BSA-015:END -->

<!-- ADMIN-REMED-PLAN-001:START -->
## GRILL REPORT -- ADMIN-REMED-PLAN-001: Production Admin Data-Path Remediation

> **Superseded execution baseline**: `ADMIN-REMED-BSA-015` narrows privileged route admission and requires `ADMIN-REMED-QA-025=TEST_BASELINE_VERIFIED`. This older plan remains historical context and cannot admit source, review, or operations work.

**Recorded**: `2026-09-01T00:45:00+07:00` (Asia/Bangkok)
**Status**: `APPROVED`
**Authorized next phase**: `QA production-contract baseline only`, followed strictly by the dependency graph below.
**Request**: Restore the production Admin panel so its authorized data reads and rendered states work through every required production service.

### Context evidence

- `[CONFIRMED]` Scope is **production only**. Source, test, configuration, and deployment work is authorized only through the tickets below; no unrelated admin redesign, new session platform, secret rotation, publishing outside the remediation deploy, or metaphysical behavior change is in scope.
- `[CONFIRMED]` Production evidence: Vercel serves `admin.html` with HTTP `200`, but Vercel returns `404` for `/admin/*`; the Vercel gateway rejects the Admin API route. Direct HF core reads return `200` except `/admin/provider-pools`, which is absent from that deployed backend. Therefore document availability is not evidence that Admin data availability works.
- `[AUTO]` `public/admin.html` calls `/admin/catalog/summary`, `/admin/grayzone`, `/admin/finetune/status`, `/admin/catalog`, source detail, write actions, and auth routes. `project/admin_router.py` declares the Admin router and provider-pools route, while the deployed provider-pools absence must be treated as an independently verified production drift until corrected.
- `[AUTO]` `public/admin.html` and `project/static/admin.html` are divergent Admin static mirrors. `project/main.py` includes `admin_router`; this is route-registration evidence only, not Vercel gateway or deployed-backend proof.
- `[CONFIRMED]` Design constraint: every protected Admin data route must verify a Google ID token server-side and enforce the existing allowed-email policy. The implementation must not add a secret, session, or identity-platform dependency.

### Nine-dimension matrix

| ID | Result | Evidence state | Decision / remaining issue |
|---|---|---|---|
| D1 Scope boundary | Restore production Admin static-to-gateway-to-HF reads and authorized rendering for catalog, summary, gray-zone, fine-tune status, and provider pools. Reconcile the two Admin static mirrors. | `[CONFIRMED]` | Exclude new Admin features, unrelated API changes, client-only authorization, secret/session-system additions, and non-production release work. |
| D2 Requirement delta | The Vercel Admin API path must route to the deployed HF backend; the deployed backend must contain the provider-pools contract; the browser must send a verifiable Google ID token; the backend must reject missing, invalid, or unauthorized tokens. | `[CONFIRMED]` / `[AUTO]` | No static fallback or public data-route bypass is acceptable. |
| D3 Acceptance and stop conditions | The acceptance matrix binds pre-change production failure receipt, source/config regression, review, an exact deployed candidate, and post-deploy browser/API E2E. | `[CONFIRMED]` | Stop and retain evidence on any 404/5xx, wrong release identity, mirror drift, unauthenticated 2xx, invalid-token acceptance, unauthorized-email acceptance, or failed required Admin panel state. |
| D4 Inputs, constraints, dependencies | Requires the current Vercel and HF production targets, existing Google token-verification configuration and allowed-email policy, a deployable candidate, and browser-capable authorized test identity. | `[CONFIRMED]` | No secret inspection or creation belongs in this plan. A missing pre-existing token-verification input blocks deployment rather than permitting weaker auth. |
| D5 Architecture, ownership, handoff | Browser -> Vercel static Admin -> same-origin `/admin/*` gateway rewrite -> HF Docker Admin router. QA owns baseline/E2E evidence; one developer owns bound source/config paths; reviewer is read-only; DevOps owns remote deployment; BSA owns only plan/board. | `[CONFIRMED]` | Serial gates prevent test/source/config/deploy ownership collisions. |
| D6 Assumption register | Existing allowed-email policy and deployable Google ID-token verification are available without a new credential or session service. Direct HF `200` evidence is read-only diagnosis, not authorization to expose data routes. | `[CONFIRMED]` | If either implementation inspection disproves the supplied assumption, halt source/deploy and escalate; do not substitute email/mock/client-side fallback. |
| D7 Risk and recovery | Risks: proxy points to wrong backend, mirror mismatch, release drift, token verification defect, or data exposure. Recovery: preserve receipts; rollback only the exact Vercel/HF deployment to its recorded prior revision; keep protected routes fail-closed. | `[AUTO]` / `[CONFIRMED]` | No production mutation proceeds without an exact target and rollback revision. |
| D8 Budget and evidence strategy | DispatchDecision v1: ranks `3/3/3/1/3`; floor `gpt-5.6-sol/xhigh` planning exception; selected `codex1`; Tier 1 Green; `WRITE_GOVERNANCE`; `root-medium=true`; HITL approved; receipt binding required. | `[CONFIRMED]` | Receipts record URLs/path class, status, candidate SHA/revision, command/result, and redacted identity outcome only--never token material. |
| D9 Domain and HITL check | No metaphysical interpretation/calculation or source-domain decision changes. Production deployment remains a separately receipt-bound HITL execution checkpoint. | `[NOT-APPLICABLE]` | No metaphysical-domain HITL audit; normal deployment authority remains mandatory. |

### Target design and ordered execution

```text
Authorized Admin browser
  -> Vercel static admin.html (canonical mirror parity)
  -> same-origin /admin/* rewrite (no 404 gateway rejection)
  -> HF Docker Admin router (deployed provider-pools included)
  -> server-side Google ID-token verification + existing allowed-email policy
  -> permitted Admin data/rendered panels
```

```text
ADMIN-REMED-PLAN-001 (DONE: governance)
  -> ADMIN-REMED-QA-010 (frozen production baseline)
  -> ADMIN-REMED-DEV-020 (single source/config change set)
  -> ADMIN-REMED-REVIEW-030 (independent review)
  -> ADMIN-REMED-OPS-040 (receipt-bound Vercel/HF deployment)
  -> ADMIN-REMED-QA-050 (post-deploy authorized browser/API E2E)
  -> ADMIN-REMED-BSA-060 (truthful closure only)
```

### Acceptance matrix

| Criterion | Verification / stop threshold | Owner |
|---|---|---|
| Failure baseline is frozen across all required Admin services | Read-only receipts demonstrate current Vercel `admin.html` response, each Vercel `/admin/*` result, direct-HF comparison, provider-pools condition, static-mirror digests, and no secret/token output. Stop on unbound target or incomplete route inventory. | `qa_tester` |
| Corrected source/config preserves mirror and protected-route contracts | Focused automated tests prove both mirror files are byte-equivalent or generated from one canonical source; gateway rewrite covers the Admin inventory; backend routes require a valid Google ID token and existing allowed email; missing/invalid/unauthorized requests never receive data. Stop on client fallback, mock-login production path, or any failing test. | `developer` |
| Candidate is independently safe | Read-only review verifies exact path ownership, auth fail-closed behavior, route inventory, mirror parity, deploy manifest, and rollback identity. Stop on any data exposure, unreviewed path, or receipt gap. | `code_reviewer` |
| Production candidate is exact and reversible | DevOps deploys only the reviewed candidate to the declared Vercel and HF targets, records both resulting revisions, and retains the prior revisions. Stop/rollback on failed health, route, or identity check. | `devops` |
| Authorized Admin works end-to-end and remains protected | Post-deploy browser/API E2E receives valid authorized data/rendered states for catalog, summary, gray-zone, fine-tune status, and provider pools; unauthorized, malformed, and absent-token attempts are denied; Vercel route results bind to the deployed HF revision. Stop on any failed required panel or security assertion. | `qa_tester` |

### Risks, recovery, waivers, and closure

- **Recovery**: never turn Admin data routes public to recover availability. On a failed deploy/E2E check, preserve the receipt, roll back only the recorded Vercel/HF revisions, and return the affected ticket to `BLOCKED`.
- **Waivers**: `NONE`.
- **Blockers**: `NONE` for planning. `QA-010` must first prove the live route inventory; `OPS-040` may not deploy if its target, candidate revision, server-side token verification, or rollback revision is unbound.
- **Stop condition for this ticket**: this BSA activity is done when this bounded plan and the atomic tickets are persisted. It does not claim the production outage is fixed.

<!-- ADMIN-REMED-PLAN-001:END -->

<!-- GHA-20260901-BSA-001:START -->
## GRILL REPORT -- GHA-20260901-BSA-001: GitHub Actions Ruff F821 Repair

**Recorded**: `2026-09-01T00:17:08+07:00` (Asia/Bangkok)
**Status**: `APPROVED`
**Authorized next phase**: `QA baseline only` -- capture the red lint provenance before any source mutation.
**Request**: Repair the `main` GitHub Actions failure on SHA `f9f8048` (run `33418206471`): Ruff `F821`, undefined name `HybridRouter`, at `project/mcp_server.py:130`.

### Context evidence

- `[AUTO]` Local checkout is `main` at `f9f80487a5f01a176ce7c16d3f1657e2c8908e16` (`git rev-parse`, 2026-09-01); worktree was clean before this governance edit.
- `[AUTO]` `project/mcp_server.py:130` declares `def _get_router() -> "HybridRouter":`; the lazy local import and construction occur at lines 133-134. `HybridRouter` is defined in `project/api_router.py:554`.
- `[AUTO]` `.github/workflows/ci.yml:146` runs `ruff check project/ tests/ --select E9,F63,F7,F82 --exclude project/kaggle_kernel`.
- `[CONFIRMED]` Current-session owner authority covers the scoped repair lifecycle, including the later closure/archive action. The present BSA task is limited to `plans/plan.md` and `PROJECT_TASKS.md`; no source, test, workflow, archive, release-note, GitHub, secret, commit, push, deploy, or publish mutation is authorized in this intake action.

### Nine-dimension matrix

| ID | Result | Evidence state | Decision / remaining issue |
|---|---|---|---|
| D1 Scope boundary | Repair the cited Ruff `F821` in `project/mcp_server.py`; record and govern the repair sprint. Exclude unrelated lint debt and all workflow changes. | `[CONFIRMED]` | Resolved. Stable interfaces: MCP lazy router behavior and public module attributes. |
| D2 Requirement delta | Remove the undefined-name lint finding without masking it or broadening lint exclusions. | `[AUTO]` | Resolved; implementation technique is deliberately constrained by behavior, not prescribed. |
| D3 Acceptance and stop conditions | Baseline, focused lint, regression, independent review, main CI, and closure evidence are measurable below. | `[CONFIRMED]` | Resolved. Stop current BSA task after only the two owned documentation files change. |
| D4 Inputs, constraints, dependencies | Required: bound SHA/run/failure, local source context, CI Ruff command, QA provenance before mutation, and normal capacity/lease admission at dispatch. | `[AUTO]` / `[CONFIRMED]` | Resolved. No credentials or external system access required for intake. |
| D5 Architecture, ownership, handoff | QA owns baseline evidence; developer owns only `project/mcp_server.py`; DevOps owns CI/push verification; reviewer is read-only; BSA owns closure documents. | `[CONFIRMED]` | Resolved; serial dependency graph prevents concurrent ownership collisions. |
| D6 Assumption register | GitHub-run diagnosis, owner authority, and required branch are confirmed. The source repair must preserve lazy initialization and must not be a blanket suppression. | `[CONFIRMED]` | No pending material assumption. |
| D7 Risk and recovery | Risks: behavior/circular-import regression, wrong SHA/run, lint suppression, or a red post-push CI. Recovery: revert only the bound source commit, return to the recorded baseline, and halt on any failed gate. | `[AUTO]` | Resolved; no rollback action is performed in this phase. |
| D8 Budget and evidence strategy | DispatchDecision v1: scope=2, complexity=2, risk=2, ambiguity=1, evidence=2; floor `gpt-5.6-terra/high`; selected `codex2`; quota Tier 1 Green; `WRITE_GOVERNANCE`; policy v1. | `[CONFIRMED]` | Resolved. Evidence is bounded to SHA/run IDs, commands, exit status, and ASCII-tagged receipts; no secrets. |
| D9 Domain and HITL check | No metaphysical calculation, interpretation, source-domain conflict, or low-consensus decision is changed. `metaphysical-domain-engine` is out of scope. | `[NOT-APPLICABLE]` | No domain HITL audit required. Current-session owner approval is recorded for the scoped repair lifecycle. |

### Scope, assumptions, acceptance, and stop condition

**IN**: a minimal, behavior-preserving source repair for the cited F821; QA baseline and regression evidence; independent review; main-branch CI/push verification; then Rule 22 closure, archive, and `ReleaseNotes.md` synchronization.
**OUT**: unrelated code/test/workflow changes, lint-rule weakening or `# noqa` masking, GitHub configuration changes, credential/secret handling, deployment/publishing, and all metaphysical-domain behavior.
**Assumptions**: none pending. The cited GitHub failure and the owner-provided run/SHA are the baseline; any conflicting fresh evidence reopens D2/D3/D7 and halts progression.

| Acceptance criterion | Verification / stop threshold | Owner |
|---|---|---|
| Frozen red baseline names the exact F821, path, line, SHA, and CI-equivalent command | The receipt binds `f9f8048`, `33418206471`, and `project/mcp_server.py:130`; stop if mismatch. | `qa_tester` |
| Repair removes F821 without suppression, workflow edits, or lazy-router behavior loss | CI-equivalent Ruff command exits 0; focused MCP/router regression passes; stop on any failure or changed excluded file. | `developer` |
| Candidate is independently safe and reviewable | Independent reviewer returns PASS on diff, scope, rollback, and receipt completeness; stop on any unresolved risk. | `code_reviewer` |
| Main verification is tied to the repaired commit | Authorized push is followed by a green GitHub Actions run on `main` for that exact commit; stop on wrong branch, stale run, or red run. | `devops` |
| Sprint closure is truthful | Every sprint ticket is independently verified `DONE`; then archive the completed planning artifact and update `ReleaseNotes.md`; stop before closure if any ticket is not DONE. | `business_analyst` |

### Risks, recovery, waivers, and blockers

- **Recovery**: on a source or CI failure, revert only the repair commit after preserving its SHA and receipts; do not touch workflow configuration or unrelated files.
- **Waivers**: `NONE`.
- **Blockers**: `NONE` for intake. Dispatch remains fail-closed on normal capacity/lease admission and the QA baseline receipt.
- **Next question**: `NONE`.

### Approved scope expansion -- AI Safety Audit and Production Synthetic Monitoring

**Recorded**: `2026-09-01T00:17:08+07:00` (Asia/Bangkok)
**Gate**: `APPROVED FOR READ-ONLY TRIAGE ONLY`
**New evidence**: AI Safety Audit run `33418206430` and Unified CI run `33418206373` on `f9f8048` identify 10 unique pytest failures across seven logical groups: quota-handoff markers (2), RAG chunk baseline (1), context-handoff wording (1), distillation timestamp (1), HF manual-gradient digest (1), AGY capacity contract expectations (3), and CI-only `project/tests/test_local_release_runner_contract.py::test_non_release_hermes_qa_and_sync_orchestration_remains_callable` (1; expected `['CALL pytest', 'CALL tee']`, actual `['', 'CALL pytest']`). Production Synthetic Monitoring run `33418604094` diagnosis found a forbidden legacy `commit` field/version `1.0.0.93f51cf` from HF immutable revision `90cb95cb...`; Vercel matches.

| Workstream | Scope and evidence | Authorized phase | Hard stop |
|---|---|---|---|
| `GHA-20260901-AISAFETY` | Read-only, one-ticket-per-logical-group triage that binds every failing node ID, actual/expected value, candidate owner/path, and `f9f8048`; then frozen-baseline QA/source correction lanes. | Seven independent read-only triage tickets only. | No test expectation, fixture, source, skill/rule, generated-agent, workflow, or release change before triage completes and a frozen correction map is reviewed. |
| `GHA-20260901-SYNTHMON` | Diagnosis is DONE: HF serves a forbidden legacy commit/version from immutable revision `90cb95cb...`; Vercel matches. | `NEEDS_HITL` remediation planning only. | No deploy, publish, remote mutation, or release claim until green CI, `PRIOR_TREE_UNAVAILABLE` resolution, candidate manifest/receipt, exact HF target, rollback revision, and current-session authorization are bound. |

**Expanded acceptance**: Every AI Safety triage receipt must account for all 10 failures and preserve the pre-correction output. Corrections require a frozen baseline, exact-path one-editor assignment, independent review, and an exact-SHA green CI run. Synthetic Monitoring diagnosis is complete; remediation remains `NEEDS_HITL` until green CI, `PRIOR_TREE_UNAVAILABLE` resolution, candidate manifest/receipt, exact HF target, rollback revision, and current-session authorization are bound. Vercel remains untouched.

**Expanded risks and recovery**: Treat a passing HTTP status as insufficient release identity evidence. Preserve failed remote and test receipts; on any incorrect correction, revert only its bound commit and retain the original baseline. No archive is authorized by this scope expansion.

<!-- GHA-20260901-BSA-001:END -->

<!-- AGILE-GOVERNANCE-SYNC-MRMAP:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-MRMAP-001)

**Recorded**: `2026-08-31T23:20:00+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `COMPLETED / SEALED`  
**Current Active Sprint**: Sprint SPRINT-METAPHYSICS-ROADMAP-001 (Five-Branch Metaphysics Roadmap & Computational Core across Steps 1-4)  
**Sprint Authority**: [`plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md`](plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md)  
**Active Milestones**: Sprint Sealed (All Steps 1-4 Completed)  
**Status Note**: All 16 tickets (`MRMAP-S1-010` through `MRMAP-S4-040`) are 100% DONE. Sprint SPRINT-METAPHYSICS-ROADMAP-001 is COMPLETED and sealed at 2026-08-31T23:30:00+07:00.  

### Synchronized Ticket Status Transitions (Sprint SPRINT-METAPHYSICS-ROADMAP-001 Final Seal)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `MRMAP-S1-010` | `DONE` | `DONE` | `domain_master` | `scripts/ocr_pdf_gemini.py`, `project/rag/obsidian_vault/` |
| `MRMAP-S1-020` | `DONE` | `DONE` | `developer` | `project/rag/ingest_vault.py` |
| `MRMAP-S1-030` | `DONE` | `DONE` | `developer` | `project/rag/vector_store.py` |
| `MRMAP-S1-040` | `DONE` | `DONE` | `qa_tester` | `project/tests/test_ingest_vault.py` |
| `MRMAP-S2-010` | `DONE` | `DONE` | `developer` | `project/core/tai_yi_engine.py`, `project/core/liu_ren_engine.py`, `project/core/qi_men_engine.py` |
| `MRMAP-S2-020` | `DONE` | `DONE` | `developer` | `project/core/bazi_engine.py`, `project/core/zi_wei_engine.py`, `project/core/qi_zheng_engine.py` |
| `MRMAP-S2-030` | `DONE` | `DONE` | `developer` | `project/core/iching_engine.py`, `project/core/liu_yao_engine.py`, `project/core/mei_hua_engine.py`, `project/core/xuan_kong_engine.py`, `project/core/san_he_engine.py`, `project/core/mian_xiang_engine.py` |
| `MRMAP-S2-040` | `DONE` | `DONE` | `developer` | `project/core/ze_ji_engine.py`, `project/core/thai_vedic_engine.py`, `project/core/western_uranian_engine.py`, `project/core/numerology_engine.py` |
| `MRMAP-S3-010` | `DONE` | `DONE` | `developer` | `project/rag/dataset_builder.py`, `project/rag/jsonl_exporter.py` |
| `MRMAP-S3-020` | `DONE` | `DONE` | `domain_master` | `project/data/synthetic_corpus_generator.py`, `project/data/sharegpt_dataset.jsonl` |
| `MRMAP-S3-030` | `DONE` | `DONE` | `developer` | `project/rag/external_finetune.py`, `project/data/sharegpt_dataset.jsonl` |
| `MRMAP-S3-040` | `DONE` | `DONE` | `devops` | `scripts/kaggle_notebook_manager.py`, `scripts/post_train_fuse.py` |
| `MRMAP-S4-010` | `DONE` | `DONE` | `developer` | `project/mcp_server.py`, `project/schemas/mcp_tools_v1.py` |
| `MRMAP-S4-020` | `DONE` | `DONE` | `developer` | `project/mcp_server.py`, `project/tests/test_e2e_mcp_svg.py` |
| `MRMAP-S4-030` | `DONE` | `DONE` | `developer` | `project/core/svg_generator.py`, `project/core/chart_bundler.py`, `project/static/css/glassmorphism_charts.css` |
| `MRMAP-S4-040` | `DONE` | `DONE` | `developer` | `project/static/js/chart_modal.js`, `project/tests/test_button_regression.py` |

---

<!-- AGILE-GOVERNANCE-SYNC-MRMAP:END -->

<!-- AGILE-GOVERNANCE-SYNC-META3:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-META3-003)

**Recorded**: `2026-08-31T22:17:30+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy2)  
**Gate**: `APPROVED`  
**Current Active Sprint**: Sprint META-PLAN-003 (MCP Full 16-Discipline Server Integration, Metaphysics Fine-Tuning Dataset Pipeline, and Glassmorphism Visual Endpoints across Milestones M0-M5)  
**Sprint Authority**: [`plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md`](plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md)  
**Active Milestones**: Sprint Sealed (All Milestones M0-M5 Completed)  
**Status Note**: All 24 tickets (`META3-M0-010` through `META3-M5-040`) are 100% DONE. Sprint META-PLAN-003 is COMPLETED and sealed at 2026-08-31T23:00:00+07:00.  

### Synchronized Ticket Status Transitions (Sprint META-PLAN-003 Wave 2 Admission)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `META3-M0-010` | `DONE` | `DONE` | `business_analyst` | `plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md` |
| `META3-M0-020` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m0_baseline_report.json` |
| `META3-M0-030` | `DONE` | `DONE` | `developer` | `project/schemas/mcp_tools_v1.py` |
| `META3-M0-040` | `DONE` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_003/m0_security_pre_impl.json` |
| `META3-M1-010` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-040` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M2-010` | `DONE` | `DONE` | `domain_master` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-040` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M3-010` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-040` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M4-010` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-020` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-030` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-040` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_integration_e2e_report.json` |
| `META3-M5-010` | `DONE` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-020` | `DONE` | `DONE` | `business_analyst` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-030` | `DONE` | `DONE` | `devops` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-040` | `DONE` | `DONE` | `orchestrator` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-META3:END -->

<!-- AGILE-GOVERNANCE-SYNC-META2:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-META2-002)

**Recorded**: `2026-08-31T22:00:00+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `COMPLETED / SEALED`  
**Current Active Sprint**: Sprint META-PLAN-002 (Milestones M0-M5 all 24 tickets 100% DONE & SEALED)  
**Sprint Authority**: [`plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md`](plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md)  
**Active Milestone**: Sprint Sealed (All Milestones M0-M5 Completed)  
**Status Note**: All 24 tickets (`META2-M0-010` through `META2-M5-040`) are `DONE`. Sprint META-PLAN-002 is 100% DONE & SEALED with comprehensive test verification (133/133 unit tests pass), 6-domain benchmark alignment (100% pass rate, 100/100 score), 18 responsive dynamic SVG visualizers, 0 secret leaks across 1,967 files, and 100% AI agent ecosystem parity.  

### Synchronized Ticket Status Transitions (Sprint META-PLAN-002 Final Seal)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `META2-M0-010` | `DONE` | `DONE` | `business_analyst` | `plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md` |
| `META2-M0-020` | `READY` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M0-030` | `READY` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M0-040` | `READY` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M1-010` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-040` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M2-010` | `BLOCKED` | `DONE` | `domain_master` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-040` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M3-010` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-040` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M4-010` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-020` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-030` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-040` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M5-010` | `BLOCKED` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-020` | `BLOCKED` | `DONE` | `business_analyst` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-030` | `BLOCKED` | `DONE` | `devops` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-040` | `BLOCKED` | `DONE` | `orchestrator` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-META2:END -->

<!-- AGILE-GOVERNANCE-SYNC-20260831:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-009)

**Recorded**: `2026-08-31T21:36:08+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `APPROVED`  
**Current Active Sprint**: Sprint BROKER-PLAN-001 (Milestones B0-B6 all 29 tickets 100% DONE & SEALED), IDQ Operational (AUTH-02 SEALED & COMPLETED), Context Handoff v1 (CORE/ADAPTERS/POLICY/SYNC/QA/REVIEW DONE, INTEGRATION HOLD)  
**B6 Status Note**: Milestone B6 tickets (`BRK-B6-010`, `BRK-B6-020`, `BRK-B6-030`) are now `DONE`. Sprint BROKER-PLAN-001 is 100% DONE & SEALED. All 29 tickets are recorded as DONE with evidence references.  

### Synchronized Ticket Status Transitions (Wave 4C Completions: B6 Capacity Certification, Rollback, Closure)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `BRK-B5-030` | `READY` | `DONE` | `agy_circuit_operator` | `b5-agy-circuit.json` |
| `BRK-B5-050` | `BLOCKED` | `DONE` | `agy1_admission_operator` | `b5-agy1-admission.json` |
| `BRK-B5-060` | `BLOCKED` | `DONE` | `agy2_admission_operator` | `b5-agy2-admission.json` |
| `BRK-B5-070` | `BLOCKED` | `DONE` | `agy3_admission_operator` | `b5-agy3-admission.json` |
| `BRK-B5-075` | `BLOCKED` | `DONE` | `agy4_admission_operator` | `b5-agy4-admission.json` |
| `BRK-B5-080A` | `BLOCKED` | `DONE` | `codex1_admission_operator` | `b5-codex1-admission.json` |
| `BRK-B5-080B` | `BLOCKED` | `DONE` | `codex2_admission_operator` | `b5-codex2-admission.json` |
| `BRK-B5-080C` | `BLOCKED` | `DONE` | `codex3_admission_operator` | `b5-codex3-admission.json` |
| `BRK-B6-010` | `READY` | `DONE` | `broker_qa_tester` | `b6-capacity-certification.json` |
| `BRK-B6-020` | `READY` | `DONE` | `broker_qa_tester` | `b6-rollback-drill.json` |
| `BRK-B6-030` | `READY` | `DONE` | `business_analyst` | `b6-sprint-closure.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-20260831:END -->

## 🏛️ Master Architecture Specifications & System Topology

### 1. 🔮 Classical Metaphysics Computational Core (16 Disciplines)
The HoroConsultant engine implements deterministic mathematical modeling across 16 classical systems in pure Python with Rust PyO3 acceleration:
- **San Shi (三式)**:
  - `TaiYiEngine`: 16-path celestial star palaces, 9-palace matrix, epoch cycle boundaries (`project/core/tai_yi_engine.py`).
  - `LiuRenEngine`: 4 lessons (四課), 3 transmissions (初傳/中傳/末傳), 12 heavenly generals, noble spirit day/night rules (`project/core/liu_ren_engine.py`).
  - `QiMenEngine`: 24 solar terms, Yang/Yin Dun 1-9 Ju, 9 palaces, 8 doors, 9 stars, 8 deities (`project/core/qi_men_engine.py`).
- **Ming Xue (命學)**:
  - `BaZiEngine`: True Solar Time calculation ($TST = LMT + EoT$), midnight Zi hour early/late split, Lichun solar term boundaries, Ten Gods, Hidden Stems, Da Yun luck cycles (`project/core/bazi_engine.py`).
  - `ZiWeiEngine`: 12 Palaces, Ming/Shen Gong, 5 Element Bureaus, 14 Major Stars, 4 Si Hua transformations (`project/core/zi_wei_engine.py`).
  - `QiZhengSiYuEngine`: 7 governors, 4 shadow stars (Rahu, Ketu, Yuebei, Ziqi), 28 lunar mansions, Swiss Ephemeris (`project/core/qi_zheng_engine.py`).
- **Pu Shi (卜筮)**:
  - `IChingEngine`: Full 64 Hexagram lookup, dynamic moving lines 6/7/8/9, all-moving and all-static transitions (`project/core/iching_engine.py`).
  - `LiuYaoEngine`: Na Jia 6-line branch assignment, Shi/Ying line placement, Five Relatives (五親), Six Spirits (六神) (`project/core/liu_yao_engine.py`).
  - `MeiHuaEngine`: Ti/Yong 5-element dynamics, mutual (互卦) and transformed (變卦) hexagrams (`project/core/mei_hua_engine.py`).
- **Xiang Xue & Ze Ji (相學 / 擇吉)**:
  - `XuanKongEngine`: Period 9 (2024–2043), 24 mountains, sitting/facing star matrices, compass boundary angle wrapping (`project/core/xuan_kong_engine.py`).
  - `SanHeEngine`: 12 Life Stages Water Method (長生十二宮水法), 3 harmonies (`project/core/san_he_engine.py`).
  - `ZeJiEngine`: Imperial Calendar Date Selection, 12 Duty Officers (建除十二神), Year/Month Breaker clash detection (`project/core/ze_ji_engine.py`).
  - `MianXiangEngine`: 5-element face shapes, 12 facial palaces, 100-year age fortune flow (`project/core/mian_xiang_engine.py`).
- **Extended Astrologies & Numerology**:
  - `ThaiVedicEngine`: 12-Rashi Lagna, 8 Maha Thaksa Sri/Kalakini, 27 Nakshatras, Vimshottari Dasha (`project/core/thai_vedic_engine.py`).
  - `WesternUranianEngine`: Tropical planetary positions, 8 Uranian TNPs, midpoint formula $A+B-C$ (`project/core/western_uranian_engine.py`).
  - `NumerologyEngine`: Satta-Lek 7-Base 4-row matrix, Chaldean scoring (`project/core/numerology_engine.py`).

### 2. 🔌 Model Context Protocol (MCP) Server Architecture
The MCP Server (`project/mcp_server.py`) provides stdio JSON-RPC 2.0 transport conforming to MCP Specification 2024-11-05:
- **36-Tool Registry**:
  - 16 Calculation Engine Tools (`calculate_bazi`, `calculate_ziwei`, `calculate_qimen`, `calculate_liuren`, `calculate_taiyi`, `calculate_iching`, `calculate_liuyao`, `calculate_meihua`, `calculate_xuankong`, `calculate_sanhe`, `calculate_zeji`, `calculate_mianxiang`, `calculate_thaivedic`, `calculate_western_uranian`, `calculate_numerology`, `calculate_qizheng`).
  - 18 Dynamic SVG Visualizer Tools (`render_bazi_svg`, `render_ziwei_svg`, etc.).
  - Question Router Tool (`route_metaphysics_question`).
  - Multi-Agent Consensus Debate Tool (`debate_metaphysics_consensus`).
- **FastMCP Protocol Bridge**: Schema auto-generation, Pydantic type safety, and zero-overhead JSON-RPC dispatch.

### 3. 📚 Metaphysics Fine-Tuning Dataset & RAG Architecture
- **Obsidian Vault & FAISS Vector Store**: 11 classical Chinese treatises ingested, parsed, chunked, and indexed with semantic retrieval (`project/rag/vector_store.py`).
- **1,050-Dialogue ShareGPT Corpus**: Multi-turn consultation dialogues covering 16 disciplines × 6 domains (`Career`, `Wealth`, `Love`, `Health`, `Timing`, `Remediation`) with classical treatise citations (`project/data/sharegpt_dataset.jsonl`).
- **Format Exporters**: Automated export to ShareGPT, MLX, Unsloth, and Kaggle notebook training pipelines (`project/rag/external_finetune.py`, `scripts/kaggle_notebook_manager.py`).

### 4. 🎨 Glassmorphism Visual Rendering System
- **Dynamic SVG Generator**: 18 dynamic SVG visualizers (`project/core/svg_generator.py`) delivering high-DPI, XML-escaped responsive chart cards.
- **Glassmorphism CSS Design System**: Dark-mode Five Elements color tokens, glass cards, tooltips, responsive breakpoints (`project/static/css/glassmorphism_charts.css`).
- **Chart Bundler & Multi-Format Exporter**: Export API supporting SVG, PNG, and PDF outputs (`project/core/chart_bundler.py`).
- **Interactive Frontend Modal**: Pan/zoom viewer, tabbed 16-discipline navigation, keyboard shortcuts (`project/static/js/chart_modal.js`).

### 5. 🛡️ Agile Governance & Multi-Account Broker Architecture
- **Rule 21 (Agile Governance)**: Fail-closed capacity admission, 3 active lanes per alias ceiling, one-editor-per-file concurrency guard (`.agents/rules/21-agile-governance.md`).
- **Rule 22 (Plan Completion & Archival Mandate)**: Mandatory archival of completed plans, `/plans/` directory cleanliness, and `ReleaseNotes.md` synchronization (`.agents/rules/22-plan-completion-and-release-notes.md`).
- **macOS Keychain Account Broker**: Swift keychain bridge with Python wrapper (`scripts/ai_account_keychain_broker.swift`, `scripts/agent_broker_wrapper.py`).

---

## 🗄️ Comprehensive Archived Plans Directory Index

All completed sprint specifications, historical GRILL reports, and task boards have achieved zero-active state and are archived per Rule 22:

| Sprint / Release | Archive Directory | Archived Planning Documents |
|---|---|---|
| **Metaphysics Roadmap** | [`plans/archive/2026-08-31-metaphysics-roadmap/`](plans/archive/2026-08-31-metaphysics-roadmap/) | [`metaphysics_learning_roadmap.md`](plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md) |
| **META-PLAN-003** | [`plans/archive/2026-08-31-meta-plan-003/`](plans/archive/2026-08-31-meta-plan-003/) | [`meta_plan_003_mcp_dataset_integration_spec.md`](plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md) |
| **META-PLAN-002** | [`plans/archive/2026-08-31-meta-plan-002/`](plans/archive/2026-08-31-meta-plan-002/) | [`meta_plan_002_metaphysics_deepening_spec.md`](plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md)<br>[`question_forecast_alignment_spec.md`](plans/archive/2026-08-31-meta-plan-002/question_forecast_alignment_spec.md) |
| **BROKER-PLAN-001** | [`plans/archive/2026-08-31-broker-plan-001/`](plans/archive/2026-08-31-broker-plan-001/) | [`broker_atomic_tickets_20260831.md`](plans/archive/2026-08-31-broker-plan-001/broker_atomic_tickets_20260831.md)<br>[`account_broker_installation_runbook_20260831.md`](plans/archive/2026-08-31-broker-plan-001/account_broker_installation_runbook_20260831.md) |
| **Release v1.3.0** | [`plans/archive/2026-08-31-release-v1.3.0/`](plans/archive/2026-08-31-release-v1.3.0/) | [`release_atomic_tickets_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/release_atomic_tickets_20260831.md)<br>[`release_atomic_ticket_audit_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/release_atomic_ticket_audit_20260831.md)<br>[`agile_governance_refactor_spec_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/agile_governance_refactor_spec_20260831.md)<br>[`native_lane_capacity_loadtest_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/native_lane_capacity_loadtest_20260831.md)<br>[`RESTART_HANDOFF.md`](plans/archive/2026-08-31-release-v1.3.0/RESTART_HANDOFF.md)<br>[`todo_tasks_plan.md`](plans/archive/2026-08-31-release-v1.3.0/todo_tasks_plan.md) |
| **Historical Archive** | [`plans/archive/2026-08-31-historical-plans/`](plans/archive/2026-08-31-historical-plans/) | [`historical_plans_archive.md`](plans/archive/2026-08-31-historical-plans/historical_plans_archive.md)<br>[`historical_tasks_archive.md`](plans/archive/2026-08-31-historical-plans/historical_tasks_archive.md) |
