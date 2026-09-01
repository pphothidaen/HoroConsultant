# HoroConsultant — Master Agile Plan & Architecture Specifications

> **Repository**: `pphothidaen/HoroConsultant`  
> **Authority**: Master Orchestrator (`orchestrator`) & Business System Analyst (`business_analyst`)  
> **Governance Enforcement**: Rule 21 (Agile Governance) & Rule 22 (Plan Completion & Archival Mandate)  
> **Last Synchronized**: 2026-08-31T23:40:00+07:00 (Asia/Bangkok)  

---

<!-- ADMIN-REMED-PLAN-001:START -->
## GRILL REPORT -- ADMIN-REMED-PLAN-001: Production Admin Data-Path Remediation

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
