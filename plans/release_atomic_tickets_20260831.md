# Source-of-Truth Atomic Release Ticket & Milestone Board

- **Document ID**: `REL-ATOMIC-001`
- **Timestamp**: `2026-08-31T09:26:00+07:00` (Asia/Bangkok)
- **Governance Standard**: Fail-Closed Release Governance v2 / Rule 11 / Rule 18 / Agile Governance v1
- **Author / Lane**: `agy1` (Gemini 3.7 Flash - Medium)
- **Status**: `READY_TO_VALIDATE`

---

## 1. DispatchDecision v1

```text
DispatchDecision v1: scope=1 complexity=1 risk=1 ambiguity=1 evidence=1; quality floor medium; selected agy1 / Gemini 3.7 Flash (Medium); quota healthy; work_mode write_docs; policy adaptive-model-effort-routing v1; root-medium state user-authorized planning; status READY_TO_VALIDATE.
```

---

## 2. Lane Capacity & Provider Quota Enforcement

### 2.1 Concurrency Limits & Repository Hard Caps
- **User Preference Ceiling**: 4 concurrent lanes.
- **Repository Hard Limit**: **3 concurrent lanes** (`max_workers = 3` strictly enforced by `.agents/config/full_capacity_guard.v2.json` and `scripts/multiagent_capacity.py`).
- **Policy Enforcement**: Fail-closed. Repository hard cap of 3 strictly overrides user ceiling of 4.
  - **`agy1` Allocation**: Max 3 concurrent worker slots.
  - **`agy2` Allocation**: Max 3 concurrent worker slots.
- **Cross-Lane Conflict Prevention**: Strict one-editor-per-file rule. Disjoint writable file sets enforced per lane. No shared file modifications without serial dependency handoff.

### 2.2 Quota-Check Command Patterns
Exact command patterns to execute for independent quota verification across governed account aliases:

```bash
# Account 1 (agy1) - Provider Quota Probe
agy1 --model "Gemini 3.7 Flash (Medium)" --dangerously-skip-permissions --print "/usage"

# Account 2 (agy2) - Provider Quota Probe
agy2 --model "Gemini 3.7 Flash (Medium)" --dangerously-skip-permissions --print "/usage"
```

*Identity & Isolation Axiom*: Identical quota values never prove shared identity, and current distinct values support but do not authenticate separate aliases. Each account alias executes in an independent session context with separate provider-reported telemetry. Never combine quota bands across accounts.

### 2.3 Current Provider Quota State (Recorded `2026-08-31` Asia/Bangkok)
- **`agy1` Allocation**:
  - **Gemini Weekly Remaining**: `66%`
  - **Gemini Five-Hour Window Remaining**: `86%`
  - **Claude / GPT Five-Hour Window Remaining**: `100%`
  - **Health Assessment**: **HEALTHY** (well above the 10.0% fail-closed throttling boundary).
- **`agy2` Allocation**:
  - **Gemini Weekly Remaining**: `87%`
  - **Gemini Five-Hour Window Remaining**: `97%`
  - **Claude / GPT Five-Hour Window Remaining**: `100%`
  - **Health Assessment**: **HEALTHY** (well above the 10.0% fail-closed throttling boundary).

### 2.4 Evidence Boundary & Process Deviation Accounting
- **Documentation Evidence Boundary**: Documentation-only lanes are strictly bounded to read-only `git status` and `git diff` operations to validate their assigned files.
- **Process Deviation Classification**: Both earlier documentation lanes executed test runners, security scanners, ecosystem sync scripts, and provenance verification commands (`pytest tests/test_idq_mvp_080_operational_provider.py`, `python3 scripts/sync_ai_agent_ecosystem.py --check`, `python3 project/core/code_reviewer.py --scan-secrets`, `pytest tests/test_publish_space_hf.py ...`, and `python3 scripts/test_provenance_guard.py verify-pr`) outside the requested documentation-only evidence boundary.
- **Child-Attributed Observations**: Factual outputs from these runs (300 passing operational provider tests, 0 secret leaks across 3,591 files, 12 synchronized platform files, 59 passing packaging contract tests) are preserved as child-attributed observations.
- **Status Reconciliation**: Work is marked DONE only when verifiable git commits exist. Parallel lane completed commit `dc1324ff63cfb10312fa3fb58238dd8017d44861` reconciling test provenance manifest (`REL-M1-003`). `REL-M1-004` is unblocked and set to `READY` for formal QA pass on clean committed tree. Premature `DONE` claims in M2 without prerequisite milestone completion remain downgraded to `BLOCKED`.

---

## 3. Milestone Rollups

| Milestone ID | Description | Total | Done | Ready | Doing | Blocked | Remaining |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **M0** | Branch Consolidation & Test Baseline Setup | 4 | 4 | 0 | 0 | 0 | 0 |
| **M1** | IDQ Operational Provider & Context Handoff Verification | 4 | 3 | 1 | 0 | 0 | 1 |
| **M2** | Release Governance, Safety & PR Harmonization | 7 | 0 | 0 | 0 | 7 | 7 |
| **M3** | Pre-Deployment Verification & Staging | 4 | 0 | 0 | 0 | 4 | 4 |
| **M4** | Production Deployment & Observability Sign-Off | 4 | 0 | 0 | 0 | 4 | 4 |
| **M5** | Agile Governance Implementation & Enforcement | 7 | 1 | 1 | 0 | 5 | 6 |
| **TOTAL** | **Comprehensive Release & Governance Lifecycle** | **30** | **8** | **2** | **0** | **20** | **22** |

*Summary*: 8 tickets DONE (`REL-M0-001` through `REL-M0-004`, `REL-M1-001`, `REL-M1-002`, `REL-M1-003`, `REL-M5-001`), 2 tickets READY for immediate dispatch (`REL-M1-004`, `REL-M5-002`), 0 tickets DOING, and 20 tickets BLOCKED by predecessor dependencies or awaiting HITL gates.

---

## 4. Dispatch-Ready Queue

Tickets ready for immediate dispatch or active execution, sorted by:
1. **Severity** (`CRITICAL` > `HIGH` > `MEDIUM` > `LOW`)
2. **Effort** (`XS` < `S` < `M` < `L` < `XL`)
3. **ASCII Ticket ID**

| Priority | Ticket ID | Milestone | Status | Severity | Effort | Owner Alias / Role | Writable Ownership | Objective Summary |
|:---:|---|:---:|:---:|:---:|:---:|---|---|---|
| **1** | `REL-M1-004` | M1 | `READY` | CRITICAL | S | `agy2 / qa_tester` | None (Read-only test execution) | Execute formal focused pytest suite on operational provider on clean committed tree. |
| **2** | `REL-M5-002` | M5 | `READY` | HIGH | S | `agy2 / qa_tester` | `plans/test_provenance/agile-governance-baseline-20260831.json`, `tests/test_agile_governance_guard.py` | Create test-only baseline and provenance manifest for Agile governance and multi-agent capacity validation. |

*(All subsequent tickets in M2 through M5 remain BLOCKED until `REL-M1-004` and `REL-M5-002` are completed and committed).*

---

## 5. Master Atomic Tickets Specification

### Milestone M0: Branch Consolidation & Test Baseline Setup (DONE)

#### `REL-M0-001`
- **Milestone**: M0
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: M
- **Owner**: `agy1 / developer`
- **Writable Ownership**: Git working tree / branch refs
- **Dependencies**: None
- **Objective**: Consolidate development branch `temp/merge-all-branches` cleanly into local `main`.
- **Acceptance Criteria**: Fast-forward or clean recursive merge with 0 merge conflicts, preserving 28 files and 2,074 insertions.
- **Evidence Command / Artifact**: Commit `752cda4c15422ce693ffb5c2b8b76423b9d39059`; `git log -1 752cda4`.
- **Stop Condition**: Stop on any unresolvable merge conflict or historical commit loss.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M0-002`
- **Milestone**: M0
- **Status**: `DONE`
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy1 / devops`
- **Writable Ownership**: Git remote refs
- **Dependencies**: `REL-M0-001`
- **Objective**: Clean up deleted temporary branches while preserving remote immutable recovery audit anchor.
- **Acceptance Criteria**: `temp/merge-all-branches` deleted locally and remotely; local `recovery/pre-test-provenance-20260827` deleted; `origin/recovery/pre-test-provenance-20260827` preserved at commit `ebfeee9`.
- **Evidence Command / Artifact**: `git branch -a`; `git rev-parse origin/recovery/pre-test-provenance-20260827`.
- **Stop Condition**: Stop if remote recovery anchor cannot be verified at `ebfeee9`.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M0-003`
- **Milestone**: M0
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: S
- **Owner**: `agy1 / qa_tester`
- **Writable Ownership**: `plans/test_provenance/merge-all-branches-20260831.json`
- **Dependencies**: `REL-M0-001`
- **Objective**: Create and anchor test provenance manifest for consolidated merge baseline.
- **Acceptance Criteria**: Manifest complies with `test-provenance-v1` schema with exact SHA-256 digests of test suites.
- **Evidence Command / Artifact**: Commit `377e01a`; file [plans/test_provenance/merge-all-branches-20260831.json](file:///Users/kimlenglim/Project/HoroConsultant/plans/test_provenance/merge-all-branches-20260831.json).
- **Stop Condition**: Stop if SHA-256 hashes do not match disk files.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M0-004`
- **Milestone**: M0
- **Status**: `DONE`
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy1 / developer`
- **Writable Ownership**: Git local refs
- **Dependencies**: `REL-M0-001`, `REL-M0-002`
- **Objective**: Merge PR branch `merge/all-to-main-20260831` into local `main` and delete local tracking branch.
- **Acceptance Criteria**: `main` contains all commits from PR branch; local `merge/all-to-main-20260831` deleted.
- **Evidence Command / Artifact**: Commit `752cda4`; `git branch --list merge/all-to-main-20260831` returns empty.
- **Stop Condition**: Stop if local `main` diverges from expected commit tree.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

---

### Milestone M1: IDQ Operational Provider & Context Handoff Verification (IN PROGRESS)

#### `REL-M1-001`
- **Milestone**: M1
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: L
- **Owner**: `agy2 / developer`
- **Writable Ownership**: `scripts/multiagent_idq_mvp_080_operational.py`
- **Dependencies**: `REL-M0-004`
- **Objective**: Implement operational provider executor replacing placeholder `NotImplementedError` with process supervision, stream buffers, and durable queue handling.
- **Acceptance Criteria**: Complete implementation supporting `agy1`, `agy2`, and `codex` runtime providers with bounded memory buffers.
- **Evidence Command / Artifact**: Commit `0a4c13ddd9bf60dc24f0129716c67dec299068cc`; 1,281 lines added.
- **Stop Condition**: Stop if stream buffer overflows or process termination leaks child processes.
- **Attempt**: 2 (rescued after initial session connector timeout).
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M1-002`
- **Milestone**: M1
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: M
- **Owner**: `agy2 / developer`
- **Writable Ownership**: `scripts/context_handoff.py`, `.agents/config/context_handoff_v1.json`, `.agents/rules/20-context-handoff.md`
- **Dependencies**: `REL-M0-004`
- **Objective**: Implement and synchronize Cross-Runtime Context Handoff v1 engine and declarative governance rules.
- **Acceptance Criteria**: Deterministic snapshot and rehydration with standard library only; all platform mirrors aligned.
- **Evidence Command / Artifact**: Commit `0a4c13d`; 22 files synchronized, 2,311 insertions.
- **Stop Condition**: Stop if external third-party dependencies are required in `scripts/context_handoff.py`.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M1-003`
- **Milestone**: M1
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: XS
- **Owner**: `agy2 / developer`
- **Writable Ownership**: `plans/test_provenance/idq-mvp-080-context-oracle-correction-20260831.json`, `plans/test_provenance/merge-all-branches-20260831.json`
- **Dependencies**: `REL-M1-001`, `REL-M1-002`
- **Objective**: Correct metadata errors in staged test provenance manifest to satisfy `scripts/test_provenance_guard.py staged` and commit to Git.
- **Acceptance Criteria**:
  1. Add `supersedes: "plans/test_provenance/idq-mvp-080-operational-provider-baseline.json"` to staged manifest.
  2. Update `baseline_parent` to match exact HEAD commit SHA `0a4c13ddd9bf60dc24f0129716c67dec299068cc`.
  3. Reconcile unstaged diff in `plans/test_provenance/merge-all-branches-20260831.json`.
  4. Commit provenance manifest and test helpers to Git.
- **Evidence Command / Artifact**: Commit `dc1324ff63cfb10312fa3fb58238dd8017d44861`; `git log -1 dc1324f`.
- **Stop Condition**: Stop if manifest schema validator rejects field updates or test SHA-256 changes unexpectedly.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M1-004`
- **Milestone**: M1
- **Status**: `READY` (Unblocked by `REL-M1-003` commit `dc1324f`)
- **Severity**: CRITICAL
- **Effort**: S
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: None (Read-only test execution)
- **Dependencies**: `REL-M1-001`, `REL-M1-002`, `REL-M1-003`
- **Objective**: Execute focused pytest suite on operational provider on clean committed tree to ensure 100% green pass.
- **Acceptance Criteria**: All 300 tests pass without failures, errors, or unexpected skips on clean committed tree.
- **Evidence Command / Artifact**: `python3 -m pytest -q --tb=no tests/test_idq_mvp_080_operational_provider.py` (Child-attributed observation: 300 passed in 113.90s during prior process deviation; formal post-commit execution receipt required).
- **Stop Condition**: Stop on any test failure, timeout exceeding 300s, or unhandled exception.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

---

### Milestone M2: Release Governance, Safety & PR Harmonization (BLOCKED)

#### `REL-M2-001`
- **Milestone**: M2
- **Status**: `BLOCKED` (Prerequisite `REL-M1-004` unclosed)
- **Severity**: HIGH
- **Effort**: XS
- **Owner**: `agy1 / business_analyst`
- **Writable Ownership**: None (Read-only audit)
- **Dependencies**: `REL-M1-004`
- **Objective**: Validate ecosystem synchronization across Antigravity, Claude, and Codex configuration mirrors following M1 baseline completion.
- **Acceptance Criteria**: `python3 scripts/sync_ai_agent_ecosystem.py --check` exits 0 with all checks `[OK]`.
- **Evidence Command / Artifact**: Terminal output: 12 platform files present, 7 core roles mapped, 17 Claude rules valid, Antigravity definitions 100% synchronized (Child-attributed observation from prior process deviation).
- **Stop Condition**: Stop if any platform mirror is out of sync.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M2-002`
- **Milestone**: M2
- **Status**: `BLOCKED` (Prerequisite `REL-M1-004` unclosed)
- **Severity**: CRITICAL
- **Effort**: XS
- **Owner**: `agy1 / code_reviewer`
- **Writable Ownership**: None (Read-only security audit)
- **Dependencies**: `REL-M1-004`
- **Objective**: Execute comprehensive parallel secret leak detection across all repository files following M1 baseline completion.
- **Acceptance Criteria**: 0 secret leaks identified across >3,500 repository files.
- **Evidence Command / Artifact**: `python3 project/core/code_reviewer.py --scan-secrets` -> `scanned_files: 3591, secret_leaks_found: 0, status: PASSED` (Child-attributed observation from prior process deviation).
- **Stop Condition**: Stop immediately if any secret leak or credential pattern is detected.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M2-003`
- **Milestone**: M2
- **Status**: `BLOCKED` (Prerequisite `REL-M1-004` unclosed)
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy1 / qa_tester`
- **Writable Ownership**: None (Read-only test execution)
- **Dependencies**: `REL-M1-004`
- **Objective**: Verify release governance and Space HF packaging contracts following M1 baseline completion.
- **Acceptance Criteria**: All release governance, deployment contract, and production monitor tests pass 100%.
- **Evidence Command / Artifact**: `python3 -m pytest -q --tb=no tests/test_publish_space_hf.py tests/test_hf_release_governance.py project/tests/test_production_monitor_release_contract.py` -> `59 passed in 5.27s` (Child-attributed observation from prior process deviation).
- **Stop Condition**: Stop if any release contract test fails.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M2-004`
- **Milestone**: M2
- **Status**: `BLOCKED`
- **Severity**: CRITICAL
- **Effort**: XS
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: Git commit history
- **Dependencies**: `REL-M1-004`
- **Objective**: Commit any remaining test provenance corrections and verify git provenance chain.
- **Acceptance Criteria**: `git commit` with message referencing ticket, followed by clean pass of `python3 scripts/test_provenance_guard.py verify-pr`.
- **Evidence Command / Artifact**: `python3 scripts/test_provenance_guard.py verify-pr` outputting `PASSED`.
- **Stop Condition**: Stop if provenance graph does not link cleanly to baseline parent.
- **Attempt**: 0
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M2-005`
- **Milestone**: M2
- **Status**: `BLOCKED` (NEEDS_HITL for GH_TOKEN auth)
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `orchestrator / hitl_reviewer`
- **Writable Ownership**: None (Remote GitHub state inspection)
- **Dependencies**: `REL-M2-004`
- **Objective**: Inspect and verify all GitHub Actions status checks on PR #8 (`merge/all-to-main-20260831` -> `main`).
- **Acceptance Criteria**: All mandatory CI checks green (`Test Provenance`, `Code Quality & Security Audit`, `Live Production Version & LuoPan E2E Regression`, `Rust PyO3 Core Audit`).
- **Evidence Command / Artifact**: `gh pr checks 8` output showing all passing checks.
- **Stop Condition**: Stop if any PR #8 check fails or reports `UNSTABLE`.
- **Attempt**: 0
- **Quota Evidence**: External GitHub Actions runner.

#### `REL-M2-006`
- **Milestone**: M2
- **Status**: `BLOCKED` (NEEDS_HITL for remote write)
- **Severity**: CRITICAL
- **Effort**: XS
- **Owner**: `orchestrator / hitl_reviewer`
- **Writable Ownership**: Remote Git `origin/main`
- **Dependencies**: `REL-M2-005`
- **Objective**: Push local verified `main` commit to `origin/main` or merge PR #8 on GitHub.
- **Acceptance Criteria**: `origin/main` ref updated to HEAD commit without force push.
- **Evidence Command / Artifact**: `git rev-parse origin/main` matches `git rev-parse HEAD`.
- **Stop Condition**: Stop on remote rejection or non-fast-forward conflict.
- **Attempt**: 0
- **Quota Evidence**: Protected remote git operation.

#### `REL-M2-007`
- **Milestone**: M2
- **Status**: `BLOCKED`
- **Severity**: LOW
- **Effort**: XS
- **Owner**: `agy1 / devops`
- **Writable Ownership**: Remote Git refs
- **Dependencies**: `REL-M2-006`
- **Objective**: Delete obsolete remote branch `origin/merge/all-to-main-20260831` after PR merge verification.
- **Acceptance Criteria**: Remote branch removed cleanly from origin.
- **Evidence Command / Artifact**: `git push origin --delete merge/all-to-main-20260831`.
- **Stop Condition**: Stop if branch is still referenced by open unmerged PR.
- **Attempt**: 0
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

---

### Milestone M3: Pre-Deployment Verification & Staging (BLOCKED)

#### `REL-M3-001`
- **Milestone**: M3
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy1 / devops`
- **Writable Ownership**: None (Read-only dry-run)
- **Dependencies**: `REL-M2-006`
- **Objective**: Run Hugging Face Space Docker packaging dry-run audit without uploading.
- **Acceptance Criteria**: Payload provenance audit passes; Dockerfile, dependencies, and artifacts verified valid.
- **Evidence Command / Artifact**: `python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk docker --dry-run` exits 0.
- **Stop Condition**: Stop if dry run discovers missing files or unanchored assets.
- **Attempt**: 0
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M3-002`
- **Milestone**: M3
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: XS
- **Owner**: `agy1 / devops`
- **Writable Ownership**: None (Read-only live health probe)
- **Dependencies**: `REL-M3-001`
- **Objective**: Verify live backend container health and version endpoints on Hugging Face Spaces.
- **Acceptance Criteria**: HTTP 200 responses for `--check-health` and `--verify-version`.
- **Evidence Command / Artifact**: `python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk docker --check-health` and `--verify-version`.
- **Stop Condition**: Stop if backend returns 503, connection error, or unexpected version.
- **Attempt**: 0
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M3-003`
- **Milestone**: M3
- **Status**: `BLOCKED`
- **Severity**: CRITICAL
- **Effort**: M
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: None (E2E browser regression execution)
- **Dependencies**: `REL-M3-002`
- **Objective**: Execute end-to-end button and interactive calculation regression suite.
- **Acceptance Criteria**: 100% pass on BaZi, True Solar Time, SVG rendering, and metaphysical calculation buttons.
- **Evidence Command / Artifact**: `python3 scripts/run_button_regression.py` passes with 0 regressions.
- **Stop Condition**: Stop if any UI interaction or calculation fails.
- **Attempt**: 0
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M3-004`
- **Milestone**: M3
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: M
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: None (Visual layout audit execution)
- **Dependencies**: `REL-M3-002`
- **Objective**: Audit canonical 5 viewports on Vercel production gateway UI (`https://horo-consultant-psi.vercel.app`).
- **Acceptance Criteria**: Visual audit passes 5/5 viewports without layout shift, horizontal clipping, or responsiveness flaws.
- **Evidence Command / Artifact**: `python3 scripts/run_visual_layout_audit.py --url https://horo-consultant-psi.vercel.app --scenario v3-consensus --no-server` reports 5/5 green.
- **Stop Condition**: Stop if any viewport fails layout assertion.
- **Attempt**: 0
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

---

### Milestone M4: Production Deployment & Observability Sign-Off (BLOCKED)

#### `REL-M4-001`
- **Milestone**: M4
- **Status**: `BLOCKED` (NEEDS_HITL for live deployment token)
- **Severity**: CRITICAL
- **Effort**: M
- **Owner**: `orchestrator / hitl_reviewer`
- **Writable Ownership**: Remote Hugging Face Space (`pphothidaen/horoconsultant-core-backend`)
- **Dependencies**: `REL-M3-003`, `REL-M3-004`
- **Objective**: Publish canonical Docker backend release payload to Hugging Face Spaces production.
- **Acceptance Criteria**: Container build triggers and completes cleanly on Hugging Face Spaces; health endpoint responds HTTP 200.
- **Evidence Command / Artifact**: Release publication receipt and live health verification URL.
- **Stop Condition**: Stop if Docker build fails on remote Space.
- **Attempt**: 0
- **Quota Evidence**: Production deployment authorization required.

#### `REL-M4-002`
- **Milestone**: M4
- **Status**: `BLOCKED` (NEEDS_HITL for Vercel production promotion)
- **Severity**: CRITICAL
- **Effort**: S
- **Owner**: `orchestrator / hitl_reviewer`
- **Writable Ownership**: Remote Vercel Production Environment
- **Dependencies**: `REL-M4-001`
- **Objective**: Promote Vercel UI build to production with verified `HF_BACKEND_URL` environment variable.
- **Acceptance Criteria**: `https://horo-consultant-psi.vercel.app` serves verified release frontend with backend proxy active.
- **Evidence Command / Artifact**: Vercel deployment URL and 200 OK proxy response.
- **Stop Condition**: Stop if Vercel responds 503 `backend_not_configured`.
- **Attempt**: 0
- **Quota Evidence**: Production deployment authorization required.

#### `REL-M4-003`
- **Milestone**: M4
- **Status**: `BLOCKED`
- **Severity**: MEDIUM
- **Effort**: S
- **Owner**: `agy1 / devops`
- **Writable Ownership**: None (Telemetry inspection)
- **Dependencies**: `REL-M4-001`, `REL-M4-002`
- **Objective**: Verify live observability telemetry on Grafana Cloud (`vividlamp2135.grafana.net`).
- **Acceptance Criteria**: Metrics ingestion verified for HTTP RPM, API latency quantiles (P95/P90/P50), and FAISS RAG query rate.
- **Evidence Command / Artifact**: Public dashboard URL [vividlamp2135.grafana.net](https://vividlamp2135.grafana.net/public-dashboards/cab04a7907b74c2b9889a8ad811bbcdb) showing active data streams.
- **Stop Condition**: Stop if Prometheus telemetry drops to zero or alert rules trigger.
- **Attempt**: 0
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M4-004`
- **Milestone**: M4
- **Status**: `BLOCKED` (NEEDS_HITL for final sign-off)
- **Severity**: CRITICAL
- **Effort**: XS
- **Owner**: `orchestrator / code_reviewer`
- **Writable Ownership**: Git release tag / `HANDOFF.md`
- **Dependencies**: `REL-M4-003`
- **Objective**: Final release sign-off, consensus approval, and post-release lock.
- **Acceptance Criteria**: Dual-orchestrator consensus reached; immutable Git release tag placed; `HANDOFF.md` updated to `PRODUCTION_LIVE`.
- **Evidence Command / Artifact**: Git release tag (e.g., `v1.2.0-prod`) and closed release audit bundle.
- **Stop Condition**: Stop if any participant objects or residual risk is unaddressed.
- **Attempt**: 0
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

---

### Milestone M5: Agile Governance Implementation & Enforcement (APPROVED / IN PROGRESS)

#### `REL-M5-001`
- **Milestone**: M5
- **Status**: `DONE`
- **Severity**: CRITICAL
- **Effort**: S
- **Owner**: `agy1 / business_analyst`
- **Writable Ownership**: `plans/release_atomic_tickets_20260831.md`, `plans/release_atomic_ticket_audit_20260831.md`
- **Dependencies**: None
- **Objective**: Establish approved Agile governance scope record defining milestone structure, fail-closed concurrency limits (max 3 active lanes per alias, repo hard cap 3 overriding user ceiling 4, one-editor-per-file), quota telemetry rules, and ticket lifecycle invariants.
- **Acceptance Criteria**: Both release ticket artifacts (`REL-ATOMIC-001` and `REL-ATOMIC-002`) are factually reconciled, agree on states, enforce max 3 active lanes, and pass `git diff --check`.
- **Evidence Command / Artifact**: Reconciled documents `plans/release_atomic_tickets_20260831.md` and `plans/release_atomic_ticket_audit_20260831.md` matching current git state.
- **Stop Condition**: Stop if edits exceed the two assigned markdown files or fail git diff check.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M5-002`
- **Milestone**: M5
- **Status**: `READY`
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: `plans/test_provenance/agile-governance-baseline-20260831.json`, `tests/test_agile_governance_guard.py`
- **Dependencies**: `REL-M5-001`
- **Objective**: Create test-only baseline and provenance manifest capturing test suites and assertions for multi-agent capacity, lane concurrency limits, and one-editor-per-file validation.
- **Acceptance Criteria**: Provenance manifest created adhering to `test-provenance-v1` schema with exact SHA-256 digests; baseline tests execute and fail-closed against unverified configurations.
- **Evidence Command / Artifact**: File [plans/test_provenance/agile-governance-baseline-20260831.json](file:///Users/kimlenglim/Project/HoroConsultant/plans/test_provenance/agile-governance-baseline-20260831.json) and passing pytest run on governance guard unit tests.
- **Stop Condition**: Stop if manifest schema verification fails or SHA-256 digests do not match.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M5-003`
- **Milestone**: M5
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: M
- **Owner**: `agy1 / developer`
- **Writable Ownership**: `.agents/rules/21-agile-governance.md`, `.agents/skills/agile-governance/SKILL.md`, `.agents/roles/business_analyst.md`
- **Dependencies**: `REL-M5-002`
- **Objective**: Refactor repository rules, skills, and agent persona definitions to codify strict Agile governance standards: max 3 concurrent lanes per alias, repo hard cap 3 overriding user ceiling 4, strict one-editor-per-file ownership, WIP/dependency gate enforcement, and prohibition of process-deviant commands in documentation lanes.
- **Acceptance Criteria**: Governance rules fully specified, referencing Fail-Closed Release Governance v2 and Rule 11/18; skill documentation aligned.
- **Evidence Command / Artifact**: Rules and skills files committed; verified syntax and linting checks.
- **Stop Condition**: Stop if conflict occurs with existing core agent rules or invalid markdown syntax detected.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M5-004`
- **Milestone**: M5
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: M
- **Owner**: `agy2 / developer`
- **Writable Ownership**: `.agents/config/full_capacity_guard.v2.json`, `scripts/multiagent_capacity.py`
- **Dependencies**: `REL-M5-003`
- **Objective**: Implement configuration schema and runtime capacity hooks enforcing max 3 active lanes per agy alias, hard repository cap of 3 lanes, disjoint file ownership validation, and PreToolUse execution boundaries.
- **Acceptance Criteria**: Configuration validated against schema; `multiagent_capacity.py` rejects attempts to spawn >3 lanes per alias or multiple editors per file.
- **Evidence Command / Artifact**: Unit test output validating capacity guard enforcement and boundary rejection.
- **Stop Condition**: Stop if capacity guard causes false-positive lockouts on valid single-editor lanes.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M5-005`
- **Milestone**: M5
- **Status**: `BLOCKED`
- **Severity**: MEDIUM
- **Effort**: S
- **Owner**: `agy1 / devops`
- **Writable Ownership**: `.claude/rules/21-agile-governance.md`, `.codex/roles/business_analyst.md`
- **Dependencies**: `REL-M5-004`
- **Objective**: Synchronize Agile governance rules, agent definitions, and capacity constraints across Antigravity, Claude Code, and OpenAI Codex environments using `sync_ai_agent_ecosystem.py`.
- **Acceptance Criteria**: `python3 scripts/sync_ai_agent_ecosystem.py --check` exits 0 with all platforms reporting synchronized parity.
- **Evidence Command / Artifact**: Terminal stdout showing clean pass of ecosystem synchronization script.
- **Stop Condition**: Stop if platform drift or unsupported markdown syntax causes sync failure.
- **Attempt**: 1
- **Quota Evidence**: `agy1` Gemini weekly 66%, five-hour 86%; Claude/GPT five-hour 100%.

#### `REL-M5-006`
- **Milestone**: M5
- **Status**: `BLOCKED`
- **Severity**: HIGH
- **Effort**: S
- **Owner**: `agy2 / qa_tester`
- **Writable Ownership**: `tests/test_governance_boundaries.py`
- **Dependencies**: `REL-M5-005`
- **Objective**: Perform independent QA verification of the complete Agile governance suite: assert that concurrency limits cannot exceed 3, one-editor-per-file is strictly enforced, and doc lanes are restricted from executing QA/guard commands.
- **Acceptance Criteria**: 100% test pass on governance boundary tests without flakiness or timeouts.
- **Evidence Command / Artifact**: Pytest execution logs and test provenance record with matching SHA-256 hash.
- **Stop Condition**: Stop on any test failure or boundary bypass.
- **Attempt**: 1
- **Quota Evidence**: `agy2` Gemini weekly 87%, five-hour 97%; Claude/GPT five-hour 100%.

#### `REL-M5-007`
- **Milestone**: M5
- **Status**: `BLOCKED` (NEEDS_HITL for sign-off)
- **Severity**: MEDIUM
- **Effort**: XS
- **Owner**: `orchestrator / hitl_reviewer`
- **Writable Ownership**: `HANDOFF.md`, `plans/release_atomic_tickets_20260831.md`
- **Dependencies**: `REL-M5-006`
- **Objective**: Formal sign-off and closure of the Agile Governance milestone (M5); reconcile final ticket statuses across all boards and update continuation handoff.
- **Acceptance Criteria**: All M5 tickets verified DONE with cryptographic/stdout evidence; orchestrator sign-off recorded in `HANDOFF.md`.
- **Evidence Command / Artifact**: Final signed-off board artifact and clean git commit log.
- **Stop Condition**: Stop if any preceding M5 ticket remains unverified or blocked.
- **Attempt**: 1
- **Quota Evidence**: Orchestrator / Human-in-the-Loop authorization.

---

## 6. Uncertainty Preservation & Fail-Closed Release Invariants

1. **No Phantom Completions**: Work is marked `DONE` if and only if verifiable cryptographic or stdout execution evidence exists in the repository.
2. **Current Gate Status**:
   - `REL-M1-003` is `DONE` (committed at `dc1324ff63cfb10312fa3fb58238dd8017d44861`).
   - `REL-M1-004` is `READY` on a clean committed tree.
   - `REL-M5-001` is `DONE` as the approved Agile governance scope record is established in this artifact pair.
   - `REL-M5-002` is `READY` for immediate test-only baseline creation.
   - PR #8, git push to `origin/main`, HF deployment, and Vercel production promotion remain strictly `BLOCKED` / `NEEDS_HITL`.
3. **No Credential Access**: All tokens (`GH_TOKEN`, `HF_TOKEN`, `VERCEL_TOKEN`, AWS S3 secrets) are strictly isolated and not accessed or requested by this documentation lane.
