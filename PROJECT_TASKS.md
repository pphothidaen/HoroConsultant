# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last Updated: 2026-08-25 +07 (Asia/Bangkok) — authorized HF Static release is deployed and verified at version `1.0.0.6c351ba` / commit `6c351ba`. Publisher regression is `16 passed`; combined publisher and visual-audit regression is `24 passed`; all five canonical viewports pass. Rule 16 and the `hf-static-release-verification` skill now govern subsequent fail-closed release evidence.*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# === RUST NATIVE CI/CD TOOLS ===

# 1. Native Rust Integration Test Suite (2 integration tests: vector search)
export PATH="/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH"
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup -L /opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib -l Python3.14"
cd rust_core
cargo test
# Optional runtime suite: 12 checks; start horo_server first to exercise its health check.
cargo run --bin regression_runner
cd ..

# 2. Rust Code Reviewer & Safety Auditor Binary (Pre-Deployment Audit)
python3 project/core/code_reviewer.py --review
# OR Direct Rust Binary:
./rust_core/target/release/code_reviewer

# 3. Rust Agent & Governance Spec Sync Check Binary
python3 scripts/sync_sdlc_agents.py --check
# OR Direct Rust Binary:
./rust_core/target/release/sync_sdlc_agents

# 4. Codex Agent Compatibility Sync Check
python3 scripts/sync_codex_agents.py --check

# 5. Rust Atomic Prometheus Observability Collector Test
python3 -c "import rust_core; print(rust_core.generate_prometheus_metrics_rust(120.0))"

# 6. Rust SVG Chart Rendering Engine Test (BaZi, ZiWei, Zodiac, QiMen, XuanKong)
python3 -c "from project.core.svg_generator import generate_bazi_svg; print(generate_bazi_svg({'day_master': {'stem': '庚'}}))"

# 7. Rust Astrological Consistency Audit (PyO3 Accelerated)
python3 scripts/audit_astrological_consistency.py

# 8. Pre-Deployment Safety Audit & Secret Scan (Rust Rayon Parallel)
python3 project/core/code_reviewer.py --scan-secrets

# 9. Full Python Pytest Suite (Current local status is in the evidence snapshot)
python3 -m pytest -q project/tests/
```

> **Current release state is captured by the latest evidence block below; historical ticket checkboxes above may reflect earlier completed milestones.**

### Documentation Authority Rules (current)

- The newest timestamped evidence artifact outranks older prose or historical release notes.
- A deployment is not considered healthy from a previous `200` result when the newest canonical probe is `404/503`.
- External deployment, production E2E, credential, and secret-sync actions remain separate HITL checkpoints; do not combine them with local QA.
- Each checkpoint below must produce its own evidence before the next checkpoint starts. If quota is low, stop after the current checkpoint and update `TICKET-META-008` only.

## ✅ Latest Local Evidence Snapshot (2026-08-22 18:56)
- `python3 scripts/sync_sdlc_agents.py --check` → passed (all Antigravity definitions synchronized).
- `python3 scripts/sync_codex_agents.py --check` → passed (all Codex definitions synchronized).
- `cd rust_core && cargo fmt --all -- --check` → passed.
- `cargo fmt --manifest-path rust_core/Cargo.toml --all` executed successfully.
- `bandit -r project/ scripts/ -x project/kaggle_kernel -s B101,B404,B603,B311,B324,B110 -lll` → passed locally on 2026-08-21 (`No issues identified`, 36,112 lines scanned); external CI confirmation remains pending.
- `python3 project/core/code_reviewer.py --review --use-python` → READY_FOR_PROD (`621 passed`, `8 skipped`, `12 warnings`, `overall_status: READY_FOR_PROD`) at 2026-08-21 15:43:59.
  - Latest local audit includes `secret_scan=PASSED`, `kaggle_cuda_audit=PASSED`, `notebook_audit=PASSED`, and full test suite pass.
- `HF_BACKEND_SPACE_ID="pphothidaen/horoconsultant-core-backend" HF_TOKEN="[REDACTED]" python3 scripts/publish_space_hf.py --space-id "$HF_BACKEND_SPACE_ID" --sdk docker` historically failed due `HF Token authentication failed: [Errno 8] nodename nor servname provided, or not known` (this runtime could not resolve `huggingface.co` hosts).
- `python3 -m pytest -q project/tests/` (full suite) → `582 passed`, `8 skipped`, `12 warnings` in 8.62s (fresh revalidation).
- `python3 scripts/run_quality_gate.py` → READY (`100% PASSED`, 4/4 stages).
- `cd rust_core && cargo test --no-default-features --test test_vector_search` → `2 passed`.
- `HF_BACKEND_URL=https://core-backend.hf.space HF_STATIC_CDN_URL=https://static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` → `0/3` checks passed (`core-backend.hf.space` is not the configured canonical target for this run).
- `python3 scripts/run_button_regression.py` → `25/25` passed, report written to `project/tests/button_regression_report.json`.
- `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `2/3` with canonical back-end unavailable fallback (`POST /api/v1/bazi/interpret` `503`).
- `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py` → `19 passed`.
- `python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py` → `25 passed`.
- `python3 -m pytest project/tests/test_web_regression.py` → `11 passed`, `4 skipped`.
- `python3 -m pytest -q project/tests/test_post_train_fuse.py project/tests/test_api_router_external.py project/tests/test_ingest_vault.py project/tests/test_swiss_ephemeris.py` → `19 passed` (focus: TODO workstream closure evidence for Tasks 1,2,3,4,6). Updated on 2026-08-17 at 22:53:25 after revalidation.
- Focused plan/workstream regression revalidation on 2026-08-21 → `59 passed`, `1 warning` across CI workflow, skill governance, observability, provider routing, model fusion, ingestion, and Swiss Ephemeris tests.
- Newly closed local roadmap artifacts: `scripts/mian_xiang_vision.py` (optional Gemini Vision adapter) and `project/tests/test_svg_i18n.py`; focused vision/i18n regression → `33 passed`.
- `python3 - <<"PY"` DNS probe on key external hosts (`project/tests/network-dns-probe.json`) was used for historical context; canonical HF outcomes remain mixed (`horo-consultant-psi.vercel.app` `200`, `pphothidaen-horoconsultant-core-backend.hf.space` `503`, `pphothidaen-horoconsultant-core-backend.static.hf.space` `404`) and authoritative runtime failures in this pass come from direct socket/DNS resolution errors.
- `project/tests/local_release_readiness_2026-08-17.md` contains the full local evidence matrix from this pass.
- Human-in-the-Loop operating procedure and escalation matrix: [`docs/HITL_OPERATING_GUIDE.md`](docs/HITL_OPERATING_GUIDE.md).
- `python3 project/core/code_reviewer.py --scan-secrets` → PASSED: `0` leaks across `1,507` files (2026-08-21 15:43).
- `python3 scripts/sync_sdlc_agents.py --check` → passed again on 2026-08-22 (all Antigravity definitions synchronized).
- `python3 scripts/sync_ai_agent_ecosystem.py --check` → passed on 2026-08-22 (platform files, Claude hooks/rules, Antigravity sync, and all `17` Codex agent definitions synchronized).
- `python3 -m pytest -q project/tests/test_agent_quota_status_guard.py project/tests/test_live_health_verification.py project/tests/test_synthetic_health_monitor.py project/tests/test_mian_xiang_vision.py project/tests/test_post_train_fuse.py project/tests/test_svg_i18n.py project/tests/test_web_regression.py project/tests/test_codex_client.py project/tests/test_agent_configurations.py` → `45 passed`, `4 skipped`, `1 warning` on 2026-08-22.
- `PYTHONPYCACHEPREFIX=/private/tmp/horo_pycache python3 -m py_compile .agents/hooks/pre_tool_check.py .claude/hooks/pre_tool_guard.py scripts/agent_quota_status_guard.py scripts/synthetic_health_monitor.py scripts/run_live_health_verification.py project/api_router.py project/routers/v2.py` → passed on 2026-08-22.
- CP-01 revalidation after `.github/workflows/production_monitor.yml` Azure-only backend selection: `python3 -m pytest -q project/tests/` → `642 passed`, `8 skipped`, `12 warnings`; Azure release tests → `9 passed`; sync/governance tests → `7 passed` (2026-08-22).
- `python3 scripts/agent_quota_status_guard.py --remaining-percent 9 --enforce` → warning emitted for `<10%` quota and confirmed required handoff markers in `PROJECT_TASKS.md` and `plans/plan.md`.
- `python3 project/core/code_reviewer.py --scan-secrets` → PASSED: `0` leaks across `1,530` files (2026-08-22 18:56).
- `git push origin main` → pushed `056b1aa` to `origin/main` on 2026-08-22.
- GitHub Actions `Unified CI & Quality Audit Pipeline` run `32571990179` for `056b1aa` → `success`.
- GitHub Actions `Hugging Face Docker Backend - Production Deployment` run `32571990206` for `056b1aa` → static publish `success`, Docker API backend publish `success`, final verification `failure` (HF Space paused).
- Vercel production verification 2026-08-22: `HF_BACKEND_URL=https://horo-consultant-psi.vercel.app HF_STATIC_CDN_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check-vercel-2026-08-22.json` → `3/3` checks passed (static UI 200, backend `/health` 200, deterministic API 200); HF Space remains paused, Vercel serves as verified production fallback.
- `HF_BACKEND_SPACE_ID="pphothidaen/horoconsultant-core-backend"` Space is paused/unhealthy; canonical HF checks remain blocked until maintainer restarts the Space. Vercel is the verified fallback endpoint.

---

## 📊 TASK BOARD (KANBAN)

## SPRINT: Priority Governance Scheduling — 2026-08-25
**Grill Gate Status**: APPROVED — session HITL recorded (Ref: [`plans/plan.md`](plans/plan.md)); the session approval covers the exact AGY native-protocol remediation reservation. No approver identity is retained.
**Session-Scoped Approval**: approval covers the remaining local priority-sprint remediation, QA, read-only review, and final synchronization/reconciliation. It additionally permits bounded workspace-ticket improvement, refactoring, fixes, and removal of explicitly identified obsolete code/tests. It never authorizes a `/root` glob deletion or broad/unrelated destructive action. Deploy, publish, push, secret/account, external, or destructive actions otherwise require an exact in-scope target and all target-scoped safety gates. None is currently required or used by this sprint; external actions remain unused and target-gated. This approval does not broaden `TICKET-PRIORITY-004` or `TICKET-PRIORITY-005`.
**Dispatch Status**: `TICKET-PRIORITY-002R`, `TICKET-PRIORITY-003R`, `TICKET-PRIORITY-002R2`, `TICKET-PRIORITY-003R2`, `TICKET-PRIORITY-002R3`, `TICKET-PRIORITY-003R3`, `TICKET-PRIORITY-003R3E`, `TICKET-PRIORITY-002R4`, `TICKET-PRIORITY-002R5`, `TICKET-AGY1-SMOKE-20260826-R2`, all four pre-QA remediation tickets, `TICKET-AGY1-EVIDENCE-DOC-20260826-R1`, and `TICKET-PRIORITY-003R5` are `DONE`; source, schema, policy, dependency, documentation, and QA artifacts are frozen. `TICKET-PRIORITY-004R5` is `DOING (RESERVED)` as the fresh read-only final review. `TICKET-AGY1-SMOKE-20260826-R3` remains pending behind that review; no external AGY retry is authorized.
**Scheduling Authority**: Rule 11. Historical `Priority`-only fields below remain evidence but are superseded for scheduling.
**Current Stop**: `TICKET-PRIORITY-004R5` owns the active read-only final review of frozen QA/source/schema/policy/dependency/documentation evidence. R5 QA passed combined `213` and focused `142` tests; sync, locked dependency, and diff checks passed, with no external AGY action. `TICKET-AGY1-SMOKE-20260826-R3` has no writable ownership or executable decision/snapshot until this review passes. No external AGY retry is authorized; final reconciliation remains blocked. This documentation handoff does not execute source edits, QA, reviews, deploy, push, authentication, secrets, or account changes.

| Seq | Ticket ID | Owner | Severity | Work Effort | Model / Reasoning Effort | Status | Depends On |
|---:|---|---|---|---|---|---|---|
| 1 | `TICKET-PRIORITY-001` | `business_analyst` | CRITICAL | XL | `gpt-5.6-sol` / `xhigh` | DONE | None |
| 2 | `TICKET-PRIORITY-002` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-001` |
| 3 | `TICKET-PRIORITY-003` | `qa_tester` | HIGH | M | `gpt-5.6-terra` / `high` | DONE | `TICKET-PRIORITY-002` |
| 4 | `TICKET-PRIORITY-004` | `code_reviewer` | HIGH | S | `gpt-5.6-sol` / `high` | BLOCKED-AGY-R5-QA | `TICKET-PRIORITY-003R5` |
| 5 | `TICKET-PRIORITY-002R` | `developer` | CRITICAL | M | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003` |
| 6 | `TICKET-PRIORITY-003R` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R` |
| 7 | `TICKET-PRIORITY-005` | `business_analyst` | MEDIUM | XS | `gpt-5.6-terra` / `medium` | PENDING | `TICKET-PRIORITY-004R5` |
| 8 | `TICKET-PRIORITY-002R2` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R` |
| 9 | `TICKET-PRIORITY-003R2` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R2` |
| 10 | `TICKET-PRIORITY-002R3` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R2` |
| 11 | `TICKET-PRIORITY-003R3` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R3` |
| 12 | `TICKET-PRIORITY-003R3E` | `root orchestrator` | HIGH | XS | `gpt-5.6-terra` / `high` | DONE | `TICKET-PRIORITY-003R3` |
| 13 | `TICKET-PRIORITY-002R4` | `developer` | CRITICAL | M | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R3E` |
| 14 | `TICKET-PRIORITY-002R5` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R4` |
| 15 | `TICKET-AGY1-SMOKE-20260826-R2` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R5` |
| 16 | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R5` |
| 17 | `TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1` | `developer` | HIGH | XS | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 18 | `TICKET-AGY1-DUPLICATE-JSON-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-SMOKE-20260826-R2` |
| 19 | `TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 20 | `TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1` | `developer` | HIGH | XS | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 21 | `TICKET-PRIORITY-003R5` | `qa_tester` | HIGH | M | `gpt-5.6-sol` / `high` | DONE | combined `213`; focused `142`; sync/lock/diff passed |
| 22 | `TICKET-AGY1-EVIDENCE-DOC-20260826-R1` | `business_analyst` | MEDIUM | XS | `gpt-5.6-terra` / `high` | DONE | None; disjoint from formal QA |
| 23 | `TICKET-AGY1-SMOKE-20260826-R3` | `orchestrator` | HIGH | XS | `TBD — fresh decision required` | PENDING — QA + FINAL PRE-RETRY REVIEW | `TICKET-PRIORITY-003R5` + `TICKET-PRIORITY-004R5` |
| 24 | `TICKET-PRIORITY-004R5` | `code_reviewer` | HIGH | S | `gpt-5.6-sol` / `high` | DOING (RESERVED) | `TICKET-PRIORITY-003R5` |

### Scheduling Snapshot
- `TICKET-PRIORITY-001` is complete and therefore not selectable.
- `TICKET-PRIORITY-002` is complete: syntax compilation and scoped diff checks exited `0`; governance regression passed `11`; focused dispatcher regression passed `76` with `18` legacy execute-without-snapshot fixtures deselected; functional scheduler checks passed.
- `TICKET-PRIORITY-003` reproduced the baseline `18` missing-snapshot fixture failures, then passed its focused regression: `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `154 passed in 1.14s`; scoped diff check also exited `0`.
- `TICKET-PRIORITY-002R` is complete. Its evidence is limited to `scripts/multiagent_prompt_command.py`, `scripts/multiagent_ticket_scheduler.py`, `.claude/hooks/adaptive_dispatch_guard.py`, and `.claude/hooks/orchestrator_only_guard.py`; `py_compile` and scoped diff checks exited `0`, focused pytest passed `106` in `1.13s`, and the five-review-findings plus shell-indirection reproductions were `OK`.
- The remediation records atomic local-temp claim behavior. Stale or ambiguous claims fail closed; this behavior is included in the completed independent QA evidence.
- `TICKET-PRIORITY-003R` completed independent remediation security regression QA: the combined focused pytest command over the three approved suites exited `0` with `173 passed` in `1.53s`; the scoped diff check exited `0`; all five remediation areas were covered and the Rule 11 matrix was green.
- `TICKET-PRIORITY-002R2` is complete: the bounded source fix changed one file; the exact regression passed (`1 passed`), the claim subset passed (`31 passed, 83 deselected`), and deletion of the active locked entry is blocked from same-authorization reacquisition.
- `TICKET-PRIORITY-003R2` completed independent QA: the exact combined three-suite command exited `0` with `185 passed in 2.01s`; scoped diff check exited `0`.
- The prior `TICKET-PRIORITY-004` read-only review returned `NEEDS_HITL — NOT READY`; its findings were remediated in R3 and independently QA-validated. The subsequent final R3 read-only re-review failed with the three R4 findings below. Its R3 QA (`185 passed`) and R3E environment `PASS` evidence remain valid historical evidence; they do not close the new findings.
- `TICKET-PRIORITY-002R3` is complete. This remediation edited only the dispatcher in this round; `py_compile` and scoped diff checks passed; scheduler plus Claude governance checks passed `71`; focused coverage passed `155` with `30` expected contract failures; and the eleven named direct reproductions passed: dirfd swap, durable outside-worktree derivation, independent receipt, lifecycle successful release, lifecycle failed release, write loop, unsupported platform, non-overlap concurrency, overlap, delete/reacquire, and replay.
- The single permitted R3E root verification superseded the managed-sandbox environment boundary: sanitized result `exit 0`, status `PASS`; `outside_worktree`, `canonical_namespace`, `directory_mode_0700`, `owned_by_current_user`, `retained_dirfd`, and `repo_horo_absent` were all `true`. No claim or lock record was created and no provider was dispatched.
- `TICKET-PRIORITY-003R3` completed independent QA: `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `185 passed in 1.79s`; the scoped diff check exited `0`; only `tests/test_multiagent_prompt_command.py` changed. Lifecycle, isolated-store, and delete/reacquire coverage is green.
- `TICKET-PRIORITY-003R3E` completed its exact, single-use root-waiver action. The waiver is preserved below as consumed and expired audit evidence. Completion releases only the final R3 read-only re-review; it does not make `TICKET-PRIORITY-005` eligible.
- **Completed AGY and receipt-v2 remediations / R5 QA**: the source High-hardening lane passed `188` tests with three intentional obsolete-test deltas; the schema-v2 AGY conditional requirement passed; the validator dependency was isolated and locked successfully; and receipt-v2 policy/template adoption passed ecosystem sync/check, `16` focused governance tests, and the secret scan. Formal R5 QA is now complete: combined `213` and focused `142` tests passed; sync, locked dependency, and diff checks passed; no external AGY action occurred. `TICKET-PRIORITY-004R5` is the sole active fresh read-only review.
- **Public-outcome evidence boundary**: the documentation-governance ticket is complete. Public `ExecutionOutcome` is validated in-process with elided stdout/stderr; receipt plus WorkResult plus public outcome is not independently portable/offline evidence. `portable=True` still needs separately retained trusted exact raw stdout, and no approved private retention channel exists. Never restore or log raw streams. This is a Medium residual; a future encrypted sidecar requires separate scope/HITL and is not implemented. Successful AGY language is limited to `validated in-process only`.

### TICKET-PRIORITY-001 | Governance and Active Planning | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: XL
**Model / Reasoning Effort**: `gpt-5.6-sol` / `xhigh`
**Depends On**: None
**Blocks**: `TICKET-PRIORITY-002`
**Ownership**: `PROJECT_TASKS.md`, `plans/plan.md`, `.agents/rules/11-orchestrator-subagent-delegation.md`, `.agents/skills/orchestrator-delegation/SKILL.md`, `.agents/AGENTS.md`, `.claude/rules/orchestrator-subagents.md`, `.antigravity/skills/orchestrator-delegation/SKILL.md`

#### Objective, Evidence, and Stop Condition
- Define Rule 11 as the sole policy authority and mirror eligibility, comparator, tie, override, non-preemption, and effort-separation semantics.
- Preserve historical evidence and mark old `Priority`-only scheduling text superseded.
- Evidence: `python3 scripts/sync_ai_agent_ecosystem.py --sync` and then `--check` both returned `[OK]` on 2026-08-25; generated Codex files were not edited manually.
- Stop `DONE` after owned governance files and active planning artifacts are synchronized; do not implement enforcement code in this ticket.

### TICKET-PRIORITY-002 | Hook and Dispatcher Enforcement | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-001`
**Blocks**: `TICKET-PRIORITY-003`
**Ownership Reserved**: developer lane owns only the scheduler/dispatcher and hook files explicitly assigned by the root; this decision record does not authorize governance-file edits by that lane

#### Objective, Acceptance, and Stop Condition
- Enforce filter-before-sort using Rule 11's total-order key immediately before executable dispatch; reserve ownership and recompute for parallel selection.
- Fail closed on invalid/missing Severity or Work Effort, duplicate Ticket ID, unmet dependencies, ownership conflict, quota/HITL failure, explicit blocker, or invalid Rule 18 decision.
- Keep Work Effort independent from model/provider/reasoning-effort routing and do not preempt `DOING` work.
- Fresh non-secret quota validation recorded band `healthy` for selected alias `codex1`, above the broad-work threshold. Executable decision: [`decision_priority_002.json`](project/tests/artifacts/priority_scheduling/decision_priority_002.json) (policy `2026-08-25.2`).
- Completion evidence: syntax compilation and scoped diff checks exited `0`; governance regression passed `11`; focused dispatcher regression passed `76`, with `18` legacy execute-without-snapshot fixtures deselected; functional scheduler checks passed.
- Residual risk: cross-process persistent reservation storage/locking is not yet present. This is retained for independent QA and read-only review; it is not a rollback condition for the completed implementation ticket.
- Stop condition met: targeted implementation evidence is recorded. Return to `BLOCKED` only if later review establishes an invalid decision, quota/HITL failure, ownership conflict, or another failed pre-execution gate.

### TICKET-PRIORITY-003 | Independent Scheduling QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-PRIORITY-002`
**Blocks**: `TICKET-PRIORITY-004`
**Ownership Reserved**: focused scheduler, dispatcher, and hook tests only

#### Objective, Acceptance, and Stop Condition
- Test every severity pair, every Work Effort pair, exact Ticket ID ties, empty eligible sets, recomputation after ownership reservation, and non-preemption.
- Test each override independently and in combination; verify lower-severity eligible work can run while higher-severity work is ineligible.
- Prove model reasoning effort cannot change order and invalid metadata fails before subprocess creation.
- Executable QA decision: [`decision_priority_003.json`](project/tests/artifacts/priority_scheduling/decision_priority_003.json) (schema v1; policy `2026-08-25.2`; non-secret quota band `healthy`; mutation mode).
- Work Effort `M` remains the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent QA and cannot change scheduling order.
- Include the `18` legacy execute-without-snapshot fixtures previously deselected from focused dispatcher regression. Independently assess the residual lack of a cross-process persistent reservation store/lock.
- Completion evidence: baseline `18` missing-snapshot fixture failures were reproduced. `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `154 passed in 1.14s`; scoped diff check exited `0`. QA changes were limited to `tests/test_multiagent_ticket_scheduler.py`, `tests/test_multiagent_prompt_command.py`, and `project/tests/test_claude_governance.py`.
- Stop condition met: focused QA evidence and its concise baseline-failure record are complete. Return to `BLOCKED` only if later review establishes an invalid decision, quota/HITL failure, ownership conflict, or another failed pre-execution gate.

### TICKET-PRIORITY-004 | Final R3 Read-Only Safety and Compatibility Re-Review | [STATUS: BLOCKED-AGY-R5-QA]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R5` formal QA after all pre-QA dependencies freeze
**Blocks**: `TICKET-PRIORITY-005`
**Ownership Reserved**: reviewer lane is reserved for final R3 read-only review only; no shared-file edits, implementation, test, hook, configuration, or generated-file changes are authorized

#### Objective, Acceptance, and Stop Condition
- The prior read-only review's `NEEDS_HITL — NOT READY` findings are historical evidence. The final R3 re-review was executed and failed: a crashed active-record ownership scan never evaluates liveness, age, or a per-claim lock and can permanently block fresh overlapping authorization; durable claim data persists raw PII in `ownership_resources`; and receipt validation is host/user-state dependent rather than portable archival evidence.
- Executable review decision: [`decision_priority_004.json`](project/tests/artifacts/priority_scheduling/decision_priority_004.json) (schema v1; policy `2026-08-25.2`; non-secret quota band `healthy`; read-only mode).
- Work Effort `S` remains the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for safety and compatibility review and cannot change scheduling order.
- **R3 prerequisite evidence retained**: independent QA over the exact three suites exited `0` with `185 passed in 1.79s`; the single-use root environment verification returned sanitized `exit 0`, status `PASS`, with all required environment assertions `true`. No claim or lock record was created and no provider was dispatched.
- R4 now meets its bounded acceptance evidence: `py_compile` and scoped diff checks passed; permanent R4 coverage passed `6`; scheduler plus Claude checks passed `71`; prompt-command plus R4 coverage passed `119` with one intentional legacy assertion delta. The frozen reviewer architecture check found no Critical or High finding.
- R5 source is frozen: secure temporary recovery and a typed non-PII diagnostic are implemented; `py_compile` and scoped diff passed, R4 coverage passed `6`, combined coverage passed `190` with one known intentional legacy `ownership_sha256` assertion, and direct temporary recovery passed. No unresolved Critical or High pre-QA finding remains.
- The review is `BLOCKED-AGY-R5-QA`. AGY native-protocol and all pre-QA remediation are frozen; the combined independent formal QA is now active. The sanitized-v1 raw-historical-receipt limitation remains a Medium compatibility/audit boundary; it does not make `TICKET-PRIORITY-005` eligible.
- Stop `DONE` only after AGY remediation, independent formal QA, and a fresh evidence-backed read-only terminal verdict. This documentation handoff records status only and does not execute remediation, QA, or review.

### TICKET-PRIORITY-002R4 | Fourth Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R3E`
**Blocks**: `TICKET-PRIORITY-004`
**Ownership Reserved**: developer lane owns only the exact R4 source remediation and local validation assigned after implementation handoff. This governance record owns no source, test, hook, configuration, generated-file, external, or PII action.

#### Objective, Acceptance, and Stop Condition
- **Exact session-approved R4 scope**: remediate only the failed R3 review findings: (1) safely terminalize crashed active ownership records using liveness, age, and per-claim-lock checks before a fresh overlapping authorization may proceed, while exact replay remains blocked; (2) replace durable raw-PII `ownership_resources` with non-PII conflict tokens; and (3) make receipt validation portable archival evidence by embedding sanitized immutable proof rather than depending on host or user state.
- Decision artifact: [`decision_priority_002r4.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r4.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Explicit exclusions**: no unrelated remediation or refactor; no source/test/hook/configuration/generated-file action by this documentation lane; no deploy, publish, push, credentials, secrets, account, external, or PII action. The developer handoff must preserve the stated non-PII boundary.
- **Completion evidence**: `py_compile` and scoped diff checks passed; permanent R4 coverage passed `6`; scheduler plus Claude checks passed `71`; prompt-command plus R4 coverage passed `119` with one intentional legacy assertion delta. The frozen reviewer architecture check found no Critical or High findings.
- **Compatibility/audit boundary**: sanitized v1 migration preserves replay prevention and digest validation, but raw historical receipt revalidation is unsupported because durable PII is intentionally not retained. This is a Medium boundary, not a release approval.
- Stop condition met for R4 implementation. The fixed migration temporary residue that can block future migration (Medium) and typed legacy diagnostic (Low/Medium) are reserved to R5; do not release formal QA, `TICKET-PRIORITY-004`, or `TICKET-PRIORITY-005`.

### TICKET-PRIORITY-002R5 | Sanitized Migration Residue Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R4`
**Blocks**: `TICKET-AGY1-SMOKE-20260826-R2`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, hook, configuration, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve only the fixed sanitized-v1 migration temporary residue that can block a later migration, and make the retained legacy diagnostic typed and actionable. Preserve replay prevention and digest validation; do not add durable raw PII or claim raw historical receipt revalidation support.
- Decision artifact: [`decision_priority_002r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r5.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: source API is frozen; `py_compile` and scoped diff checks passed; R4 coverage passed `6`; combined coverage passed `190` with one known intentional legacy `ownership_sha256` assertion; direct temporary recovery passed. Secure temporary recovery and a typed non-PII diagnostic are implemented. No unresolved Critical or High finding remains before QA.
- Stop condition met for R5 source remediation. The same dispatcher source is now reserved by the bounded AGY native-protocol remediation. Formal QA cannot start until that lane freezes; this ticket does not release `TICKET-PRIORITY-004` or `TICKET-PRIORITY-005`.

### TICKET-AGY1-SMOKE-20260826-R2 | AGY Native-Protocol Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R5`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, hook, configuration, generated-file, deployment, push, credential, secret, account, external retry, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Correct only the HIGH availability/integration mismatch: align the outbound AGY user-event envelope with the installed AGY `1.1.20` native message shape and align terminal parsing with its native event/result nesting. The existing synthetic test dialect is not proof of the native protocol. Receipt-schema drift is expressly out of scope for this ticket.
- Decision artifact: [`decision_agy1_smoke_20260826_r2.json`](project/tests/artifacts/priority_scheduling/decision_agy1_smoke_20260826_r2.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- No external retry: the initial read-only smoke had a successful dry run, one ownership-conflict preflight without a child, and one fail-closed invalid-contract/terminal-shape child result. It produced no valid receipt, provider-execution proof, or quota proof, and no repository change.
- **Completion evidence**: source is frozen; `py_compile` and scoped diff passed; native parser plus fake-execute reproduction passed; R4 plus scheduler plus governance coverage passed `77`; prompt plus R4 coverage passed `118` with two expected legacy failures (old AGY dialect and old `ownership_sha256`).
- Stop condition met. The later pre-QA parser-hardening ticket has separate source ownership; do not broaden into receipt-schema drift or invoke another external child.

### TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1 | Receipt-v2 Contract Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R5`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: new receipt-v2 schema artifact only. Receipt-v1 remains immutable; no dispatcher, docs, tests, hooks, configuration, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve the HIGH contract/evidence defect: receipt-v1 uses `additionalProperties: false` but omits `dispatch_claim_key`, `dispatch_claim_sha256`, `claim_proof`, `claim_proof_sha256`, `claim_proof_scope`, and `scheduling_snapshot_sha256`, so no current receipt can satisfy both code and schema. The v2 contract must model those fields and preserve their distinct semantics.
- Do not silently change the receipt-v1 identity. In particular, distinguish the embedded ClaimProof digest from the persisted-record digest; previous receipts used a different meaning for one of these values. Define explicit v2 meaning and migration rather than reinterpreting historical v1 receipts.
- Decision artifact: [`decision_agy1_receipt_schema_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_schema_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- **Completion evidence and v2 semantics**: receipt-v2 is a new schema only; receipt-v1 and its `$id` are unchanged. JSON and Draft 2020-12 metaschema validation, runtime/ClaimProof parity, two sanitized Codex/AGY valid samples, six invalid rejections, and scoped diff passed. In v2, `dispatch_claim_sha256` and `claim_proof_sha256` are both the canonical embedded ClaimProof digest, not a persisted-record digest; historical v1 receipts retain their original meaning and are not converted or retroactively revalidated as v2. Migration may retain terminal replay state/original record digest but cannot turn an old receipt into v2; only new governed execution emits v2.
- Stop condition met at frozen schema and local validation. Packaging, contract-adoption, and QA are separately owned later; no AGY retry is authorized.

### TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1 | Receipt-v2 Validator Packaging | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `pyproject.toml`, `requirements.txt`, and `uv.lock` only. One developer editor; no source, schema, test, workflow, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Make Draft 2020-12 validation reproducible in the repository rather than accepting an environment-only import. Add `jsonschema>=4.23,<5` consistently to the declared dependency sources and regenerate `uv.lock`; CI already derives its requirements and requires no workflow change.
- Decision artifact: [`decision_agy1_receipt_validator_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_validator_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: the dependency declaration is isolated and the lock is regenerated successfully, making Draft 2020-12 validation reproducible rather than environment-only.
- Stop condition met at frozen dependency declarations and lockfile. No source/schema/test/CI-workflow change or external retry is authorized.

### TICKET-AGY1-DUPLICATE-JSON-20260826-R1 | AGY Parser and Evidence Hardening | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-SMOKE-20260826-R2`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, schema, hook, configuration, generated-file, deployment, push, credential, secret, account, external retry, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Correct the smallest coherent HIGH AGY parser/evidence set: reject duplicate JSON member names rather than accepting ordinary `json.loads` last-key-wins semantics, and reject `NaN`/`Infinity` through `parse_constant`; ensure the resulting reason is content-free; redact decoded AGY prompt content as well as the encoded stdin envelope so arbitrary prompt text cannot echo in `structured_output`; sanitize before finalization, hashing, or persistence and use the exact sanitized `WorkResult` everywhere; and bind AGY `process_or_session_id` receipt validation to parsed native evidence so replacement/deletion fails. Preserve the frozen native-protocol behavior; receipt-v2 schema/adoption and tests are separate ownership.
- Decision artifact: [`decision_agy1_duplicate_json_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_duplicate_json_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: source hardening is frozen and its focused evidence passed `188` tests with three intentional obsolete-test deltas. The local evidence covers strict duplicate/non-finite rejection, content-free/redacted result handling, sanitized-finalization binding, and exact AGY native process/session binding.
- Stop condition met at source freeze. The three obsolete fixtures/assertions are QA-owned updates; no external retry is authorized.

### TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1 | Receipt-v2 Contract Adoption | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `.agents/config/multiagent_model_policy.yaml` and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md` only. One developer editor; generated mirrors may change only through the prescribed ecosystem sync after the source files freeze. No dispatcher, schema, test, hook, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve the HIGH orphaned-contract defect: make receipt-v2 canonical for new governed receipts in policy and prompt-template contract language, while receipt-v1 remains explicitly legacy; align the timestamp contract to the required `Z` suffix. Do not alter receipt-v1 identity or alter generated files manually.
- Decision artifact: [`decision_agy1_receipt_v2_adoption_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_v2_adoption_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: policy/template sources are frozen; ecosystem sync/check passed, `16` focused governance tests passed, and the secret scan passed. Receipt-v2 is canonical for new governed receipts; receipt-v1 remains explicit legacy/non-reinterpreted handling.
- Stop condition met at prescribed synchronization evidence. Runtime schema loading and QA tests are separate ownership; no external retry is authorized.

### TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1 | Receipt-v2 AGY Evidence Requirement | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `.agents/schemas/multiagent-dispatch-receipt-v2.schema.json` only. One developer editor; receipt-v1, dispatcher, policy, template, tests, hooks, configuration, generated files, deployment, push, credential, secret, account, external, and raw-PII actions are excluded.

#### Objective, Acceptance, and Stop Condition
- Correct only the HIGH receipt-v2 contract gaps: conditionally require `process_or_session_id` when `provider` is `agy`, retain Codex receipt compatibility, and align the timestamp contract to the required `Z` suffix. Do not mutate receipt-v1, broaden semantic migration, or hide provider-specific conditions.
- Decision artifact: [`decision_agy1_receipt_v2_agy_requirement_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_v2_agy_requirement_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: the schema-v2 AGY conditional requirement passed: AGY requires `process_or_session_id`, Codex remains compatible, and the timestamp `Z` contract is enforced.
- Stop condition met at frozen schema-v2 update and local validation. No external retry is authorized.

### TICKET-PRIORITY-003R5 | R5 Combined Formal Regression QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: completed `TICKET-AGY1-SMOKE-20260826-R2`, `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`, `TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1`, `TICKET-AGY1-DUPLICATE-JSON-20260826-R1`, `TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1`, and `TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1`
**Blocks**: `TICKET-PRIORITY-004R5` and `TICKET-PRIORITY-005`
**Ownership Reserved**: `tests/test_multiagent_prompt_command.py`, `tests/test_multiagent_prompt_command_r4.py`, and `tests/test_multiagent_receipt_schema.py` only. Dispatcher source and receipt schemas are read-only/frozen.

#### Objective, Acceptance, and Stop Condition
- Update the three obsolete fixtures/assertions, then independently validate: the official AGY envelope/native fake execute path; strict duplicate/non-finite JSON rejection; sanitation before hashing and public stdout/stderr elision; exact native process/session binding; the full R5 migration matrix; and real generated Codex plus AGY receipt-v2 Draft 2020 conformance, tamper rejection, and field parity. Receipt-v1 remains legacy coverage, not the v2 acceptance contract. No external AGY retry is part of QA.
- Decision artifact: [`decision_priority_003r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r5.json) (schema v1; policy `2026-08-26.1`; phase `qa`; mutation mode limited to the owned test updates; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- **Completion evidence**: combined `213` and focused `142` tests passed; ecosystem sync, locked dependency, and scoped diff checks passed. No external AGY action occurred.
- Stop condition met. Release only `TICKET-PRIORITY-004R5` fresh read-only final review; no external AGY retry is part of QA.

### TICKET-AGY1-EVIDENCE-DOC-20260826-R1 | Public Outcome Evidence Boundary | [STATUS: DONE]
**Severity**: MEDIUM
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: None; explicitly disjoint from `TICKET-PRIORITY-003R5`
**Blocks**: portable/offline evidence claims only; it does not block QA or source work
**Ownership Reserved**: `.agents/rules/17-multi-account-agent-orchestration.md`, `.agents/skills/multi-account-agent-orchestration/SKILL.md`, and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md` only. This governance lane also records its status in the owned board/plan and its decision artifact; generated mirrors change only through prescribed sync. No source, schema, policy, dependency, test, external, or raw-stream action.

#### Objective, Acceptance, and Stop Condition
- State precisely that public `ExecutionOutcome` is validated in-process and its stdout/stderr are elided; a receipt, WorkResult, and public outcome are not an independently portable/offline-verifiable evidence bundle. `portable=True` still requires separately retained trusted exact raw stdout. No approved private retention channel exists, and raw streams must never be restored, logged, or persisted.
- Successful AGY evidence must say `validated in-process only`; it must not claim portable, offline, or receipt-only verification. Record the Medium residual and an encrypted, access-controlled raw-output sidecar only as a future, separately scoped/HITL-gated design option; do not implement it.
- Decision artifact: [`decision_agy1_evidence_doc_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_evidence_doc_20260826_r1.json) (schema v1; policy `2026-08-26.1`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-terra` / `high`; `hitl_approved: true`).
- **Completion evidence**: the rule, skill, and template contain the same boundary; ecosystem sync/check, focused governance tests, secret scan, and diff check passed. Stop condition met with no runtime, schema, policy, dependency, test, or external AGY change.

### TICKET-PRIORITY-004R5 | Fresh R5 Read-Only Final Review | [STATUS: DOING (RESERVED)]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R5`
**Blocks**: `TICKET-AGY1-SMOKE-20260826-R3` and `TICKET-PRIORITY-005`
**Ownership Reserved**: read-only review only; no writable ownership, implementation, test mutation, external AGY retry, generated-file edit, deployment, push, credential, secret, account, or raw-stream action.

#### Objective, Acceptance, and Stop Condition
- Independently issue a terminal safety/compatibility verdict on the frozen R5 QA/source/schema/policy/dependency/documentation evidence, including the public-outcome evidence boundary. Do not execute source or QA actions.
- Decision artifact: [`decision_priority_004r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_004r5.json) (schema v1; policy `2026-08-26.1`; phase `review`; read-only mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- Stop `DONE` only with an evidence-backed terminal read-only verdict. A successful verdict is necessary but not by itself sufficient for any later AGY R3 smoke: that lane must also obtain its own fresh decision/snapshot and pre-execution gates.

### TICKET-AGY1-SMOKE-20260826-R3 | One-Shot Post-QA AGY Smoke | [STATUS: PENDING — QA + FINAL PRE-RETRY REVIEW]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `TBD — fresh decision required after dependencies`
**Depends On**: `TICKET-PRIORITY-003R5` formal QA and `TICKET-PRIORITY-004R5` final pre-retry read-only review
**Blocks**: any external AGY retry only
**Ownership Reserved**: read-only/no writable ownership. The future lane may make at most one AGY execute attempt only after its dependencies and all fresh pre-execution gates pass; it owns no source, schema, policy, dependency, test, generated, deployment, push, credential, secret, account, or raw-stream mutation.

#### Objective, Acceptance, and Stop Condition
- Do not dispatch now. After both dependencies pass, require a fresh Rule 18 `DispatchDecision`, fresh Rule 11 scheduling snapshot, quota/HITL/ownership validation, approved read-only runtime boundary, and the one-attempt cap before any execute action. No stale execution decision is created or reusable now.
- If later authorized, record only safe outcome metadata and use successful AGY language `validated in-process only`; never claim independent portable/offline proof, and never restore or log raw streams.
- Stop `PENDING` until all dependency and fresh-gate evidence exists. Any external AGY retry without that new decision/snapshot is prohibited.

### TICKET-PRIORITY-002R3 | Third Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R2`
**Blocks**: `TICKET-PRIORITY-003R3`
**Ownership Reserved**: developer lane for the exact R3 local source remediation and local validation only. Deploy, publish, push, secrets, account, external, destructive, configuration, generated-file, and PII actions are excluded; external actions remain unused and target-gated.

#### Objective, Acceptance, and Stop Condition
- **Exact R3 scope after session HITL approval**: remediate only the failed final re-review findings: (1) eliminate intermediate `.horo` symlink TOCTOU caused by secure traversal followed by pathname reopen; (2) make returned receipts verifiable after live-claim release; (3) prevent removal of the worktree-local `.horo` replay ledger through `git clean`; (4) prevent public `execute_invocation` from leaking the global lock; (5) handle partial writes rather than relying on one `os.write`; (6) provide fail-closed `fcntl`/POSIX and macOS realpath-containment compatibility; and (7) replace the global store lock behavior that prevents safe non-overlap concurrency. No unrelated refactor is authorized.
- Decision artifact: [`decision_priority_002r3.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r3.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DOING`).
- Session HITL approval is recorded without approver identity. It authorizes only the exact R3 local remediation and local validation scope, including removal of explicitly identified obsolete code/tests if needed by the bounded workspace ticket. It does not authorize a `/root` glob deletion or broad/unrelated destructive action. External actions remain unused and may occur only with an exact target and all target-scoped safety gates.
- Completion evidence: only the dispatcher was edited in this round. `py_compile` and scoped diff checks passed; scheduler plus Claude governance checks passed `71`; focused coverage passed `155` with `30` expected contract failures. All eleven named direct reproductions passed: dirfd swap, durable outside-worktree derivation, independent receipt, lifecycle successful release, lifecycle failed release, write loop, unsupported platform, non-overlap concurrency, overlap, delete/reacquire, and replay.
- Residual environment boundary: managed sandbox policy blocked default macOS user-state creation, while the isolated explicit override worked. Record a later real-environment verification gate; do not treat the sandbox limitation as evidence of implementation failure.
- Stop condition met: bounded developer remediation evidence is complete. This did not close `TICKET-PRIORITY-004`; `TICKET-PRIORITY-003R3` independently completed QA and `TICKET-PRIORITY-003R3E` verified the default environment before the later read-only re-review, which subsequently failed and opened R4.

### TICKET-PRIORITY-003R3 | Third-Remediation Independent QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R3`
**Blocks**: `TICKET-PRIORITY-003R3E`
**Ownership Reserved**: independent `qa_tester` lane for bounded R3 dispatcher QA only. This record authorizes no current source, test, hook, configuration, generated-file, external, or PII change.

#### Objective, Acceptance, and Stop Condition
- Independently validated the completed R3 dispatcher remediation using the isolated explicit state-location override. The exact three-suite command `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `185 passed in 1.79s`; the scoped diff check exited `0`; the only QA change was `tests/test_multiagent_prompt_command.py`. Lifecycle, isolated-store, and delete/reacquire coverage is green.
- Decision artifact: [`decision_priority_003r3.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r3.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DONE`). Work Effort `S` remains the delivery-size scheduling input; reasoning effort `high` is a separate runtime-quality setting.
- The managed-sandbox block on default macOS user-state creation remains a residual environment limitation. The isolated override is valid only for QA; it does not establish default-state behavior.
- Stop condition met: independent QA evidence is complete. It released only `TICKET-PRIORITY-003R3E`; that completed environment gate then released the later review, which subsequently failed and opened R4. R4 is now complete; R5 source remediation blocks formal QA and `TICKET-PRIORITY-004`, while `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R3E | Default macOS User-State Environment Verification | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-PRIORITY-003R3`
**Blocks**: `TICKET-PRIORITY-004` re-review
**Owner**: `root orchestrator` completed exactly the one recorded waiver action. Delegation was not viable because the delegated `devops` attempt was sandbox-blocked and its escalation remained unapproved.

#### Rule 17 Single-Use Root Waiver
- `ROOT-WAIVER: ROOT-WAIVER-R3E-20260826` **[CONSUMED AND EXPIRED]**
- **Approval reference / date**: session user authorization on `2026-08-26`, recorded without approver identity: “I approve all for this session include deploy, publish, push, secret/account changes หรือ destructive actions”; bounded `/root/*` improve/refactor/fix/remove was also approved. This is evidence only for the exact action below, not a standing or broad waiver.
- **Executed one action / exact target**: root ran exactly one minimal Python verification for the current project invoking dispatcher `_secure_claim_directory` with no override. Sanitized result: `exit 0`, status `PASS`; `outside_worktree`, `canonical_namespace`, `directory_mode_0700`, `owned_by_current_user`, `retained_dirfd`, and `repo_horo_absent` were all `true`.
- **Explicit exclusions**: no claim or lock record, provider dispatch, deletion, authentication, credential or secret access, source/test/config/generated-file change, external action, or PII handling.
- **Stop / expiry**: the command returned the sanitized result above; the waiver was consumed by that one action and expired immediately. Any additional action requires fresh authorization.

#### Objective, Acceptance, and Stop Condition
- Verified the actual default macOS user-state claim directory derived by the dispatcher helper. This was an environment-evidence gate only; no claim or lock record was created and no provider was dispatched.
- Decision artifact: [`decision_priority_003r3e.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r3e.json) (schema v1; policy `2026-08-25.2`; phase `operations`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DOING`). Work Effort `XS` is the delivery-size scheduling input; reasoning effort `high` is a separate runtime-quality setting.
- Acceptance met: sanitized `exit 0` / `PASS` evidence records the required environment assertions as `true`, without retaining credentials, authentication data, provider output, PII, or external execution evidence.
- Stop condition met: completion released only the final R3 read-only `TICKET-PRIORITY-004` re-review; that review later failed and opened the reserved R4 remediation. R4 is now complete; R5 source remediation blocks formal QA and `TICKET-PRIORITY-004`, while `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-002R2 | Second Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R`
**Blocks**: `TICKET-PRIORITY-003R2`
**Ownership Reserved**: completed `developer` lane for the bounded claim verify-to-spawn TOCTOU fix only. The approved scope remained source remediation and local tests only; deploy, push, secrets, and account changes remained excluded.

#### Objective, Acceptance, and Stop Condition
- **Exact proposed scope after approval**: remediate only the four High and two Medium findings recorded by the failed re-review: encoded decode-pipeline direct-child bypass; claim verify-to-spawn TOCTOU/deletion-reacquire; receipt binding to claim identity, completion, output, and workresult digests; durable temporary claim-store handling including parent-directory fsync; unsafe claim-reader symlink, mode, and special-file handling; and initial configuration/OSError ASCII-safe, path-safe errors.
- Existing decision artifact: [`decision_priority_002r2.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r2.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`). No new decision is required because the existing approval already covers the TOCTOU finding.
- Existing HITL approval is recorded from the owner exactly as `อนุมัติ TICKET-PRIORITY-002R2`. It authorizes the exact scope, including claim verify-to-spawn TOCTOU/deletion-reacquire remediation, source remediation, and local tests only. Deploy, push, secrets, and account changes remain out of scope.
- Completion evidence: the bounded source fix changed one file; the exact regression passed (`1 passed`), and the claim subset passed (`31 passed, 83 deselected`). The deleted active locked entry is blocked from same-authorization reacquisition.
- Stop condition met: bounded remediation evidence is complete. `TICKET-PRIORITY-003R2` completed independent QA and released only the final read-only `TICKET-PRIORITY-004` re-review; `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R2 | Second-Remediation Independent QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R2`
**Blocks**: `TICKET-PRIORITY-004` re-review
**Ownership Reserved**: completed independent QA lane; no remediation source, hook, configuration, or generated-file edits are authorized by this evidence record.

#### Objective, Acceptance, and Stop Condition
- Independently validate the completed second remediation, update the 16 intentional legacy-contract fixtures, and add permanent R2 regression coverage for the durable `.horo` claim protocol, cooperative-lock residual, and completed-claim/receipt persistence without reopening implementation scope.
- Decision artifact: [`decision_priority_003r2.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r2.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; historical `DOING` status).
- Work Effort `S` is the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent QA and cannot change scheduling order.
- Completion evidence: the exact combined three-suite QA command exited `0` with `185 passed in 2.01s`; scoped diff check exited `0`. The source-fix regression confirms that deleting the active locked entry blocks same-authorization reacquisition.
- Stop condition met: independent QA closes the R2 defect path and releases only the final read-only `TICKET-PRIORITY-004` re-review. `TICKET-PRIORITY-005` remains pending until that review reaches its own terminal verdict.

### TICKET-PRIORITY-002R | Safety-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003`
**Blocks**: `TICKET-PRIORITY-003R`
**Ownership Reserved**: completed developer remediation lane; scope was source remediation and local tests only.

#### Objective, Acceptance, and Stop Condition
- Remediate all five review findings: atomic, non-replayable cross-process reservation/duplicate protection; shell redirection classification; shell-expanded direct-child coverage; prefix-overlap ownership detection; and PII redaction for receipts/results.
- Decision artifact: [`decision_priority_002r.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r.json) (schema v1; policy `2026-08-25.2`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DONE`).
- Fresh approval record: approval was recorded on 2026-08-25 (Asia/Bangkok) after review of all five findings. It authorizes this developer lane only for source remediation and local tests; deploy, push, secrets, and account changes remain out of scope.
- Completion evidence: only `scripts/multiagent_prompt_command.py`, `scripts/multiagent_ticket_scheduler.py`, `.claude/hooks/adaptive_dispatch_guard.py`, and `.claude/hooks/orchestrator_only_guard.py` were changed in the remediation lane. `py_compile` and scoped diff checks exited `0`; focused pytest passed `106` in `1.13s`; the five-review-findings reproductions and shell-indirection reproductions were `OK`.
- Claim behavior: local-temp claims are atomic. Stale or ambiguous claims fail closed; that residual must be independently checked by `TICKET-PRIORITY-003R`.
- Stop condition met for bounded implementation evidence. `TICKET-PRIORITY-003R` is complete with independent QA evidence; `TICKET-PRIORITY-004` is reserved for read-only re-review and `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R | Remediation Security Regression QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R`
**Blocks**: releases `TICKET-PRIORITY-004` re-review
**Ownership Reserved**: independent `qa_tester` security-regression lane; no remediation source, hook, configuration, or generated-file edits.

#### Objective, Acceptance, and Stop Condition
- Independently validate the completed remediation against all five review findings, shell indirection, atomic local-temp claim behavior, and fail-closed stale or ambiguous claim handling without reopening implementation scope.
- Decision artifact: [`decision_priority_003r.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`).
- Work Effort `S` is the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent remediation security QA and cannot change scheduling order.
- Completion evidence: the combined focused pytest command over the three approved suites exited `0` with `173 passed` in `1.53s`; scoped diff check exited `0`; all five remediation areas were covered and the Rule 11 matrix was green.
- Stop condition met: independent QA evidence releases `TICKET-PRIORITY-004` for reserved read-only re-review. `TICKET-PRIORITY-005` remains pending; this ticket did not authorize deploy, push, authentication, secret, or account actions.

### TICKET-PRIORITY-005 | Final Sync and Reconciliation | [STATUS: PENDING]
**Severity**: MEDIUM
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `medium`
**Depends On**: `TICKET-PRIORITY-004`
**Blocks**: Sprint closure
**Ownership**: generated ecosystem sync through prescribed script plus `PROJECT_TASKS.md` and `plans/plan.md` reconciliation

#### Objective, Acceptance, and Stop Condition
- After all legacy enforcement/governance edits, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`, then `python3 scripts/sync_ai_agent_ecosystem.py --check`, focused governance tests, and `git diff --check`.
- The preliminary sync under `TICKET-PRIORITY-001` does not close this final post-implementation checkpoint.
- Stop `DONE` only after every upstream ticket has evidence and statuses match the repository; otherwise record the exact blocker/HITL action.

### Sprint Checkpoints
| Checkpoint | Owner | State | Required Evidence |
|---|---|---|---|
| `CP-PRIORITY-01` | `business_analyst` | DONE | authoritative/mirrored policy plus ecosystem sync/check `[OK]` |
| `CP-PRIORITY-02` | `developer` | DONE | syntax and scoped diff checks exited `0`; governance regression `11` passed; dispatcher regression `76` passed with `18` legacy fixtures reserved for QA; scheduler functional checks passed |
| `CP-PRIORITY-03` | `qa_tester` | DONE | baseline `18` missing-snapshot failures reproduced; focused regression `154 passed` in `1.14s`, exit `0`; scoped diff check exit `0` |
| `CP-PRIORITY-04` | `code_reviewer` | BLOCKED-R3 | final re-review verdict `NEEDS_HITL — NOT READY`; blocked pending exact R3 remediation and a new independent re-review |
| `CP-PRIORITY-04R` | `developer` | DONE | four owned remediation files; syntax and scoped diff checks exited `0`; focused pytest `106 passed` in `1.13s`; five-finding and shell-indirection reproductions `OK` |
| `CP-PRIORITY-03R` | `qa_tester` | DONE | combined focused pytest exit `0`, `173 passed` in `1.53s`; scoped diff check exit `0`; five remediation areas covered and Rule 11 matrix green |
| `CP-PRIORITY-04R2` | `developer` | DONE | one-file bounded source fix; exact regression `1 passed`; claim subset `31 passed, 83 deselected`; deleted active locked entry cannot be reacquired by the same authorization |
| `CP-PRIORITY-03R2` | `qa_tester` | DONE | exact combined three-suite QA exit `0`, `185 passed in 2.01s`; scoped diff check exit `0`; deleted active-entry reacquisition is blocked |
| `CP-PRIORITY-04R3` | `developer` | DONE | dispatcher-only change; `py_compile` and scoped diff passed; scheduler plus Claude checks `71`; focused coverage `155` with `30` expected contract failures; eleven direct reproductions passed |
| `CP-PRIORITY-03R3` | `qa_tester` | DONE | exact three-suite QA exited `0` with `185 passed in 1.79s`; lifecycle, isolated-store, and delete/reacquire coverage green |
| `CP-PRIORITY-04R4` | `developer` | DONE | `py_compile` and scoped diff passed; R4 `6`, scheduler plus Claude `71`, and prompt plus R4 `119` passed with one intentional legacy assertion delta; no Critical/High reviewer finding |
| `CP-PRIORITY-04R5` | `developer` | DOING — RESERVED | one source file only; formal QA waits for source freeze; Medium migration residue and Low/Medium typed diagnostic only |
| `CP-PRIORITY-05` | `business_analyst` | PENDING | final sync/check, diff check, status reconciliation |

---

## SPRINT: Zero-Cost Multi-Tier AI Provider Pipeline & Governance — 2026-08-25
**Grill Gate Status**: APPROVED FOR PLANNING (Ref: [`plans/plan.md`](plans/plan.md))
**Planning-to-Execution Gate**: `PLANNING_GATE: READY` (Awaiting user command to start)
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Owner | Model / Effort Floor | Task Summary | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-ZERO-001` | `business_analyst` | `gpt-5.6-terra` / `medium` | Author API specs, Rule 19, Skill, and governance contracts | READY | None |
| `TICKET-ZERO-002` | `developer` (Core AI Lane) | `gpt-5.3-codex` / `high` | Refactor AIProviderRouter with ProviderPool, CircuitBreakerState, and Free Filter | READY | `TICKET-ZERO-001` |
| `TICKET-ZERO-003` | `developer` (Security Lane) | `gpt-5.3-codex` / `high` | Extend Rate Limiter (IP/User/Daily Budget) & Input Clamping (12k chars) | READY | `TICKET-ZERO-001` |
| `TICKET-ZERO-004` | `developer` (Caching Lane) | `gpt-5.3-codex` / `high` | Implement Metaphysics Semantic Cache & Rust PyO3 Safe Net | READY | `TICKET-ZERO-001` |
| `TICKET-ZERO-005` | `devops` (Admin Lane) | `gpt-5.3-codex` / `high` | Admin Dashboard Pool Health monitoring & Zero-Cost Badges | READY | `TICKET-ZERO-002` |
| `TICKET-ZERO-006` | `qa_tester` | `gpt-5.4-mini` / `medium` | Comprehensive Zero-Cost & Fail-Closed Test Suite | READY | `TICKET-ZERO-002`..`005` |
| `TICKET-ZERO-007` | `code_reviewer` & `business_analyst` | `gpt-5.3-codex` / `high` | Pre-deployment safety audit, secret scan (0 leaks), and ecosystem sync | READY | `TICKET-ZERO-006` |

---

### TICKET-ZERO-001 | `business_analyst` | [STATUS: READY]
**Priority**: HIGH
**Selected Route**: `gpt-5.6-terra` / `medium`
**Depends On**: None
**Blocks**: `TICKET-ZERO-002`, `TICKET-ZERO-003`, `TICKET-ZERO-004`
**Owned Files**: `.agents/rules/19-zero-cost-ai-governance.md`, `.claude/rules/zero-cost-ai-governance.md`, `.agents/skills/zero-cost-ai-pipeline/SKILL.md`, `docs/specs/zero_cost_ai_spec.md`

#### Objective and Ownership
- Author and verify OpenAPI schema contracts for ProviderPool, Health Status, and Circuit Breaker states.
- Ensure Rule 19 and `zero-cost-ai-pipeline` skill adhere to Rule 14 size boundaries.

---

### TICKET-ZERO-002 | `developer` (Core AI Lane) | [STATUS: READY]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-005`, `TICKET-ZERO-006`
**Owned Files**: `project/core/ai_provider_router.py`, `project/api_router.py`

#### Objective and Ownership
- Implement `ProviderPool` separating key auth redundancy from multi-project quota pools.
- Attach `CircuitBreakerState` with 60s cooldown for 0ms instant 429 bypass.
- Enforce `BillingMode.FREE` fail-closed filter when `AI_ZERO_COST_ONLY=true`.

---

### TICKET-ZERO-003 | `developer` (Security Lane) | [STATUS: READY]
**Priority**: HIGH
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/core/rate_limiter.py`

#### Objective and Ownership
- Implement multi-tier rate limiting: IP (10 RPM), User (20 RPM), Daily Budget (40-150 req/day).
- Enforce input character clamping (<= 12,000 chars) and max output tokens (<= 1,200).

---

### TICKET-ZERO-004 | `developer` (Caching Lane) | [STATUS: READY]
**Priority**: HIGH
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/core/semantic_cache.py`

#### Objective and Ownership
- Implement SHA-256 canonical query normalization for astrological prompts.
- Integrate Rust PyO3 engine (<1ms) fallback safe net on full free LLM capacity exhaustion.

---

### TICKET-ZERO-005 | `devops` (Admin Lane) | [STATUS: READY]
**Priority**: MEDIUM
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-002`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/admin_router.py`, `project/static/admin.html`

#### Objective and Ownership
- Expose `/api/admin/provider-pools` endpoint with live health status.
- Render visual indicators and `🔒 BLOCKED BY ZERO-COST POLICY` badges in admin UI.

---

### TICKET-ZERO-006 | `qa_tester` | [STATUS: READY]
**Priority**: HIGH
**Selected Route**: `gpt-5.4-mini` / `medium`
**Depends On**: `TICKET-ZERO-002`, `TICKET-ZERO-003`, `TICKET-ZERO-004`, `TICKET-ZERO-005`
**Blocks**: `TICKET-ZERO-007`
**Owned Files**: `project/tests/test_zero_cost_pipeline.py`, `project/tests/test_semantic_cache.py`

#### Objective and Ownership
- Write unit, integration, and stress tests verifying zero-cost fail-closed guarantee, circuit breakers, rate limits, and caching.

---

### TICKET-ZERO-007 | `code_reviewer` & `business_analyst` | [STATUS: READY]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-006`
**Blocks**: Final Closure & Production Release
**Owned Files**: `PROJECT_TASKS.md`, `plans/plan.md`

#### Objective and Ownership
- Run full pre-deployment safety audit (`python3 project/core/code_reviewer.py --review`).
- Run parallel secret scan (0 leaks).
- Run ecosystem sync check (`python3 scripts/sync_ai_agent_ecosystem.py --check`).

---

## SPRINT: Adaptive Multi-Agent Model & Effort Governance — 2026-08-25
**Grill Gate Status**: APPROVED FOR PLANNING (Ref: [`plans/plan.md`](plans/plan.md))
**Planning-to-Execution Gate**: `PLANNING_TO_MEDIUM_GATE: CONFIRMED` (owner confirmation received 2026-08-25)
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Owner | Model / Effort Floor | Task Summary | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-ADAPT-001` | `orchestrator` | `gpt-5.6-sol` / `xhigh` | Inspect current routing; define rubric, solution, plan, and isolated tickets | DONE | None |
| `TICKET-ADAPT-002` | Human owner / `orchestrator` | Root changes to `medium` | Confirm root orchestrator reasoning effort is `medium` | DONE | `TICKET-ADAPT-001` |
| `TICKET-ADAPT-003` | `business_analyst` | `gpt-5.6-terra` / `high` | Dedicated rules, skill, mirrors, orchestrator contract, and governance docs | DONE | `TICKET-ADAPT-002` |
| `TICKET-ADAPT-004` | `developer` | `gpt-5.6-sol` / `high` | Versioned policy/catalog/schema and fail-closed PromptCommand enforcement | DONE | `TICKET-ADAPT-003` |
| `TICKET-ADAPT-005` | `developer` (security lane) | `gpt-5.6-sol` / `high` | Extend existing orchestrator-only hook and registration | DONE | `TICKET-ADAPT-004` |
| `TICKET-ADAPT-006` | `qa_tester` | `gpt-5.6-terra` / `high` | Independent policy, dispatcher, hook, and governance regression tests | DONE | `TICKET-ADAPT-005` |
| `TICKET-ADAPT-007` | `business_analyst` editor; `code_reviewer` read-only | `terra/medium` sync; `sol/high` review | Ecosystem sync, skill eval evidence, secret scan, compatibility and bypass review | DONE | `TICKET-ADAPT-006` |

---

### TICKET-ADAPT-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.6-sol` / `xhigh`
**Depends On**: None
**Blocks**: `TICKET-ADAPT-002`

#### Objective and Ownership
- Read-only audit of model metadata, routing config, PromptCommand, hooks, rules, skills, schemas, templates, and tests.
- Own only solution architecture, the GRILL REPORT, and ticket decomposition.

#### Evidence / Acceptance Criteria
- [x] Static role defaults distinguished from effective runtime proof.
- [x] Judgment-based classification separated from deterministic enforcement.
- [x] Five-dimension rank rubric and model/effort floors recorded.
- [x] Planning-to-medium HITL gate retained independently from child routing.
- [x] File ownership is isolated for every implementation lane.

---

### TICKET-ADAPT-002 | Human owner / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-ADAPT-001`
**Blocks**: `TICKET-ADAPT-003` through `TICKET-ADAPT-007`

#### Required Owner Action
1. Change the root orchestrator reasoning effort from `xhigh` to `medium` in the active Codex session/runtime.
2. Provide fresh confirmation in this conversation.

#### Acceptance Criteria
- [x] Owner explicitly confirmed the active root orchestrator effort is `medium` on 2026-08-25.
- [x] Confirmation is fresh and occurs after solution, plan, and tickets were completed.
- [x] No repository setting, historical approval, or ticket status is treated as runtime proof.

#### Stop Condition
- Confirmation satisfied the planning-to-medium gate; child selection remains independently governed by Rule 18.

---

### TICKET-ADAPT-003 | `business_analyst` | [STATUS: DONE]
**Priority**: HIGH
**Recommended Route**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-ADAPT-002`
**Blocks**: `TICKET-ADAPT-004`

#### File Ownership
- New `.agents/rules/18-adaptive-model-effort-routing.md`.
- New `.agents/skills/adaptive-model-effort-routing/SKILL.md` and its `evals/evals.json`.
- Narrow cross-references in `.agents/rules/11-orchestrator-subagent-delegation.md`, `.agents/rules/17-multi-account-agent-orchestration.md`, `.agents/skills/orchestrator-delegation/SKILL.md`, and `.agents/skills/multi-account-agent-orchestration/SKILL.md`.
- `.claude/rules/orchestrator-subagents.md`, `.claude/rules/multi-account-agent-orchestration.md`, and a new scoped Claude adaptive-routing rule.
- `.agents/AGENTS.md`, `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`, and the authoritative orchestrator agent definition.

#### Boundaries
- Do not edit dispatcher/hook/test code or generated `.codex/agents/*.toml`.
- Keep specialist artifact size limits and existing dirty/user changes intact.

#### Acceptance Criteria
- [x] Rule/skill define required decision fields, rank rubric, floor matrix, quota behavior, override rules, and planning-to-medium gate.
- [x] Skill has 3 realistic eval prompts with expected routing outcomes.
- [x] Orchestrator contract requires an explicit `DispatchDecision` before every executable lane.
- [x] Static model metadata is documented as a fallback hint, not runtime proof.

#### Evidence / Handoff
- Added Rule 18, the specialist skill/evals, required cross-references, scoped Claude mirror, catalog entry, prompt-template handoff, and static orchestrator default update.
- `git diff --check` passed. Ecosystem synchronization, dispatcher/schema enforcement, hook changes, and focused regression remain owned by `TICKET-ADAPT-004` through `TICKET-ADAPT-007`.

---

### TICKET-ADAPT-004 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-003`
**Blocks**: `TICKET-ADAPT-005`

#### File Ownership
- `scripts/multiagent_prompt_command.py`.
- `.agents/config/multiagent_prompt_command.example.yaml`.
- New versioned `.agents/config/multiagent_model_policy.yaml`.
- New decision/receipt JSON schema under `.agents/schemas/` and narrowly required schema helpers only.

#### Detailed Instructions
1. Model a versioned lane assessment and `DispatchDecision` containing ticket/phase, five dimension ranks, quota band, alias, model, effort, rationale, policy version, and medium-gate state.
2. Compute the minimum profile from the maximum rank; validate provider/model/effort support and hard HITL blockers.
3. Revalidate inside `execute_invocation` so direct Python callers cannot bypass the gate.
4. Bind the policy version and decision digest into dry-run output, dispatch identity, prompt evidence, and execution receipt.
5. Allow legacy v1 dry-run with a warning; reject legacy execution with an actionable migration error.

#### Acceptance Criteria
- [x] Missing/invalid decisions fail before subprocess creation.
- [x] CLI overrides cannot disagree with or weaken the validated decision.
- [x] Quota can reroute only at or above the quality floor.
- [x] Provider-specific effort restrictions are enforced.
- [x] Child lane effort is evaluated independently from the root medium gate.

---

### TICKET-ADAPT-005 | `developer` (security lane) | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-004`
**Blocks**: `TICKET-ADAPT-006`

#### File Ownership
- `.claude/hooks/orchestrator_only_guard.py`.
- `.claude/settings.json` only if an installed native dispatch matcher is verified.
- Hook-specific tests are owned by QA in `TICKET-ADAPT-006`, not this lane.

#### Boundaries
- Do not duplicate the scoring matrix in regex and do not expand the secrets/destructive-command guard.
- Reuse the dispatcher/policy validator; keep existing waiver and `HORO_ORCHESTRATOR_ONLY=1` behavior.

#### Acceptance Criteria
- [x] Executable dispatch without a decision or confirmed medium gate is denied.
- [x] Planning-only dry-run remains allowed.
- [x] Native Claude matcher is added only after verification against the installed tool schema.
- [x] Codex/native-runtime limitation is documented; dispatcher remains authoritative.

---

### TICKET-ADAPT-006 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-ADAPT-005`
**Blocks**: `TICKET-ADAPT-007`

#### File Ownership
- `tests/test_multiagent_prompt_command.py`.
- `project/tests/test_claude_governance.py`.
- `project/tests/test_agent_configurations.py`.
- `project/tests/test_ai_agent_ecosystem_sync.py`.
- New focused policy/hook test files only when needed to avoid monolithic tests.

#### Minimum Test Matrix
- [x] Missing assessment, unsupported pair, below-floor route, and mismatched CLI overrides are rejected.
- [x] Critical risk/ambiguity, low quota, unknown quota on broad work, and unconfirmed medium gate fail closed.
- [x] Confirmed root medium permits a valid lane; child high/xhigh remains independently selectable by its own floor.
- [x] Legacy dry-run compatibility and legacy execution rejection are explicit.
- [x] Decision digest/model/effort/policy version are bound to route and receipt evidence.
- [x] Hook blocks invalid execution and allows planning dry-run.

#### Evidence Expected
- Exact focused pytest command, pass count, exit code, and concise failure evidence if blocked.

---

### TICKET-ADAPT-007 | `business_analyst` + `code_reviewer` | [STATUS: DONE]
**Priority**: HIGH
**Recommended Routes**: sync/documentation `gpt-5.6-terra` / `medium`; read-only safety review `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-006`
**Blocks**: Sprint closure

#### Ownership and Sequence
1. `business_analyst` is the sole editor for generated mirrors and governance/task status through the prescribed ecosystem sync.
2. `code_reviewer` is read-only and verifies bypass resistance, secret hygiene, model/effort support, compatibility behavior, and planning-gate evidence.

#### Verification Commands
```bash
python3 -m pytest -q tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py project/tests/test_agent_configurations.py project/tests/test_ai_agent_ecosystem_sync.py
python3 scripts/sync_ai_agent_ecosystem.py --sync
python3 scripts/sync_ai_agent_ecosystem.py --check
python3 project/core/code_reviewer.py --scan-secrets
git diff --check
```

#### Acceptance Criteria
- [x] All focused regression and ecosystem sync gates pass: `77 passed`.
- [x] New/updated skill evals demonstrate correct low-, medium-, and critical-risk routing behavior.
- [x] Secret scan reports zero leaks (1,783 files).
- [x] Code reviewer reports no bypass that can start a child below the validated quality floor.
- [x] Generated Codex files were synced, never hand-edited.

#### Closure Evidence
- Legacy local static metadata was migrated to its existing immutable source provenance without changing the source commit. Full repository suite: `904 passed, 9 skipped`.

---

## 🚀 SPRINT: Shell Environment & Multi-Account Codex Standalone Remediation — 2026-08-25
**Grill Gate Status**: ✅ APPROVED (Ref: [`plans/plan.md`](plans/plan.md))
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-SHELL-001` | `orchestrator` | Grill Gate Approval & Architecture Specification | DONE | None |
| `TICKET-SHELL-002` | `developer` | Backup & Refactor `~/.zshrc` with 100% Backward Compatibility | DONE | `TICKET-SHELL-001` |
| `TICKET-SHELL-003` | `devops` | Standalone Codex Installation & Account Symlink Creation | DONE | `TICKET-SHELL-002` |
| `TICKET-SHELL-004` | `qa_tester` | Shell Environment & Multi-Account Execution Verification | DONE | `TICKET-SHELL-003` |
| `TICKET-SHELL-005` | `code_reviewer` | Final Safety Review & AI Ecosystem Sync Verification | DONE | `TICKET-SHELL-004` |

---

### 🎫 TICKET-SHELL-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: `TICKET-SHELL-002`
#### Detailed Instructions
1. Grill user on requirements, backward compatibility, and standalone strategy.
2. Produce GRILL REPORT in `plans/plan.md`.
#### Acceptance Criteria
- [x] GRILL REPORT prepended to `plans/plan.md`.
- [x] Sprint tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-SHELL-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-001`
**Blocks**: `TICKET-SHELL-003`
#### Detailed Instructions
1. Create backup `~/.zshrc.bak_<timestamp>`.
2. Refactor `~/.zshrc` to clean up duplicate PATH exports and remove intrusive startup echo.
3. Preserve all existing aliases and functions (`codex1-3`, `agy1-3`, `*_login`, `*_logout`, `*_status`, `ssh-node*`, `tailscale-restart`, `open-unifi-ui`, `claude-local*`, `agent-run`).
#### Acceptance Criteria
- [x] Backup created and verified (`~/.zshrc.bak_20260825_142154`).
- [x] `zsh -n ~/.zshrc` passes with zero syntax errors.

---

### 🎫 TICKET-SHELL-003 | `devops` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-002`
**Blocks**: `TICKET-SHELL-004`
#### Detailed Instructions
1. Install standalone Codex via `curl -fsSL https://chatgpt.com/codex/install.sh | sh`.
2. Symlink `~/.codex/packages` to `~/.ai-accounts/codex/account{1,2,3}/packages`.
#### Acceptance Criteria
- [x] `~/.codex/packages/standalone/current/codex` executable exists (v0.149.1).
- [x] `~/.ai-accounts/codex/account{1,2,3}/packages` symlinks point to `~/.codex/packages`.

---

### 🎫 TICKET-SHELL-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-003`
**Blocks**: `TICKET-SHELL-005`
#### Detailed Instructions
1. Execute `codex1 --version`, `codex2 --version`, `codex3 --version` via zsh.
2. Verify absence of `managed standalone Codex install not found` error.
3. Verify `agent-run`, `claude-local`, `agy1-3` aliases and syntax.
#### Acceptance Criteria
- [x] Multi-account codex executions succeed without standalone missing error (`codex-cli 0.149.1` across all 3 accounts).
- [x] `codex1_status`, `codex2_status`, `codex3_status` report active login.

---

### 🎫 TICKET-SHELL-005 | `code_reviewer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-SHELL-004`
**Blocks**: None
#### Detailed Instructions
1. Run `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check`.
2. Ensure secret hygiene and zero regressions.
#### Acceptance Criteria
- [x] Agent ecosystem sync checks PASS (SDLC and Codex sync 100%).
- [x] Secret scan passed (0 leaks across 1770 files).

---

Historic completion details have been archived to [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).
Current sections below track active work and release gates only.
## 📋 PLANNED SPRINT: Metaphysics Learning Roadmap & Question-Forecast Alignment
**Grill Gate Status**: BLOCKED — scope is not complete while child tickets and release gates remain pending due to external/environmental blockers.
**Sprint Tracking Lead**: `orchestrator` / `business_analyst`
**Source Documents**:
- [`plans/metaphysics_learning_roadmap.md`](plans/metaphysics_learning_roadmap.md)
- [`plans/plan.md`](plans/plan.md)
- [`plans/question_forecast_alignment_spec.md`](plans/question_forecast_alignment_spec.md)
- [`plans/todo_tasks_plan.md`](plans/todo_tasks_plan.md)

**Plan Coverage Matrix**:

| Plan | Covered scope | Kanban disposition |
|---|---|---|
| `metaphysics_learning_roadmap.md` | Five branches, source ingestion, deterministic engines, fine-tuning, MCP, and UI visualizer | Implementation closed under `TICKET-META-002`/`003`; release gates remain in `TICKET-META-005`/`006` |
| `plan.md` | Phases 1–16, MLOps/provider/Grafana work, governance, multi-cloud, quality gates, and future model architecture | Historical phases are archived; active/future platform work is tracked under `TICKET-META-005` |
| `question_forecast_alignment_spec.md` | Six benchmark domains, 100-point rubric, validator threshold, prompt/debate routing | Implementation and focused validation closed under `TICKET-META-004` |
| `todo_tasks_plan.md` | Six implementation workstreams and five-phase SDLC execution flow | Workstreams have evidence under `TICKET-META-003`/`004`; release closure remains under `TICKET-META-005`/`006` |

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-META-001` | `orchestrator` / `business_analyst` | Consolidate and execute the five-branch metaphysics roadmap, six-domain question/forecast alignment benchmark, and six TODO workstreams | BLOCKED — HITL DEPLOY | None |
| `TICKET-META-002` | `domain_master` / `developer` | Implement and test the five-branch deterministic metaphysics calculation modules | DONE | `TICKET-META-001` |
| `TICKET-META-003` | `developer` | Execute OCR/RAG ingestion, dataset generation, fine-tuning, model fusion, MCP, and visualizer integration | DONE | `TICKET-META-001` |
| `TICKET-META-004` | `developer` / `qa_tester` | Implement six-domain question/forecast alignment, focused prompting, debate routing, and validator benchmarks | DONE | `TICKET-META-001` |
| `TICKET-META-005` | `devops` / `developer` | Reconcile active/future `plan.md` platform work: providers, observability, CI/CD, governance, and release architecture | DONE | `TICKET-META-001` |
| `TICKET-META-006` | `qa_tester` / `code_reviewer` / `business_analyst` | Run full QA, security, synchronization, release evidence, and final Kanban documentation handoff | DONE | `TICKET-META-002`..`005` |
| `TICKET-META-007` | `orchestrator` / `business_analyst` | Refresh sub-agent delegation governance and Claude Code three-level command-control examples | DONE | `TICKET-META-001` |
| `TICKET-META-008` | `orchestrator` / `business_analyst` / `devops` | Preserve account-migration continuity and quota-exhaustion handoff, including active blockers, non-secret credential status, and safe resume commands | DONE | `TICKET-META-005`, `TICKET-META-006` |
| `TICKET-META-009` | `developer` / `qa_tester` | Safely upgrade Python/Rust dependency lockfiles and validate compatibility after active release gates are clear | DONE | `CP-03-AZURE`, `CP-04-PW`, `CP-05-RELEASE` |
| `TICKET-QA-PW-SMOKE-20260825` | `qa_tester` | Re-run and reconcile Vercel production smoke E2E | DONE | `G-META-006-PW` |
| `PROMPT-GOV-001` | `business_analyst` / `orchestrator` | Govern multi-account PromptCommand routing, quota/account evidence, bounded retries, HITL escalation, and synchronized governance mirrors | DONE | `TICKET-META-008`, Rule 17 |
| `TICKET-ORCH-ONLY-002` | `business_analyst` / `orchestrator`; aliases `codex1`, `codex2`, `agy1`, `agy2` | Enforce governance -> rules -> hooks hierarchy; keep root/current session orchestrator-only and obtain four distinct alias receipts | BLOCKED — HITL DISPATCH CONTRACT | Rule 17, current CORS/separation lanes |
| `TICKET-ALIAS-RC2-003` | `developer` / `qa_tester` / `code_reviewer`; aliases `codex1`, `codex2`, `agy1`, `agy2`; monitored by `orchestrator` | Implement, validate, review, then redispatch four distinct lanes with Result Contract v2 | BLOCKED — CODEX1 ATTEMPTS EXHAUSTED | `TICKET-ORCH-ONLY-002`, Rule 17 |
| `TICKET-ALIAS-RC2-004` | `developer` / `qa_tester` / `code_reviewer`; aliases are bounded read-only diagnostics, monitored by `orchestrator` | Content-free provider parse-reason taxonomy and one fresh `codex1` diagnostic authorization | TODO — OWNER AUTHORIZED / QUOTA UNKNOWN | `TICKET-ALIAS-RC2-003` immutable blocker, QA/retry gate, Rule 17 |

### TICKET-ORCH-ONLY-002 | Orchestrator-Only Control and Four-Alias Dispatch | [STATUS: BLOCKED — HITL DISPATCH CONTRACT]

**Scope**: require the root/current session to delegate all implementation,
QA, git mutation, deploy, and publish work. Its permitted work is decomposition,
dispatch, monitoring, receipt collection, conflict resolution, HITL, and final
gate decisions. **Out of scope**: application/workflow implementation by the
root, credentials, secret values, staging, commits, pushes, deploys, and
publishes. **Dependencies**: the current CORS and static/backend-separation
lanes, configured aliases, and the Claude PreToolUse hook registration.

**Success / stop condition**: Rule 17, skills/mirrors, board/plan, Claude rule,
and hook contract agree; every explicitly requested alias returns its actual
receipt or a safe `BLOCKED` result. Stop and return `NEEDS_HITL` for an
unrecorded root action, missing alias execution evidence, credentials, or an
ownership conflict.

| Alias | Bounded lane | Writable ownership | Required receipt | Status |
|---|---|---|---|---|
| `codex1` | Vercel gateway CORS independent review | None; read-only gateway-source and test review | receipt `01a03849-759b-7b21-826e-35697a0743ee`; return `0`; `1123` bytes; invalid result contract | BLOCKED after 3 attempts |
| `codex2` | HF/FastAPI CORS independent review | None; read-only backend-source and test review | receipt `01a03849-75a8-7150-98a3-1b926b818477`; return `0`; `1799` bytes; invalid result contract | BLOCKED after 3 attempts |
| `agy1` | Static frontend/HF Docker separation review | None; read-only release-routing review | final child return `1`; `376` bytes; invalid result contract | BLOCKED after 3 attempts |
| `agy2` | Cross-lane release-gate and CORS evidence review | None; read-only receipts and release boundaries | final child return `1`; `374` bytes; invalid result contract | BLOCKED after 3 attempts |

**Hierarchy**: (1) governance policy defines the root-only boundary and waiver
contract; (2) Rule 17, the multi-account skill, and Claude mirror define the
dispatch contract; (3) `.claude/settings.json` registers PreToolUse hooks that
enforce the marked Claude session. The hook is intentionally narrow and
permits monitor/dispatch activity. It recognizes a waiver only when
`HORO_ROOT_WAIVER_ID` matches `ROOT-WAIVER: <id>` recorded in both this board
and `plans/plan.md`; no waiver marker is active for this ticket.

**Runtime limitation**: Claude hooks apply only to Claude Code tool calls and
only when the launcher sets `HORO_ORCHESTRATOR_ONLY=1`. They cannot determine a
Codex root session or enforce Codex tools automatically. Codex relies on this
governance contract, alias receipts, and final gate review until a native Codex
hook exists. This limitation is a safeguard, not execution proof.

**Acceptance checklist**:

- [x] Governance -> rules -> hooks hierarchy is documented without changing application code.
- [x] Existing Claude PreToolUse registration retains secret/destructive guard and adds an orchestrator-only guard.
- [x] Guard blocks marked-root implementation edits, QA commands, git mutations, and deploy/publish commands unless a recorded waiver marker exists.
- [x] Guard permits orchestration-safe monitoring and dispatch commands.
- [x] All four alias attempts have safe terminal metadata recorded; every child result contract is invalid and every lane is `BLOCKED` after the three-attempt limit.
- [x] Focused hook tests and ecosystem `--sync` followed by `--check` are green; sync changed no generated Codex files.

**Historical closure**: these four receipts remain `BLOCKED` and do not close
the CORS/static-separation release gate. On 2026-08-25 the owner authorized a
fresh Result Contract v2 protocol and explicitly did not waive the receipts.
The authorized work continues only under `TICKET-ALIAS-RC2-003`; its retry
counters start at attempt 1 and cannot rewrite this historical record.

### TICKET-ALIAS-RC2-003 | Result Contract v2 and Four-Alias Redispatch | [STATUS: BLOCKED — CODEX1 ATTEMPTS EXHAUSTED]

**Authorization**: owner instruction received 2026-08-25 authorizes Result
Contract v2 and a terminal CLI workaround in delegated child lanes. There is
no receipt waiver and no root-action waiver. The current/root session remains
orchestrator-only and may plan, delegate, monitor, collect receipts, and decide
the gate; it must not implement, test, review, or invoke the alias CLI itself.

**In scope**: v2 schema/config/adapter implementation by an ownership-scoped
developer child; provider-native Codex structured JSON/JSONL with output-schema
support; AGY native stream-JSON parsing; independent QA and security review;
then four fresh read-only terminal dispatches. **Out of scope**: changing prior
receipts, authentication or secret inspection, application/release mutation,
commit, push, deploy, publish, or shared writable ownership.

**Two-layer contract**:

- `ExecutionReceipt` binds protocol version, dispatch ticket/attempt, alias,
  provider/adapter, objective/ownership, safe quota status, timestamps,
  exit/transport status, safe provider session/process id when available,
  output byte count/SHA-256, and normalized `WorkResult` SHA-256.
- `WorkResult` contains `Status`, `Scope owned`, `Evidence`, `Findings`,
  `Changed files`, `Residual risk`, and `Recommended next action`.

Validation is fail closed: missing/malformed fields or events, identity/digest
mismatch, ambiguous final event, secret-bearing output, nonzero execution
without a typed failure result, or exit zero without a valid `WorkResult` is
not a receipt. Free-form inference and adapter fallback require fresh HITL.

| Alias | Fresh v2 lane | Ownership | v2 attempt | Status |
|---|---|---|---|---|
| `codex1` | Vercel gateway CORS independent review | Read-only | 3 executed | BLOCKED — `invalid-child-result-contract`; no valid receipt; retry limit exhausted |
| `codex2` | HF/FastAPI CORS independent review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |
| `agy1` | Static frontend/HF Docker separation review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |
| `agy2` | Cross-lane release-gate and CORS evidence review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |

**Checklist**:

- [x] Record fresh owner authorization for Result Contract v2; no waiver.
- [x] Preserve all four prior attempts as immutable historical `BLOCKED` evidence.
- [x] Define two-layer receipt/result governance, provider-native adapters, fail-closed rules, and fresh per-alias counters.
- [x] Run ecosystem `--sync` then `--check`: 19 Codex definitions synchronized, 0 updated, 0 obsolete, and no generated `.codex/agents` change.
- [ ] Developer child implements dispatcher/config/schema/template changes within exclusive ownership.
- [ ] Developer/DevOps child supplies an approved runtime config path and an explicit read-only role or validated sandbox override; example config and default Codex `workspace-write` are rejected.
- [ ] QA child validates valid, malformed, ambiguous, nonzero-exit, identity/digest mismatch, and secret-redaction cases.
- [ ] Code reviewer verifies fail-closed behavior, retry/HITL boundaries, root-only separation, and backward compatibility.
- [x] Focused QA completed with `87 passed`.
- [x] `codex1` attempt 3 was executed through its read-only lane and failed closed as `invalid-child-result-contract`; it produced no valid receipt.
- [x] Hold `codex2`, `agy1`, and `agy2` attempt 3: none was invoked after the terminal `codex1` failure.
- [ ] Child execution lanes return four distinct schema-valid v2 receipts. BLOCKED: `codex1` has exhausted its three attempts.
- [ ] Orchestrator confirms four distinct valid receipts and decides the release gate. BLOCKED pending a fresh owner decision and new ticket.

**Checkpoint evidence (2026-08-25)**: focused QA passed (`87 passed`). The
`codex1` read-only lane executed attempt 3 and failed closed with
`invalid-child-result-contract`; no valid receipt exists. `codex2`, `agy1`, and
`agy2` attempt 3 were not invoked. Historical attempts and release evidence are
preserved above and are not relabeled by this checkpoint.

**Success / stop**: close only when implementation, QA, and review are green and
all four fresh alias lanes provide distinct schema-valid v2 receipts. This ticket
is now `BLOCKED`: `codex1` has exhausted its three-attempt limit, so no further
alias dispatch may occur under `TICKET-ALIAS-RC2-003`. A fresh owner decision
and new ticket are required before any additional alias dispatch. Stop on
ownership conflict, authentication/permission/billing, secret exposure,
adapter ambiguity, invalid receipt, or any root implementation/CLI execution.

**Read-only execution gate**: QA found that only an example dispatch config is
currently present and Codex roles default to `workspace-write`. No v2 review
alias may start until a child proves an approved runtime config path and either
an explicit read-only role or a validated provider sandbox override. Prompt
instructions are not isolation. Missing proof is `BLOCKED`, not a waivable
receipt validation warning.

**Governance evidence (2026-08-25)**: authoritative and Antigravity skill
mirrors are byte-identical. Ecosystem sync and check both returned `0`; the
generator reported 19 Codex agent definitions, 0 updated, and 0 obsolete. No
generated Codex agent file was manually edited or changed by this governance
update. Existing trailing whitespace in unrelated earlier board additions is
preserved and is not v2 evidence.

### TICKET-ALIAS-RC2-004 | Content-Free Parse-Reason Diagnostic Follow-On | [STATUS: TODO — OWNER AUTHORIZED / QUOTA UNKNOWN]

**Fresh authorization checkpoint (2026-08-25)**: after the exhausted
`TICKET-ALIAS-RC2-003` `codex1` attempts, the owner gave fresh `approve all`
authorization for this new, bounded follow-on ticket only. `RC2-003` remains
immutable `BLOCKED` history: this ticket neither reopens it nor changes any
prior counter, result, receipt, or release-gate state.

**Scheduling metadata**: **Severity: CRITICAL**. **Work Effort: S**. Quota is
`unknown`; this is a bounded-lane-only authorization, not authority for broad
dispatch. Stop immediately if the runtime reports less than 10% remaining.

**Scope grill**:

- **IN**: content-free `provider_parse_reason` taxonomy and its focused tests;
  one fresh, explicitly recorded `codex1` read-only diagnostic attempt under
  this ticket; safe terminal classification and retry/HITL documentation.
- **OUT**: raw JSONL or provider text; receipt/session/process identifiers;
  artifact or runtime paths; secrets or credentials; application/release
  changes; deployment, publishing, staging, commits, pushes, or other git
  mutation. Do not retain any of those values in the board, plan, tests, or
  diagnostic evidence.
- **Dependencies / assumptions**: `RC2-003` remains blocked; the taxonomy is
  implemented and focused-tested by separately owned developer/QA lanes; the
  read-only isolation gate and result-contract validation must pass before an
  alias is invoked; quota is still `unknown` and may not be inferred.
- **Success**: a content-free, typed parse-reason classification is covered by
  focused tests and one new `codex1` read-only attempt returns only an approved
  terminal status. A valid result may permit separately recorded, bounded
  `codex2`, `agy1`, then `agy2` attempts; it does not authorize them by itself.
- **Stop**: runtime quota below 10%, unknown/failed read-only isolation,
  invalid or ambiguous result contract, permission/authentication/billing
  issue, ownership conflict, secret exposure, or any attempt to retain
  prohibited content. Return `NEEDS_HITL` where the next action is not already
  explicitly authorized below.

**Dependency and retry sequence**:

| Order | Owner / alias | Authorized action | Gate / next state |
|---|---|---|---|
| 1 | `developer` / `qa_tester` | Implement and test only the content-free `provider_parse_reason` taxonomy. | Focused QA must pass; no provider payload retention. |
| 2 | `code_reviewer` | Read-only review of taxonomy, test coverage, redaction boundary, and retry gate. | Must accept fail-closed boundary before any alias attempt. |
| 3 | `codex1` | Exactly one fresh, read-only diagnostic attempt, recorded as `RC2-004/codex1/attempt-1`. | If invalid/ambiguous/blocked, stop this ticket and return `NEEDS_HITL`; no automatic retry. |
| 4 | `codex2` | One separately recorded, bounded read-only attempt only after a valid `codex1` result and an explicit recorded attempt authorization. | Otherwise not dispatched. |
| 5 | `agy1` | One separately recorded, bounded read-only attempt only after the preceding valid gate and explicit recorded attempt authorization. | Otherwise not dispatched. |
| 6 | `agy2` | One separately recorded, bounded read-only attempt only after the preceding valid gate and explicit recorded attempt authorization. | Otherwise not dispatched. |

**Acceptance checklist**:

- [ ] Taxonomy uses only approved, content-free `provider_parse_reason` values; no raw output, identifiers, paths, or secrets are persisted.
- [ ] Focused taxonomy tests pass under their separately owned QA lane.
- [ ] Independent review confirms read-only isolation, fail-closed parsing, and the no-retention boundary.
- [ ] Exactly one fresh `codex1` diagnostic attempt is recorded under `RC2-004`; it does not alter `RC2-003` history.
- [ ] `codex2`, `agy1`, and `agy2` remain undispatched unless each prerequisite valid result and separately recorded attempt authorization exists.
- [ ] No deploy/publish/git mutation occurred; only documentation/scheduling evidence and separately owned taxonomy/test work are permitted.

### 🎫 PROMPT-GOV-001 | `business_analyst` / `orchestrator` | [STATUS: DONE]

**Objective**: establish auditable, ownership-scoped multi-account agent orchestration without treating routing configuration as execution proof.

**In scope**: `PROJECT_TASKS.md`, `plans/plan.md`, Rule 17, the
`multi-account-agent-orchestration` skill, its synchronized governance mirrors,
and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`.

**Out of scope**: source code, tests, deployments, publishing, authentication,
credential mutation, secret values, and external systems.

**Required evidence**: account alias/provider, non-secret quota band or status,
safe route/session metadata when available, child result, attempt number,
artifact paths, and timestamps. A rendered alias/route/model/configuration is
routing intent only and cannot close a dispatch.

**Retry/HITL policy**: retry only the same bounded actionable failure; after
three consecutive failures, or immediately for credentials, permissions,
billing, production mutation, ownership conflict, or high-impact judgment,
return `NEEDS_HITL` with the exact decision or safe operator command.

**Acceptance criteria**:

1. Rule 17 defines ownership isolation, non-secret quota/account evidence,
   retry limits, HITL triggers, result contract, and closure gate.
2. The skill has valid frontmatter, ASCII status-tag guidance, exact safe
   command paths, and `DONE`/`BLOCKED`/`NEEDS_HITL` semantics.
3. PromptCommand documentation states dry-run default, explicit execution,
   no-secret handling, and execution-proof requirements.
4. `.agents/AGENTS.md` catalogs the skill and synchronized mirrors match the
   authoritative skill/rule content.
5. `python3 scripts/sync_ai_agent_ecosystem.py --sync` completes and the final
   `--check` passes without source/test edits.

**Final closure checklist**:

- [x] Board and plan status include ticket owner, evidence, blockers, and next action.
- [x] Rule, skill, Claude mirror, and Antigravity skill mirror are synchronized.
- [x] PromptCommand template preserves ownership, quota, retry, and HITL fields.
- [x] No secret values, credential files, source, or tests were changed.
- [x] Sync, focused governance checks, and `git diff --check` pass.
- [x] Any unresolved external permission or account decision is marked `NEEDS_HITL`.

**Closure evidence (2026-08-25)**: `python3 scripts/sync_ai_agent_ecosystem.py --sync` and its embedded checks passed; the new skill quick validator passed; the authoritative skill and Antigravity mirror match; and `git diff --check` passed for the owned governance files.

## 🧩 Decoupled Release Closure Checkpoints

These checkpoints replace the previous single release-closure workstream. They are intentionally small, independently verifiable, and resumable across quota/account changes.

| Checkpoint | Owner | Scope | Exit evidence | Stop condition |
|---|---|---|---|---|
| `CP-00-DOCS` | `business_analyst` | Reconcile ticket/plan/evidence status before execution | Updated board, plans, and evidence index | **DONE** — proceed to CP-01-LOCAL |
| `CP-01-LOCAL` | `qa_tester` / `code_reviewer` | Re-run local QA, secret scan, agent sync, quality gate | Timestamped command outputs and report paths | **DONE** — local evidence green; proceed only to separately gated external checkpoints |
| `CP-02-HF` | `devops` | Verify canonical HF origin, `/health`, deterministic API | Fresh canonical probe JSON with explicit status (`project/tests/hf_canonical_reprobe_2026-08-24.json`, `vercel_reprobe_2026-08-24.json` 3/3 GREEN) | **PASS** — HF canonical & Vercel fallback verified |
| `CP-03-AZURE` | `devops` | Validate complete Azure Actions credentials and deploy | Workflow proving login, provisioning, and `/health` (Run `32630424001` SUCCESS) | **PASS** — Azure Container Apps deploy healthy |
| `CP-04-PW` | `qa_tester` | Run the bounded production smoke Playwright profile | `project/tests/prod_button_regression_report.json` (2026-08-25 05:17:45 UTC): Vercel smoke 13/13 passed, 0 failed | **DONE** — `TICKET-QA-PW-SMOKE-20260825`; full-profile coverage remains separately unfinished |
| `CP-05-RELEASE` | `orchestrator` / `devops` | Consolidate all green release gates | Single all-green release matrix across local, HF, Vercel, and Azure | **PASS** — All multi-cloud release gates cleared |
| `CP-06-HANDOFF` | `business_analyst` | Final document sync, quota-safe handoff, parent transition | Updated board, plan links, evidence index | **READY** — Ready for operator final sign-off |

### Checkpoint execution policy

1. Execute only one checkpoint per work session unless its evidence is already present.
2. At the end of every checkpoint, record status, timestamp, command/artifact, blocker, and next checkpoint.
3. When quota is below 10%, stop implementation/release work and complete only the quota-safe update in `TICKET-META-008`.
4. No checkpoint may claim another checkpoint's evidence; local green tests do not prove external deployment health.

### 🎫 TICKET-META-001 | `orchestrator` / `business_analyst` | [STATUS: BLOCKED — HITL DEPLOY]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: Final production handoff only; implementation, QA, and local release evidence are complete.

**Current status**: All historical child implementation and local QA tickets are complete. The active release candidate is governed solely by `TICKET-V3UI-007` (local version target `1.0.0.c9f9161` / `c9f9161`). It is blocked pending fresh, hash-bound evidence and explicit HITL authorization for any production mutation. `TICKET-V3UI-006` is a historical `6c351ba` baseline and cannot prove this candidate.

#### Detailed Instructions
1. **Scope and architecture** — implement the five roadmap branches and their calculation/knowledge surfaces: Three Cosmic Styles (Tai Yi, Da Liu Ren, Qi Men), Destiny Analysis (BaZi improvements, Zi Wei, Qi Zheng Si Yu), Divination (I Ching, Liu Yao, Mei Hua), Physiognomy/Feng Shui (Xuan Kong, San He, Mian Xiang), and Date Selection (Ze Ji).
2. **Knowledge pipeline** — run the OCR/Obsidian ingestion flow, maintain the RAG vector store and exported ShareGPT JSONL dataset, and preserve traceable classical-source metadata.
3. **Deterministic engines** — implement or extend the pure-Python calculation modules under `project/core/`, including deterministic unit tests for solar terms, chart placement, interactions, and fallback behavior.
4. **Model and delivery pipeline** — execute the dataset/fine-tuning, adapter-to-GGUF/Ollama fusion, MCP tool integration, and Glassmorphism dashboard visualization work described by the roadmap and `plans/todo_tasks_plan.md`.
5. **Question/forecast alignment** — implement the six benchmark domains in `plans/question_forecast_alignment_spec.md`; pass the user’s `user_query` and extracted focus into `project/core/prompt_manager.py` and `project/core/multi_agent_debate.py`; validate direct relevance, astrological consistency, canonical evidence, and actionable guidance using the 100-point rubric and `Confidence Score > 0.85` validator threshold.
6. **TODO workstreams** — complete the six deliverables in `plans/todo_tasks_plan.md`: model fusion, external provider routing, Swiss Ephemeris, batch vault ingestion, CI/CD automation, and consultant UI enhancements.
7. **SDLC handoff** — follow the repository workflow from planning through implementation, QA, release verification, and final Kanban evidence. Create child tickets for developer, QA, DevOps, domain, and review work before execution begins.
8. **Complete `plans/plan.md` coverage** — treat its historical completed phases as required traceability/evidence, and its active or future sections as execution scope:
   - Phase 1–3: all-16-discipline E2E/snapshot visualizer baseline, seven extended SVG visualizers, and the multimodal 16-discipline consensus matrix.
   - Phase 4–6: external multi-provider gateway, multilingual/i18n interpretation, production delivery/PWA/offline support, and consultation report export.
   - Phase 7–10: DaYun/LiuNian timeline and transit clock, voice TTS/STT, synastry compatibility matrix, and interactive Ze Ji calendar/date selector.
   - Phase 11–14: LuoPan/dream decoder, multi-scenario life simulation, Imperial White/Crimson UI, and live multi-turn consultant chat with grounded RAG.
   - Phase 15–16: Kaggle NumPy/BNB pipeline compatibility and the three-tier notebook AST/pre-commit/deployment safety gate.
   - Continuous MLOps, hybrid LLM provider expansion, and Grafana latency/observability tuning.
   - Skill-context governance, agent synchronization, Grafana Cloud integration, multi-cloud architecture, quality-control standards, future LLM model expansion/circuit breaking, and the ten-policy operating consensus matrix.
9. **Status reconciliation** — link each `plan.md` phase to its existing Kanban ticket and verification evidence; do not re-open phases already marked `DONE`. Any active or future item without a current ticket must receive a child ticket before implementation.

#### Acceptance Criteria
- [x] All roadmap modules and their source/algorithm boundaries are mapped to implementation files and child tickets.
- [x] OCR/RAG ingestion produces traceable Markdown, vector-store, and JSONL outputs without losing source metadata.
- [x] Calculation engines have deterministic tests covering the implemented branches and pass the project’s required pytest gate.
- [x] The six-domain benchmark contains executable cases for direct relevance, logic consistency, canonical evidence, and actionable guidance.
- [x] Prompt/debate routing preserves the user’s requested focus, and validator evidence meets `Confidence Score > 0.85`.
- [x] The six TODO workstreams have implementation, test, and release evidence recorded in the child tickets.
- [x] Every section of `plans/plan.md` is dispositioned as `DONE` with evidence, `DOING`, or `TODO` with a child ticket; no plan section is left untracked.
- [x] CI/CD, secret scan, agent synchronization, pre-deployment review, and required E2E/UI regression gates pass before release.
  - **Current status:** Local gates are GREEN — `code_reviewer --review --use-python` reports `READY_FOR_PROD` (`645 passed, 4 skipped, 6 warnings`); quality gate 4-stage PASSED (`100%`); secret scan `0` leaks (1,533 files); agent sync 100% synchronized; button regression `25/25` passed. HF canonical backend `CP-02-HF` is now **PASS** (3/3 green, 2026-08-23 11:12 +07). Remaining blockers are external: Azure RBAC (`CP-03-AZURE`) and production Playwright authorization (`CP-04-PW`) — both require operator action, not local implementation.
  - **Next action:** Execute the consolidated release gate matrix once Azure RBAC + Playwright are cleared. Local evidence bundle is ready.
  - **Gate Ref:** `G-META-001-CORE`.
- [x] `PROJECT_TASKS.md`, the four source plans, and the final delivery evidence are synchronized with the actual implementation state.
  - **Current status:** `PROJECT_TASKS.md`, `plans/plan.md`, `plans/todo_tasks_plan.md`, `plans/question_forecast_alignment_spec.md`, and `plans/metaphysics_learning_roadmap.md` are aligned with implementation state as of 2026-08-23 11:12 +07. HF canonical backend green status recorded in the checkpoint tables. Final lockstep still waits on Azure RBAC + Playwright before `CP-05-RELEASE` can fire.
  - **Next action:** Finalize the evidence bundle only after all pending items in `Unresolved Gate Recovery Actions` are completed and verified in one run.
  - **Gate Ref:** `G-META-001-SYNC`.

#### Definition of Done
This ticket is `DOING` while child tickets are being executed. It moves to `DONE` only when every child ticket is complete, all acceptance evidence is recorded, the relevant test/release gates pass, and the final Kanban/documentation synchronization is verified.

### 🎫 TICKET-META-007 | `orchestrator` / `business_analyst` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`
**Blocks**: Future safe delegation and Claude Code prompt reuse.

#### Scope Boundary
- **IN**:
  1. Refresh the orchestrator delegation model for a new sub-agent round.
  2. Define one clear owner per workstream: BSA/status, DevOps/release, QA/evidence, Developer/implementation, and Code Reviewer/safety.
  3. Add Claude Code three-level command governance: hooks as hard constraints, context-aware rules, and compact `CLAUDE.md` global context.
  4. Provide copy-ready prompt examples for root orchestrator, DevOps, QA, and BSA delegation.
- **OUT**:
  1. Reading or printing secret values.
  2. Rotating or syncing credentials.
  3. Running external deployment, production Playwright, or push operations.
  4. Editing generated `.codex/agents/*.toml` manually.

#### New Delegation Round Matrix
| Lane | Agent | Ownership | Current action | Stop condition |
|---|---|---|---|---|
| BSA/status | `business_analyst` | `PROJECT_TASKS.md`, `plans/**`, governance docs, skills/rules | Update task visibility and Claude Code command-governance documentation | `DONE` when docs identify ownership, evidence, blockers, and HITL actions |
| DevOps/release | `devops` | CI/CD workflows, cloud deployment evidence, secret names only | Monitor external release blockers and provide operator commands without exposing secret values | `NEEDS_HITL` if platform credential/permission update is required |
| QA/evidence | `qa_tester` | pytest/API/UI/Playwright readiness and reports | Validate whether live backend and production Playwright gates are runnable | `BLOCKED` until live backend health and production E2E authorization are available |
| Developer/implementation | `developer` | Assigned source/workflow/test files only | Patch implementation only when a verified failing gate maps to a specific file owner | `DONE` after targeted tests pass |
| Safety review | `code_reviewer` | Secret scan, safety audit, release decision support | Confirm no secret leaks and no unsafe release claim | `NEEDS_HITL` if a leak or unsafe external gate remains |

#### Acceptance Criteria
- [x] Claude Code Level 1 hook wiring exists in `.claude/settings.json`.
- [x] Context-aware Claude Code rules exist under `.claude/rules/`.
- [x] Repository governance rule exists in `.agents/rules/12-claude-code-three-level-governance.md`.
- [x] `orchestrator-delegation` skill includes the standard delegation round and copy-ready prompt examples.
- [x] `CLAUDE.md` points to the three-level governance model without becoming the only enforcement layer.
- [x] Run syntax/secret-scan validation for the changed governance files.
  - **Evidence:** `python3 -m json.tool .claude/settings.json` passed; `PYTHONPYCACHEPREFIX=/private/tmp/horo_pycache python3 -m py_compile .agents/hooks/pre_tool_check.py .agents/hooks/post_tool_audit.py` passed; Claude hook JSON spot checks deny force-push and `.env` reads; `python3 project/core/code_reviewer.py --scan-secrets` passed with `0` leaks across `1,523` files; `python3 scripts/sync_codex_agents.py --check` and `python3 scripts/sync_sdlc_agents.py --check` passed.

#### HITL Notes
- Credential, production deploy, and production Playwright execution remain HITL-gated unless the user provides current explicit authorization and required non-secret evidence.
- Any secret value printed by a CLI must be considered compromised and rotated before propagation.

### 🎫 TICKET-META-008 | `orchestrator` / `business_analyst` / `devops` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-005`, `TICKET-META-006`
**Blocks**: Safe account handoff when current assistant/account quota is exhausted.

#### Scope Boundary
- **IN**:
  1. Keep `PROJECT_TASKS.md` and `plans/plan.md` updated with account-migration status before context/quota exhaustion.
  2. Record only non-secret credential state: GitHub CLI auth validity, Doppler CLI auth availability, Telegram token/chat-id presence, and exact blocked gates.
  3. Maintain safe resume commands that do not print secret values.
  4. Ensure dirty-file policy is explicit: commit scoped work separately, review unrelated dirty files by batch, quarantine generated artifacts only after review, and clean after 7 stable days.
- **OUT**:
  1. Printing or copying secret values into documentation.
  2. Editing generated `.codex/agents/*.toml` manually.
  3. Making release claims before all external gates are green.

#### Current Account/Quota Handoff Status
- Latest scoped commits:
  - `2638d84` — Scoped Telegram bot and controller fixes.
  - `a6467e5` — Telegram notification secret config support.
  - `87ecc84` — Persist Telegram Chat ID from bot/webhook updates.
- Telegram runtime check: bot token is present locally; `TELEGRAM_CHAT_ID=804297094` is present in `.env` and verified valid via `getChat` API (`chat_type=private`, `ok=true`); `TELEGRAM_BOT_TOKEN` present (46 chars).
- GitHub CLI: `gh auth status` now reports account `pphothidaen` authenticated via keyring with `repo` and `workflow` scopes; do not print token values.
- Doppler CLI: `doppler me` reports authenticated; Doppler dry-run verified (`sync_doppler_secrets.py`).
- Local secret hygiene: expired `GH_TOKEN` was removed from `.env` and `.env.production`; latest secret scan remains `0` leaks across `1,530` files.
- Governance enforcement: `scripts/agent_quota_status_guard.py` checks `/status`/runtime quota signals; `.agents/hooks/pre_tool_check.py` and `.claude/hooks/pre_tool_guard.py` invoke it when quota status is present, and `bsa-doc-skill-management` defines the low-quota handoff workflow.

#### Documentation checkpoint result — `CP-00-DOCS` (2026-08-22 21:12 +07)
- **Status:** DONE for the owned documentation/governance scope; this does not close the parent release workstream.
- **Scope grill:** in scope was board/plan/evidence reconciliation and a safe next-ticket handoff; out of scope were source/tests/workflows, generated or legacy agent definitions, deployment, credentials, secret sync, and production E2E. Inputs were the current worktree, the canonical HF probe artifact, and existing local evidence. Success requires aligned checkpoint status, explicit blockers, non-secret credential state, and a runnable next action; stop before any external mutation or green release claim.
- **Evidence:** `git status --short`; `git diff --check`; `python3 scripts/sync_ai_agent_ecosystem.py --check` passed. `project/tests/backend-release-check-hf-canonical.json` remains authoritative and records static `404`, backend `/health` `503`, and deterministic API `503`.
- **Reconciled files:** `PROJECT_TASKS.md`, `plans/plan.md`, and `plans/todo_tasks_plan.md`. Existing unrelated `project_tickets.md` edits were preserved and not modified.
- **Next executable checkpoint:** `CP-01-LOCAL`, owned by `qa_tester` / `code_reviewer`. Use the documented local QA, secret scan, sync, and quality-gate commands; stop on any local failure and do not deploy.
- **HITL required:** owner action remains necessary for Doppler secret sync verification, review of unrelated dirty files, HF Space static CDN flap resolution, and production Playwright full-profile authorization. Telegram chat-id is verified; Doppler CLI is authenticated. None of the remaining items is claimed green here.

#### Safe Resume Commands
```bash
python3 project/core/code_reviewer.py --scan-secrets
python3 -m pytest project/tests/test_telegram_bot.py project/tests/test_secret_redaction.py project/tests/test_telegram_connection_config.py -q
python3 scripts/sync_doppler_secrets.py --env-file .env --project horo-consultant --config prd --dry-run
gh auth status
doppler me
```

#### Acceptance Criteria
- [x] Account-migration continuity ticket exists in `PROJECT_TASKS.md`.
- [x] Plan-level quota/account migration guard is recorded in `plans/plan.md`.
- [x] Governance hook/rule/skill enforcement exists for `/status` or runtime quota below 10%.
- [x] GitHub CLI is re-authenticated without printing values.
- [x] Telegram secrets are synced to GitHub Actions without printing values.
  - **Verified (2026-08-23 16:27 +07):** `TELEGRAM_CHAT_ID=804297094` is present in `.env` and confirmed valid via `getChat` API call (`chat_type=private`, `ok=true`); `TELEGRAM_BOT_TOKEN` is present (46 chars). Chat ID was previously recorded as empty in `PROJECT_TASKS.md`/`plans/plan.md` but is actually populated — docs updated below.
- [ ] Doppler CLI/API auth is available and `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are synced without printing values.
- [x] Final handoff includes clean scoped commits and a reviewed disposition for unrelated dirty files.
  - **Reviewed disposition (2026-08-23 16:27 +07):** The 4 dirty files (`grayzone_answers.json`, `hitl_reviews.json`, `hitl_approved.jsonl`, `hitl_approved_with_metadata.jsonl`) contain only `last_updated` / `answered_at` timestamp changes — no content, schema, or answer changes. They are safe to keep dirty until a scoped HITL data commit is made; no quarantine action required.

### 🎫 TICKET-META-009 | `developer` / `qa_tester` | [STATUS: DONE]
**Priority**: MEDIUM
**Depends On**: `CP-03-AZURE`, `CP-04-PW`, `CP-05-RELEASE`
**Blocks**: None; release-gate prerequisites were green before execution.

#### Scope Boundary
- **IN**:
  1. Upgrade Python lockfile dependencies with `uv lock --upgrade` using a workspace-local cache if the default user cache is unavailable.
  2. Upgrade Rust dependencies with `cargo update --manifest-path rust_core/Cargo.toml`.
  3. Review dependency diffs before committing any version movement.
  4. Run focused compatibility checks after upgrade: dependency resolution, Rust tests that cover changed crates, Python import/API smoke checks, and any affected pytest subset.
- **OUT**:
  1. Running broad dependency upgrades while release checkpoints or operator-gated production verification are still active.
  2. Editing `requirements.txt`, `pyproject.toml`, `Cargo.toml`, or lockfiles manually unless a resolver exposes a required compatibility constraint.
  3. Combining dependency upgrade work with deployment, credential, secret, or production Playwright actions.

#### Execution Order
1. Finish or explicitly defer the release-gate blockers first: `CP-03-AZURE`, `CP-04-PW`, then `CP-05-RELEASE`.
2. Create a clean upgrade branch or isolated worktree so existing dirty files and release evidence are not mixed with dependency churn.
3. Run Python and Rust lockfile upgrades separately; record exact commands, resolver output, and changed packages.
4. Validate locally before any push: `python3 scripts/sync_ai_agent_ecosystem.py --check`, targeted pytest, Rust tests, and `git diff --check`.

#### Stop Conditions
- Stop immediately if a resolver wants to change major-version ranges that are not already allowed by `requirements.txt` or `Cargo.toml`.
- Stop if network/cache permissions are unavailable; request explicit approval rather than bypassing the dependency manager.
- Stop if any release checkpoint becomes active again; dependency upgrade remains lower priority than production recovery.

#### Acceptance Criteria
- [x] Python dependency lockfile upgraded by `env UV_CACHE_DIR=/private/tmp/horo-uv-cache uv lock --upgrade`; reviewed diff updates `idna` 3.18→3.19, `timezonefinder` 8.2.5→8.3.0, adds `timezonefinder-data` 1.2026.3, and updates `uvicorn` 0.52.3→0.52.4.
- [x] Rust lockfile upgraded by `cargo update --manifest-path rust_core/Cargo.toml`; reviewed diff updates `h2` 0.4.18→0.4.19 and `syn` 3.0.3→3.0.4.
- [x] Locked resolution passes (`uv lock --check`; `uv sync --locked --dry-run`). Focused Python compatibility suite passes `19 passed`; Rust `cargo test --locked` passes `40 passed, 7 ignored`.
- [x] `git diff --check` passes; only `uv.lock` and `rust_core/Cargo.lock` changed for this ticket. Existing visual-integrity dirty files were preserved.

#### Final evidence
- Resolver previews showed no major-version movement or manifest edits.
- No deployment, credential, secret, or production Playwright action was performed.

### 🎫 TICKET-META-002 | `domain_master` / `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-004`, `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-003 | `developer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-004 | `developer` / `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`, `TICKET-META-002`
**Blocks**: `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-005 | `devops` / `developer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`, `TICKET-META-003`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Reconcile every active or future section of `plan.md` with implementation or a child ticket. Cover hybrid provider failover, Grafana/observability, CI/CD, multi-cloud deployment, skill and agent synchronization, release safeguards, caching/rate limits/security, and future model circuit-breaking architecture. Do not reopen historical `DONE` phases without contrary evidence.

#### Current Blocker
- None. Azure workflow, Hugging Face canonical backend, and multi-cloud configurations are fully cleared and passing.

#### Acceptance Criteria
- [x] Each active/future plan section has an owner, ticket, dependency, and measurable gate.
- [x] Provider, observability, CI/CD, security, and agent-sync checks pass for the implemented scope.
  - **Current status (DONE):** Agent sync passes (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`), provider/observability/CI/security convergence verified, multi-cloud gates clear.
  - **Gate Ref:** `G-META-005-SECURE`.
- [x] Rollback and release evidence is recorded before production claims.

### 🎫 TICKET-META-006 | `qa_tester` / `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-002`..`005`
**Blocks**: None

#### Detailed Instructions
Run the required unit, integration, UI/E2E, security, agent synchronization, pre-deployment, and documentation audits. Reconcile all four source plans against actual implementation evidence, update ticket statuses, and record the final handoff without marking incomplete work as done.

#### Current Verification Evidence
- [x] Deterministic and integration QA: `621 passed` (fresh reviewer summary at 2026-08-21 15:43:59) including engines, routing, ingestion, MCP, observability, and regression scopes.
- [x] Button and endpoint contract regression: `25/25 PASSED`.
- [x] Full local QA: current local `code_reviewer --review --use-python` run records `621 passed`, `8 skipped`, `12 warnings` and marks `overall_status: READY_FOR_PROD`.
- [x] Fresh full local pytest revalidation on 2026-08-21 records `582 passed`, `8 skipped`, and `12 warnings`; no local test failures remain.
  - **Current status:** Network-dependent and socket-dependent cases are guarded (`RUN_REMOTE_INTEGRATION`, local bind skip), so remaining failures are reduced to external-environment gate execution requirements, not local-suite determinism.
  - **Gate Ref:** `G-META-006-FULLQA`.
- [x] Browser readiness regression: `15/15 PASSED` with service-worker isolation; no product fallback is permitted.
- [x] Secret scan: `0` leaks across `1,507` files (fresh reviewer run at 2026-08-21 15:43:59).
- [x] Hugging Face static payload dry-run: `21` files, `3.75 MB`, authenticated payload audit passed.
- [x] Authorized push: remote `origin/main` advanced to `bbc5bc2`; Vercel production deployment `dpl_BpRzm5avDj4KudRYQMpxDYCMD1Zv` is READY.
- [x] HF static production workflow `32016627926` completed successfully; static payload is published for `bbc5bc2`.
- [x] Vercel API probe executed; in this run production curl checks are `2/3` with `POST /api/v1/bazi/interpret` returning `503` (`canonical_bazi_unavailable`) and missing `X-AI-Source`/`X-AI-Model` headers.
- [x] Local release-verifier routing and synthetic-monitor fallback are covered by focused regression tests: an explicit backend URL takes precedence, a canonical HF Space ID derives the backend URL when unset, and static `/index.html` fallback no longer crashes the monitor.
- [x] 2026-08-21 15:43 local revalidation: code review passed with notebook audit clean; secret scan found `0` leaks across `1,507` files, and the UI contract suite passed `25/25` checks.
- [x] Historical HF Docker deployment evidence exists for workflow `32577425927` / commit `52149b7`.
- **AUTHORITATIVE CURRENT STATUS (`CP-02-HF`):** `project/tests/hf_canonical_reprobe_2026-08-24.json` and `project/tests/vercel_reprobe_2026-08-24.json` are **3/3 GREEN** (static UI 200, backend `/health` 200, deterministic API 200). `CP-02-HF` is **PASS**.
  - **Gate Ref:** `G-META-006-BACKEND` / `CP-02-HF`.
- `CP-03-AZURE`: replace GitHub Azure credentials with complete non-secret field configuration, rerun the workflow, and verify provisioning plus `/health`.
  - **Current status:** **RESOLVED / PASS** — GitHub Actions run `32630424001` (2026-08-23 16:20 +07, commit `6c8ee89`) completed with `success`: build/push Docker, Azure login + preflight + deploy to Southeast Asia, ingress config, health verification, and Hermes headless post-deploy E2E all passed. RBAC remediation is effective in Actions runner context.
  - **Gate Ref:** `G-META-005-AZURE`.
- **Historical evidence (superseded):** `production-verification.json` reported `3/3` and `synthetic-health.json` reported `2/2` for an earlier deployment.
- [x] Release CI confirmation for the previously reported Rust formatting drift and Bandit B602 findings.
  - **Current status:** GitHub Actions `Unified CI & Quality Audit Pipeline` run `32571990179` for `056b1aa` completed successfully. Local Rust formatting, Rust vector/security tests, MLOps Python compilation, and CI Bandit command pass with no issues.
  - **Gate Ref:** `G-META-005-RUSTCI`.
- [x] Rust/Python full-review wrapper completion: wrapper command path confirmed; accepted commands are `--review --use-python` and `--review`.
  - **Current status:** `python3 project/core/code_reviewer.py --review --use-python` and `python3 project/core/code_reviewer.py --review` execute deterministically with `READY_FOR_PROD`.
  - **Gate Ref:** `G-META-006-WRAPPER`.
- [x] Live production smoke Playwright E2E: `TICKET-QA-PW-SMOKE-20260825` completed against the Vercel fallback at 2026-08-25 05:17:45 UTC with **13/13 expected smoke controls passed** and 0 failed. The smoke scope excludes the nine full-profile discipline checks; full-profile coverage remains separately unfinished. `CP-04-PW` is **DONE** for smoke scope.
  - **Gate Ref:** `G-META-006-PW`.

#### Acceptance Criteria
- [x] Required pytest, UI regression, E2E, secret scan, and code-review gates pass.
  - **Current status (PASS):** Local QA 100%, 0 leaks, HF canonical 3/3, Vercel 3/3, Azure green, Playwright verified. Consolidated release matrix is PASS (`CP-05-RELEASE`).
  - **Gate Ref:** `G-META-001-CORE`.
- [x] Agent definitions are synchronized with zero drift.
  - **Current status:** Sync checks passing (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`, `python3 scripts/sync_ai_agent_ecosystem.py --check`).
  - **Gate Ref:** `G-META-001-SYNC`.
- [x] All child tickets have evidence-backed `DONE` status.
  - **Current status:** `TICKET-META-001` through `TICKET-META-008` are `DONE`.
  - **Gate Ref:** `G-META-001-SYNC`.
- [x] Parent ticket is moved to `DONE` only after the complete audit passes.
  - **Current status:** Complete multi-cloud audit passed; `CP-06-HANDOFF` is `READY`.
  - **Gate Ref:** `G-META-001-SYNC`.

### Unresolved Gate Recovery Actions (mapped to checkpoints)
- `CP-01-LOCAL` baseline is currently available from the latest evidence snapshot; rerun it only after release-affecting changes.
- Local checks completed in this workspace:
  - `cargo fmt --manifest-path rust_core/Cargo.toml --all` completed successfully.
  - `cd rust_core && cargo fmt --all -- --check` completed successfully.
  - Local `project/mlops` scan shows no `shell=True` / `os.system` subprocess anti-patterns tied to Bandit B602 in a literal string search.
- Exact CI Bandit command passes locally; retain CI run evidence under `CP-01-LOCAL`/`G-META-005-RUSTCI`.
- `CP-02-HF`: canonical artifact `project/tests/backend-release-check-hf-canonical-2026-08-23-latest.json` (2026-08-23 11:12 +07) is 3/3 GREEN, but fresh 5-sample multi-probe at 16:48 +07 shows HF **static UI (`static.hf.space`) consistently 404** while Docker backend `/health` and deterministic API remain stable 200. Vercel fallback is stable 3/3 GREEN. **Downgraded from PASS to FLAPPING** — backend healthy, static CDN path unstable. **Next action:** characterize flap window + operator decision (Vercel primary vs HF static repair); attach `project/tests/hf_static_ui_flap_characterization_2026-08-23.json`.
- `CP-03-AZURE`: replace GitHub Azure credentials with complete non-secret field configuration, rerun the workflow, and verify provisioning plus `/health`.
- `CP-04-PW`: `TICKET-QA-PW-SMOKE-20260825` is **DONE**. Playwright `chromium` ran the bounded smoke profile against the Vercel fallback (`horo-consultant-psi.vercel.app`) at 2026-08-25 05:17:45 UTC with **13/13 expected controls passed** and 0 failed; `project/tests/prod_button_regression_report.json` is the artifact. The smoke profile intentionally excludes nine discipline checks. **Separate unfinished gate:** obtain authorization and run the full profile (22 controls), then archive and assess that evidence independently.
- `CP-05-RELEASE`: run only after CP-01 through CP-04 have current evidence.
- `CP-06-HANDOFF`: synchronize docs and transition tickets only after the consolidated matrix is green.

#### Unresolved Gate Ownership & Validation
| Gate ID | Gate | Owner | Action/Validation target |
|---|---|---|---|
| `G-META-006-BACKEND` | `HF_BACKEND_SPACE_ID` + Docker/HF backend deployment smoke checks | `devops` | Explicitly approve and publish the 69.78 MB Docker payload to `pphothidaen/horoconsultant-core-backend`, then verify canonical HF `/health` and API availability. |
| `G-META-005-AZURE` | `AZURE RBAC` remediation (`Azure Container Apps — Production Deployment`) | `devops` | RBAC is granted and local Resource Group read preflight passes; fix GitHub Azure credential secrets, rerun `Azure Container Apps — Production Deployment`, and confirm both login and provisioning stages pass. |
| `G-META-005-RUSTCI` | Rust formatter + Bandit `B602` remediation (`project/mlops`) | `developer`, `code_reviewer` | Apply formatter/bandit fixes and rerun release CI to clear the red security/format gate. |
| `G-META-006-WRAPPER` | Full-review wrapper convergence | `code_reviewer` | Confirm the wrapper target command, run `python3 project/core/code_reviewer.py --review --use-python`, and confirm deterministic completion. |
||| `G-META-006-PW` | Full-profile production Playwright authorization + run | `qa_tester` | Smoke scope is closed by `TICKET-QA-PW-SMOKE-20260825`: Vercel smoke artifact at 2026-08-25 05:17:45 UTC reports 13/13 expected controls passed. **Unfinished separate gate:** capture authorization, run the 22-control full profile, archive the result, and triage any failures independently. |
| `G-META-006-FULLQA` | Full local QA + canonical-backend unavailable assertions | `qa_tester`, `code_reviewer` | Execute local full QA suite including BaZi 503-path assertions; record canonical timestamped report. |
| `G-META-005-SECURE` | Provider/observability/CI/security convergence | `devops`, `developer` | Ensure provider/observability and CI/security checks green in consolidated release gate matrix. |
| `G-META-001-CORE` | Core release gates (CI, E2E/UI, secret scan, agent sync) | `devops`, `qa_tester` | Re-run consolidated release gate matrix and verify all required gates are green before release. |
| `G-META-001-SYNC` | Final project/plan/evidence synchronization | `business_analyst`, `orchestrator` | Close remaining evidence links, confirm `PROJECT_TASKS.md` and source plans are aligned, archive final status snapshot. |

#### Required Evidence Matrix (Attach on gate completion)
| Gate ID | Required proof | Suggested artifact location |
|---|---|---|
| `G-META-006-BACKEND` | Verified environment var `HF_BACKEND_SPACE_ID`; deployment run log for Docker + canonical HF runs; endpoint probe logs for `/health` (`200` or explicit dependency-fallback `503`). | CI workflow log + smoke-test output file in release notes. |
| `G-META-005-AZURE` | Azure workflow log proving successful `azure/login` + provisioning stages after RBAC remediation. | GitHub Actions log (workflow `Azure Container Apps — Production Deployment`) archived to handoff note. |
| `G-META-005-RUSTCI` | Rust formatter and bandit reports with zero blocking findings; green release CI after fixes. | Release CI report + `cargo fmt --check` output + `bandit` report (from CI runner if local toolchain lacks Bandit). |
| `G-META-006-WRAPPER` | Wrapper transcript showing no hangs and deterministic completion; stable exit code and pass count. | Wrapper debug log + final stdout/stderr artifact. |
| `G-META-006-PW` | Signed-off authorization evidence and production Playwright run artifact proving browser E2E pass set. | Authorization evidence + Playwright report artifact path. |
| `G-META-006-FULLQA` | Timestamped local QA run with `582` passed, `8` skipped, and network-sensitivity notes for any canonical-bazi API fallback path assertion. | Local QA report snapshot, environment timestamp, and `project/tests/local_release_readiness_2026-08-17.md`. |
| `G-META-005-SECURE` | Consolidated provider/observability/CI/security matrix with all checks green. | Release gate checklist + matrix log. |
| `G-META-001-CORE` | Full consolidated release-matrix evidence with all gates green: CI, E2E/UI, secret scan, pytest, pre-deployment checks. | Release gate matrix snapshot + `PROJECT_TASKS.md` status comment. |
| `G-META-001-SYNC` | Final evidence snapshot including updated `PROJECT_TASKS.md`, links to four source plans, unresolved blockers status, and final archive. | Status archive + evidence bundle index. |

#### Gate Execution Commands (Recommended)
| Gate ID | Recommended command(s) |
|---|---|
| `G-META-006-BACKEND` | `HF_BACKEND_SPACE_ID=... python3 scripts/publish_space_hf.py --space-id \"$HF_BACKEND_SPACE_ID\" --sdk docker`<br/>`HF_BACKEND_URL=https://pphothidaen-horoconsultant-core-backend.hf.space HF_STATIC_CDN_URL=https://pphothidaen-horoconsultant-core-backend.static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check-hf-canonical.json`<br/>`HF_BACKEND_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` |
| `G-META-005-AZURE` | `gh workflow run "Azure Container Apps — Production Deployment" -f force_rebuild=true`<br/>`gh run list --workflow="Azure Container Apps — Production Deployment" --limit=1`<br/>`gh run view <run_id> --log-failed --job <deploy_job_id>` |
| `G-META-005-RUSTCI` | `cd rust_core`<br/>`cargo fmt --all -- --check`<br/>`cargo test --no-default-features --test test_vector_search`<br/>`cd ..`<br/>`bandit -r project/mlops -x project/kaggle_kernel -s B101,B404,B603,B311,B324,B110 -lll` |
| `G-META-006-WRAPPER` | `python3 project/core/code_reviewer.py --review --use-python` |
|| `G-META-006-PW` | `python3 scripts/run_prod_e2e_playwright.py --profile full`<br/>`HORO_PUBLIC_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_prod_e2e_playwright.py --profile smoke`<br/>**Smoke verified 2026-08-25 05:17:45 UTC:** Vercel fallback completed 13/13 expected smoke controls, 0 failed (`TICKET-QA-PW-SMOKE-20260825`). This gate remains for the separately unfinished 22-control full-profile run. |
| `G-META-006-FULLQA` | `python3 -m pytest -q project/tests/` |
| `G-META-005-SECURE` | `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py -q`<br/>`python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py -q`<br/>`python3 scripts/grafana_cloud_exporter.py --check-connection --dry-run` |
| `G-META-001-CORE` | `python3 scripts/run_quality_gate.py`<br/>`python3 project/core/code_reviewer.py --scan-secrets`<br/>`python3 scripts/run_button_regression.py` |
| `G-META-001-SYNC` | `git status --short PROJECT_TASKS.md plans/*.md`<br/>`git diff -- PROJECT_TASKS.md plans/metaphysics_learning_roadmap.md plans/plan.md plans/question_forecast_alignment_spec.md plans/todo_tasks_plan.md` |


## 📣 RELEASE NOTES (historical completion archive)
Full historical completion details are tracked in [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).

## 📋 Release Handoff Checklist
Use [docs/RELEASE_HANDOFF_CHECKLIST.md](docs/RELEASE_HANDOFF_CHECKLIST.md) for the current gate-by-gate closure matrix and remaining operator actions before marking final ticket completion.

---

## 🚀 SPRINT: Horo Architecture v3.0 — Data Contracts & WBS Bootstrap — 2026-08-24
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md` — GRILL REPORT 2026-08-24T18:11:30+07:00)  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Commit**: `7e6cbe7` | **Git Tag**: `v3.0-data-contracts`

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-001` | `agy2` (orchestrator) | สร้าง WBS `TDD-HORO-v3.0/` structure + `01_DATA_CONTRACTS/` เต็ม + `04_TEST_PLANES/` เต็ม + `02/03` placeholder | ✅ DONE | None |
| `TICKET-HORO30-002` | `agy2` (orchestrator) | pytest validation suite (69 tests) + secret scan (0 leaks) | ✅ DONE | TICKET-HORO30-001 |
| `TICKET-HORO30-003` | `agy2` (orchestrator) | sync_ai_agent_ecosystem.py --check PASS + PROJECT_TASKS.md update | ✅ DONE | TICKET-HORO30-002 |
| `TICKET-HORO30-004` | `agy2` (orchestrator) | git commit `7e6cbe7` + tag `v3.0-data-contracts` + prepend GRILL REPORT | ✅ DONE | TICKET-HORO30-003 |

### Sprint Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/proto/astro_kernel_service.proto` | gRPC proto3 — L1 Astro Kernel Service (5 methods, 11 messages, 2 enums) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json` | JSON Schema draft-07 — Common Claim Emission (AtomicClaim, EpistemicTrace, ConfidenceVector, PotentialConflict) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/convention_profile.json` | JSON Schema — Convention Profile (profile_hash, CanonicalBook, CalculationConventions, CrossDomainFirewall) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json` | JSON Schema — Tri-Graph Ontology (G_deriv/G_sem/L_event, EdgeOntologyRegistry, LCIw/RNIw metrics) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf` | EBNF Grammar — Horo Rule DSL (5-stage epistemic chain, 30+ production rules) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/README.md` | Placeholder — Sprint TODO |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/README.md` | Placeholder — Sprint TODO |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json` | 6 JPL DE440 golden test vectors |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_B_tradition_conformance_cases.json` | 7 canonical conformance cases (BaZi/ZiWei/QiMen/DaLiuRen/XuanKong) |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json` | 5 adversarial/inversion attack cases |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_D_empirical_isolation_policy.md` | Observational Data Firewall Policy (Rules D-1 through D-5) |
| `TDD-HORO-v3.0/tests/test_data_contracts.py` | 69 pytest tests — 69/69 PASSED |

### Gate Evidence
- pytest: **69/69 PASSED** in 0.03s
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync**
- Git commit: `7e6cbe7`
- Git tag: `v3.0-data-contracts`

### Next Sprint (Sprint 2 — COMPLETED ✅)
- `TICKET-HORO30-005`: Implement FSM `constraint_state_machine.json` in `02_ENGINE_INTERFACES/` — ✅ DONE
- `TICKET-HORO30-006`: Implement `dynamic_arbitration.json` policies — ✅ DONE
- `TICKET-HORO30-007`: Implement `audit_policy_truth_table.csv` in `02_ENGINE_INTERFACES/matrices/` — ✅ DONE
- `TICKET-HORO30-008`: Implement pytest suite `test_engine_interfaces.py` (22 tests) — ✅ DONE

---

## 🚀 SPRINT 2: Horo Architecture v3.0 — Engine Interfaces — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL 4 TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-005` | `agy2` (orchestrator) | สร้าง FSM `constraint_state_machine.json` (4-Tier: H0, H1, H2, H3, 13 states, 18 transitions) | ✅ DONE | TICKET-HORO30-004 |
| `TICKET-HORO30-006` | `agy2` (orchestrator) | สร้าง `dynamic_arbitration.json` (6 intent matrices, 4 arbitration rules ARB-01..04, HITL escalation) | ✅ DONE | TICKET-HORO30-005 |
| `TICKET-HORO30-007` | `agy2` (orchestrator) | สร้าง `audit_policy_truth_table.csv` (7 deterministic rules, 4 verdicts: PASS, WARN, RECOMPUTE, ESCALATE) | ✅ DONE | TICKET-HORO30-006 |
| `TICKET-HORO30-008` | `agy2` (orchestrator) | สร้าง `test_engine_interfaces.py` (22 tests) + Full Suite (91 tests total, 100% PASS) | ✅ DONE | TICKET-HORO30-007 |

### Sprint 2 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/fsm/constraint_state_machine.json` | 4-Tier Constraint FSM (H0, H1, H2, H3, 13 states, 18 transitions, recovery loops) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/policies/dynamic_arbitration.json` | Dynamic Arbitration Matrix across 6 user intent categories, rules ARB-01..04, HITL criteria |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv` | Deterministic L6 Audit verdict lookup table (7 rules, 4 output verdicts) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/README.md` | Complete architectural documentation for 02_ENGINE_INTERFACES module |
| `TDD-HORO-v3.0/tests/test_engine_interfaces.py` | 22 pytest tests validating FSM, dynamic arbitration, and audit truth table |

### Quality & Safety Gate Evidence
- pytest: **91/91 PASSED** across full `TDD-HORO-v3.0/tests/` suite (0.06s)
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync (Antigravity & Codex 100%)**

### Next Sprint (Sprint 3 — COMPLETED ✅)
- `TICKET-HORO30-009`: Implement Neo4j Cypher schema `semantic_graph_schema.cql` — ✅ DONE
- `TICKET-HORO30-010`: Implement Derivation DAG Merkle provenance spec `derivation_dag_immutability.md` — ✅ DONE
- `TICKET-HORO30-011`: Implement Append-Only Event Ledger streaming spec `event_ledger_stream.md` — ✅ DONE
- `TICKET-HORO30-012`: Implement pytest / schema tests for storage & event sourcing (`test_storage_and_event_sourcing.py`, 14 tests) — ✅ DONE

---

## 🚀 SPRINT 3: Horo Architecture v3.0 — Storage & Event Sourcing — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL 4 TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-009` | `agy2` (orchestrator) | สร้าง Neo4j Cypher schema `semantic_graph_schema.cql` (Constraints, Indexes, Traversal queries) | ✅ DONE | TICKET-HORO30-008 |
| `TICKET-HORO30-010` | `agy2` (orchestrator) | สร้าง Merkle DAG specification `derivation_dag_immutability.md` (Acyclicity, JCS Hash Formula, R0..R4 Tiers) | ✅ DONE | TICKET-HORO30-009 |
| `TICKET-HORO30-011` | `agy2` (orchestrator) | สร้าง Event Ledger stream spec `event_ledger_stream.md` (17 canonical events, Hash chaining, Redis/Kafka) | ✅ DONE | TICKET-HORO30-010 |
| `TICKET-HORO30-012` | `agy2` (orchestrator) | สร้าง `test_storage_and_event_sourcing.py` (14 tests) + Full Suite (105 tests total, 100% PASS) | ✅ DONE | TICKET-HORO30-011 |

### Sprint 3 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql` | Neo4j Cypher constraints, indexes, relationship ontology, and stored traversal/audit queries |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/derivation_dag_immutability.md` | Derivation DAG Merkle hash formula, topological insertion guard, and R0..R4 verification spec |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md` | Append-Only Event Ledger streaming spec, 17 FSM event types, hash chaining recurrence & replay |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/README.md` | Complete architectural documentation for 03_STORAGE_AND_EVENT_SOURCING module |
| `TDD-HORO-v3.0/tests/test_storage_and_event_sourcing.py` | 14 pytest tests validating Cypher schema, Merkle DAG algorithms, and Event Ledger chaining |

### Quality & Safety Gate Evidence
- pytest: **105/105 PASSED** across full `TDD-HORO-v3.0/tests/` suite (0.07s)
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync (Antigravity & Codex 100%)**

### Next Phase: Production Agent Prompts & Runtime Adapters (Sprint 4 — COMPLETED ✅)
- `TICKET-HORO30-013`: Implement specialized prompt templates for 10 tradition domain nodes (L3/L4) — ✅ DONE
- `TICKET-HORO30-014`: Implement Consensus Engine (L5), Audit Node (L6), and Plan Composer (L7) runtime wrappers — ✅ DONE
- `TICKET-HORO30-015`: Integrate Test Plane validation suite into CI/CD regression pipeline (`test_test_planes_execution.py`) — ✅ DONE

---

## 🚀 SPRINT 4: Horo Architecture v3.0 — Agent Prompts, Runtimes & Test Planes — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-013` | `agy2` (orchestrator) | สร้าง 10 Production Prompt Templates (L3/L4: BaZi, ZiWei, FengShui, BuShi, QiMen, DaLiuRen, TaiYi, QiZheng, MianXiang, ZeJi) | ✅ DONE | TICKET-HORO30-012 |
| `TICKET-HORO30-014` | `agy2` (orchestrator) | สร้าง L3–L7 Runtime Adapters (`ClaimValidator`, `ConsensusEngine`, `AuditNode`, `PlanComposer`) | ✅ DONE | TICKET-HORO30-013 |
| `TICKET-HORO30-015` | `agy2` (orchestrator) | สร้าง `test_agent_prompts_and_runtimes.py` (28 tests) + `test_test_planes_execution.py` (7 tests) + Full Suite (**140 tests total, 100% PASS**) | ✅ DONE | TICKET-HORO30-014 |

### Sprint 4 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/prompts/*.json` | 10 specialized agent prompt templates enforcing domain firewalls, 5-stage epistemic chains, and Claim Emission schema |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/claim_validator.py` | L3/L4 Claim Validator runtime enforcing schema conformance and domain firewall checks |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/consensus_engine.py` | L5 Consensus Engine runtime executing dynamic arbitration (ARB-01..03) and Tier H2 veto filtering |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/audit_node.py` | L6 Audit Node runtime computing LCIw/RNIw, echo chamber detection, and truth table verdict lookup |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/plan_composer.py` | L7 Plan Composer synthesizing user reports and enforcing mandatory Epistemic Disclaimer verbatim |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/README.md` | Architecture documentation for prompts and runtime adapters |
| `TDD-HORO-v3.0/tests/test_agent_prompts_and_runtimes.py` | 28 pytest tests validating all 10 prompt templates and L3–L7 runtime engines |
| `TDD-HORO-v3.0/tests/test_test_planes_execution.py` | 7 pytest tests executing validation across Test Planes A, B, C (Adversarial attacks), and D |

### Master Verification & Quality Gate Evidence
- 🧪 **Full Pytest Suite**: **140/140 PASSED** in 0.09s across all 5 test files
- 🔐 **Secret Scan**: **0 leaks** (1,694 files scanned via Rust Rayon)
- 🔄 **AI Agent Ecosystem Sync**: **[OK] All sync (Antigravity & Codex 100%)**
- 🏛️ **Architecture Compliance**: Horo Architecture v3.0 Frozen Baseline 100% Bootstrap Complete

---

## 🤖 Multi-Agent Execution & Delegation Evidence (2026-08-24)
- **`codex2` (Account 2, OpenAI Plus, `gpt-5.6-luna`)**:
  - **Task D1 (Telegram Dirty Files)**: 11 unit tests passed (`test_telegram_bot.py`), scoped commit created (`2638d84`).
  - **Task D2 (Quality Gate & Security Scan)**: 1,694 files scanned (0 leaks), 4-stage strict quality gate 100% passed, ecosystem sync passed.
  - **Task D3 (Playwright Smoke Verification)**: Location search verified passing (`BTN-PROD-01` PASSED), triage report generated in `project/tests/prod_button_regression_report.json`.
  - **Quota Offloading**: 96,313 tokens offloaded to OpenAI Plus account (`task-284` + `task-323`).

- **`agy1` (Account 1, Gemini 3.7 Flash Low — Replaced `codex1` for Lane 2)**:
  - **Task Q2 (Live Canonical Health Probes)**:
    - Vercel: 3/3 checks PASSED (Static UI 200, Docker Backend 200, Deterministic API 200) $\rightarrow$ `project/tests/vercel_reprobe_2026-08-24.json`
    - HF Canonical: 3/3 checks PASSED (Static UI 200, Docker Backend 200, Deterministic API 200) $\rightarrow$ `project/tests/hf_canonical_reprobe_2026-08-24.json`
  - **Task Q3 (Doppler Dry-Run)**: 50+ production secrets validated & categorized.
  - **Task Q4 (Ecosystem Check)**: 100% synchronized across all platform definitions.
  - **Quota Efficiency**: Executed via high-efficiency Gemini Flash Low model, saving Claude/GPT quotas.

- **`codex1` (Account 1, OpenAI Pro Lite `longteskondu45@gmail.com`, 93% Quota)**:
  - **Task Q-V3-01 (Full Cross-Suite Regression & Security Audit)**:
    - `TDD-HORO-v3.0/tests/`: 140/140 PASSED (100%)
    - `Secret Scan`: 0 leaks found across 1,696 files (Rust Rayon)
    - `UI & API Button Regression`: 33/33 PASSED (100%)
    - `Ecosystem Sync`: 100% synchronized
  - **Quota Offloading**: 25,850 tokens offloaded to OpenAI Pro Lite account.

---

## 🚀 PHASE 2: Core Deterministic Engine Adapter (2026-08-24)
**Lead Developer**: `codex2` (OpenAI Plus, `gpt-5.6-luna`)  
**Lead QA Auditor**: `codex1` (OpenAI Pro Lite, `gpt-5.6-luna`)  
**Status**: ✅ COMPLETED (Commit: `2ce8a43`)

| Ticket ID | Assigned Agent | Task Summary | Status |
|---|---|---|---|
| `TICKET-HORO30-016` | `codex2` (Developer) | สร้าง `project/core/v3_engine_adapter.py` (BaZi, ZiWei, QiMen, ZeJi adapters $\rightarrow$ `claim_emission_v3.0.json`) + `project/tests/test_v3_engine_adapter.py` (9 tests, 100% PASS) | ✅ DONE |
| `TICKET-HORO30-017` | `codex1` (QA) | Full Cross-Suite Regression & 33 UI/API Button Contracts Verification (100% PASS) | ✅ DONE |
| `TICKET-HORO30-018` | `codex2` (Dev) / `codex1` (QA) | สร้าง `project/routers/v3.py` (POST /calculate, GET /health, GET /schema, POST /audit) + `project/tests/test_v3_router.py` (13 tests total, 100% PASS, Commit: `06d787b`) | ✅ DONE |
| `TICKET-HORO30-019` | `codex1` (High Thinking) | เพิ่มเติม Domain Adapters ครบ 10 สำนักวิชา (XuanKong, DaLiuRen, LiuYao, TaiYi, QiZheng, MianXiang) + 10-engine pipeline router + 25 contract tests (Commit: `5339e1a`) | ✅ DONE |
| `TICKET-HORO30-020` | `codex1` (High Thinking) | พัฒนา `rust_core/src/v3_merkle_dag.rs` (SHA-256 Merkle Hashing & BFS Acyclicity Cycle Guard, `cargo test` 40/40 tests PASS, Commit: `3eb0add`) | ✅ DONE |
| `TICKET-HORO30-021` | `agy1` (UX/UI Design) | พัฒนา `project/static/v3_tokens.css` (Five Elements Semantic Color System, WCAG 2.1 AA Compliant Dark/Light Themes, Claim Card components, Commit: `3eb0add`) | ✅ DONE |
| `TICKET-HORO30-023` | `agy1` (UI Frontend) | พัฒนา `renderHoroV3Results()` ใน `project/static/app.js` & `public/app.js` แสดงผล 10 Claim Cards และ Epistemic Disclaimer Banner (Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-024` | `codex1` (High Thinking) | พัฒนา PyO3 Bindings (`compute_merkle_node_hash_py`, `check_reachability_py`) ใน `rust_core/src/lib.rs` & `v3_engine_adapter.py` (24 tests PASS, Commit: `9e87014`) | ✅ DONE |
| `TICKET-HORO30-025` | `codex1` (High Thinking) | พัฒนา `project/tests/test_v3_prompt_benchmarks.py` ตรวจสอบ Golden Prompts 10 สำนักวิชา & Domain Firewalls (4 tests PASS, Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-026` | `codex2` (Dev) | พัฒนา Prometheus Metrics สำหรับ Horo v3.0 ใน `project/core/observability.py` & `test_v3_observability.py` (3 tests PASS, Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-027` | `codex1` (High Thinking) | พัฒนา `scripts/run_v3_e2e_consultation.py` & `test_v3_e2e_consultation.py` รัน 5 Synthetic Consultation Profiles (5/5 PASS, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-028` | `agy1` (Docs) | พัฒนา `docs/v3_api_specification.md` (Full OpenAPI & Epistemic Derivation Specification, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-029` | `codex2` (Dev) | พัฒนา `scripts/v3_diagnostic_cli.py` & `test_v3_diagnostic_cli.py` (Interactive Terminal CLI with Tri-Graph Output, 3 tests PASS, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-030` | `codex1` (High Thinking) / `codex2` (DevOps) | แก้ไข Docker build contexts (`Dockerfile.hf`, `Dockerfile`), เพิ่ม `TDD-HORO-v3.0` ใน `publish_space_hf.py` และ dynamic runtime discovery ใน `v3.py` ป้องกัน `RUNTIME_ERROR` บน Hugging Face Space (Commit: `e52bafd`) | ✅ DONE |

---

## 💎 Cumulative Multi-Agent Token Savings Matrix
- **`codex1` (OpenAI Pro Lite, `gpt-5.6-luna` — High Thinking Priority)**: **375,381 tokens** offloaded across QA Verification, 10 Domain Adapters, Rust Merkle DAG, PyO3 Bindings, Prompt Benchmarks, E2E Consultation, and HF Docker Build Remediation (`task-667`).
- **`codex2` (OpenAI Plus, `gpt-5.6-luna` — Heavy Implementation)**: **291,356 tokens** offloaded across Tasks D1..D3, Engine Adapters, v3 Router, Observability Metrics, Diagnostic CLI, and Channel Auditing (`task-671`).
- **`agy1` (Antigravity Account 1, `Gemini 3.7 Flash Low`)**: 100% of Documentation Sync, Doppler Dry-run, Live Health Probes, Web Color Tokens, Frontend UI Visualizer, and Technical API Specs.
- **`agy2` (Orchestrator Session)**: **Zero heavy code-writing overhead**, pure orchestration & review mode.
- **Total Multi-Agent Tokens Offloaded**: **666,737+ tokens** (100% Zero-cost to this Antigravity session).

---

## 🚀 SPRINT: Production UI Visual Integrity — Horo v3.0 Consensus Engine — 2026-08-24
**Grill Gate Status**: ✅ APPROVED (Ref: `plans/plan.md`)
**Sprint Tracking Lead**: root orchestrator
**External Gate**: Production deployment is not authorized in this sprint; local fixes and read-only Production verification only.

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-V3UI-001` | `orchestrator` | Baseline Production inspection, acceptance matrix, screenshot/version evidence | DONE | None |
| `TICKET-V3UI-002` | `ux_ui_designer` | WCAG/color/typography/spacing and hierarchy audit | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-003` | `developer` | Implement isolated v3 responsive/layout/contrast remediation | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-004` | `ui_visual_tester` | Add selected-v3 scenario, contrast/overflow/collision checks, and five-viewport captures | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-005` | `qa_tester` / `orchestrator` | Run targeted/full regression, compare before/after, and triage console/network failures | DONE | `TICKET-V3UI-003`, `TICKET-V3UI-004` |
| `TICKET-V3UI-006` | `orchestrator` / `code_reviewer` | Historical `6c351ba` release baseline: lesson learned, sync docs, and safety review | DONE — HISTORICAL BASELINE ONLY | `TICKET-V3UI-005` |
| `TICKET-V3UI-007` | `orchestrator` / `business_analyst` / `devops` / `qa_tester` / `code_reviewer` | Release the current `c9f9161` candidate through user-authorized `release_source_commit` provenance, fail-closed local, evidence, HITL, publish, and post-deploy gates | DOING — BLOCKED ON GATES / HITL | `TICKET-V3UI-006` |

### TICKET-V3UI-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: browser evidence, `plans/plan.md`, `PROJECT_TASKS.md`, `.agents/LESSONS_LEARNED.md`
**Definition of Done**: v3 tab selected in Production; reference and live evidence captured; exact viewport/contrast/collision acceptance criteria recorded; release/version drift documented.

### TICKET-V3UI-002 | `ux_ui_designer` | [STATUS: DONE]
**Priority**: HIGH
**Ownership**: read-only review of Production evidence, `project/static/v3_tokens.css`, v3 markup in `project/static/app.js`
**Boundaries**: no file edits; no deployment; no calculation/copy changes.
**Definition of Done**: concise defect list with severity, offending selector/token, measured or reproducible evidence, and implementation-ready remediation covering light/dark, color-blind, and long multilingual content.

### TICKET-V3UI-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: `project/static/v3_tokens.css` and only the v3 presentation block of `project/static/app.js` if CSS alone is insufficient
**Boundaries**: do not edit audit scripts/tests/docs, backend routes, computation logic, public payloads, or deploy files.
**Definition of Done**: targeted patch removes identified overflow/clipping/collision/contrast risks at all five viewports; inline styles are minimized only where required; targeted frontend tests pass.

### TICKET-V3UI-004 | `ui_visual_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: `scripts/run_visual_layout_audit.py`, `project/tests/test_visual_layout_audit.py`, generated `project/tests/screenshots/visual_audit/**`, and `project/tests/artifacts/visual_layout_report.json`
**Boundaries**: do not edit production frontend source or governance docs; do not publish/deploy.
**Definition of Done**: selected-v3 populated scenario is deterministic; five canonical viewports captured; horizontal overflow, unintended overlap, clipping, and WCAG contrast results are present in JSON; targeted audit tests pass.

**Evidence**: deployed remote `v3-consensus` scenario ran at five canonical viewports; exact tab selected, 10 populated claims each, HTTP 200, `LAYOUT_PASS`, zero overflow/overlap/out-of-bounds/clipping/contrast failures. The current `visual_layout_report.json` is `PASSED` 5/5. Its 30 automated gradient indeterminates were closed by the documented manual screenshot review; unresolved indeterminates block release under Rule 16.

### TICKET-V3UI-005 | `qa_tester` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: read-only verification and generated test reports
**Definition of Done**: targeted tests, button regression, visual suite, console-error audit, `git diff --check`, and full pytest proportional to change pass; failures include concise selector/file/error evidence.

**Evidence**: visual-audit and mirrored-asset tests 13/13 passed; governance/frontend regression tests 26 passed and 5 skipped; button regression passed all controls; JavaScript syntax, `git diff --check`, fixture cleanliness, and ecosystem sync passed. Full pytest passes `792 passed, 9 skipped, 12 warnings`; code reviewer returns `READY_FOR_PROD`, with secret/Kaggle/notebook audits passed and `0` leaks. Post-deploy visual QA is 5/5 exact-tab PASS with zero layout failures.

**Telegram QA remediation**: `TelegramBotController` now resolves the default `TELEGRAM_CHAT_ID` at request time while preserving explicit constructor overrides. The notifier unit contract clears external credentials before asserting formatting, preventing real DNS/network calls. Focused Telegram/config/security tests pass `16 passed` and the prior three full-suite failures are closed.

### TICKET-V3UI-006 | `orchestrator` / `code_reviewer` | [STATUS: DONE — HISTORICAL BASELINE ONLY]
**Priority**: HIGH
**Ownership**: lesson/task/plan evidence and read-only safety review
**Definition of Done**: historical 5-Whys/root cause, prevention protocol, regression guard, artifact links, residual risks, deployed `6c351ba` SHA/HITL action, and `python3 scripts/sync_ai_agent_ecosystem.py --check` result are recorded. It is not evidence for a later candidate.

**Historical evidence only**: secret scan passed with 0 leaks; comprehensive review passed 801 tests with 0 secret/CUDA issues; publisher patch tests 5/5 passed; authorized publish completed with HTTP 200 commits; source version `1.0.0.6c351ba`, HF revision `f8aaa24ed36248c957ff35b405c3056626b28fc7`, runtime `RUNNING`. Its report, screenshot hashes, and manual review are bound to that release. Any changed source version, regenerated report, screenshot, or different HF revision requires `TICKET-V3UI-007` to repeat the applicable gates and obtain a new sign-off.

### TICKET-V3UI-007 | Current `c9f9161` HF Static Release | [STATUS: DOING — BLOCKED ON GATES / HITL]

**Sole authority**: this ticket is the only release checklist for local candidate `1.0.0.c9f9161` / `c9f9161`. Historical `TICKET-V3UI-006`, source `6c351ba`, HF revision `f8aaa24ed36248c957ff35b405c3056626b28fc7`, and their artifacts are baseline context only; none may close a row below.

**Scope**: release-affecting files deliberately selected from the current dirty worktree, including mirrored Static assets and their tests/reports only after ownership review. **Out of scope**: unrelated dirty data/RAG/HITL files, secret access or mutation, infrastructure changes, generated agent definitions, and any unapproved production mutation. **User-authorized identity decision**: immutable `release_source_commit` identifies the deployed payload; the later `packaging_commit` is evidence-only. The packaging commit must not replace the source identity on version surfaces, and no legacy commit/version/metadata fallback or override is permitted.

**Current evidence gate (open)**: `project/tests/artifacts/visual_layout_report.json` was regenerated at `2026-08-25T07:13:49Z` (SHA-256 `807d2609ca53da995bb9c1f89c565a67d867f91855a758dd139470adba9422c0`) and reports 30 gradient indeterminates. The historical post-deploy artifact records a different report hash (`083631501d9129574928fd1af8e386e706f1f20d407068adb5c4a22846bb2f68`) for `6c351ba`; therefore the historical manual review is invalid for this candidate under Rule 16.

**Required release checklist**:

- [ ] Confirm the exact release-file allowlist, exclude unrelated dirty files, and record the intended candidate version plus immutable `release_source_commit` after review.
- [ ] Commit source metadata that names its path, SHA-256 digest, version, immutable `release_source_commit`, and source revision. Do not permit a legacy fallback, environment variable, CLI default, runtime `HEAD`, or external override to replace it.
- [ ] Verify `project/static/**` and `public/**` mirrored release surfaces, including version, HTML, app, and service-worker references, are coherent for the intended commit.
- [ ] Run and archive proportional local QA, publisher regression, visual-audit regression, JavaScript syntax/parity checks, `git diff --check`, secret/safety review, and `python3 scripts/sync_ai_agent_ecosystem.py --check`; stop on the first red result.
- [ ] Capture a fresh five-viewport `v3-consensus` report and the five screenshots, record their SHA-256 values, and bind them to the immutable `release_source_commit` and timestamp.
- [ ] Resolve every automated gradient indeterminate with a new reviewer record per viewport: six findings each (30 total), report/screenshot hashes, reviewer, timestamp, visual basis, and explicit PASS or FAIL. A regenerated artifact invalidates this row.
- [ ] Obtain explicit HITL authorization before staging, selective commit, push, or publish. This ticket does not itself authorize any of those operations.
- [ ] After authorization, selectively stage only the reviewed allowlist, create and record the later `packaging_commit`, then push it; do not include unrelated dirty files. Record both identities in evidence and prove `release_source_commit` is an ancestor of `packaging_commit`.
- [ ] Publish the payload identified by `release_source_commit` to the HF Static Space, run SDK-aware Static health and exact-version verification, and save the resulting target, revision, version, both commit identities, source-metadata path/digest, and asset-parity evidence.
- [ ] Re-capture the five production viewports after publish; verify report/screenshot hashes and all version surfaces correspond exactly once to `release_source_commit`, while the evidence records the later `packaging_commit`; repeat manual gradient sign-off for the post-deploy artifacts.
- [ ] Code reviewer records a fresh fail-closed `READY_FOR_PROD` verdict only after every row above is green; orchestrator then updates the board/plan with the final evidence or records `[ERROR] BLOCKED`.

**Owners and stop conditions**: `qa_tester` owns local regression and captures; `devops` owns payload/health/version/publish evidence after authorization; `code_reviewer` owns safety and the fail-closed verdict; `business_analyst` owns evidence/ticket synchronization; `orchestrator` owns allowlist, dispatch, HITL request, and final decision. Stop and return the first failing gate to its owner. After three failed remediation cycles or any missing authorization, return `NEEDS_HITL`; never infer a pass from the historical baseline.

### Sprint Evidence & Release Decision

- Production baseline: `project/tests/artifacts/production_v3_visual_baseline_2026-08-24.json` and five selected-tab screenshots under `project/tests/screenshots/visual_audit/production_baseline/`.
- Local post-fix evidence: `project/tests/artifacts/v3_visual_post_fix_evidence_2026-08-24.json` and final compact-mobile PASS/TENSION screenshots under `project/tests/screenshots/visual_audit/post_fix/`.
- Confirmed Production risks: fourth tab/descendant clipping on compact mobile, v3-only dark-mode island, sub-AA semantic colors, fixed-height long-content clipping, UI/backend version-label drift, and stale `/index.html` PWA references.
- Release decision: **READY_FOR_PROD**. Authorized deployment and post-deploy verification are complete. The documented final manual screenshot review resolves the 30 automated gradient indeterminates for this release; an indeterminate without equivalent named reviewer sign-off is a blocking risk. The expected static simulation API 404 remains a documented non-blocking Static-SDK behavior.

### Historical Post-Deploy Update — `6c351ba` — 2026-08-25

- Release authorization received and static HF Space published successfully.
- Evidence: `project/tests/artifacts/hf_post_deploy_v3_verification_2026-08-25.json`.
- Remote asset parity: app.js, v3_tokens.css, and sw.js all match local SHA-256 values; version.json reports `1.0.0.6c351ba`.
- Release tooling is now SDK-aware: Static health checks `/` plus production `version.json`; Docker alone checks `/health`.
- Post-redeploy version coherence is PASS: `CURRENT_PAGE_VERSION`, footer, `CLIENT_APP_VERSION`, service-worker cache, and cache-busting query strings all use `1.0.0.6c351ba` / `6c351ba`; no `e432e0d` or composite labels remain.
- Fail-closed release verification requires exactly one matching value/reference on every version surface and rejects missing assets, malformed metadata, network errors, duplicate declarations, stale/composite labels, Docker version mismatches, and CLI mismatches. Publisher suite: `16 passed`; combined publisher and visual-audit regression: `24 passed`.
- Live post-hardening checks: Static health `HEALTHY`; exact version verification `PASSED` for `1.0.0.6c351ba` / `6c351ba`.
- **Historical release state: `6c351ba` was DEPLOYED — READY_FOR_PROD. This does not authorize or verify `TICKET-V3UI-007`.**

### TICKET-HFSTATIC-GOV-001 | Mandatory Release Verification Governance | [STATUS: DONE]

**Priority**: CRITICAL
**Rule / skill**: `.agents/rules/16-hf-static-release-verification.md` and `.agents/skills/hf-static-release-verification/SKILL.md`
**Scope**: make HF Static health, exact-version, publisher regression, visual regression, safety review, and ecosystem synchronization mandatory and fail-closed. No deployment is performed by this governance ticket.

| Work item | Responsible sub-agent | Acceptance evidence | Status |
|---|---|---|---|
| Publisher verifier implementation and regression coverage | `developer` | `python3 -m pytest -q tests/test_publish_space_hf.py` → `16 passed` | DONE |
| Payload, Static health, exact-version and release evidence | `devops` | Dry-run plus `--sdk static --check-health` and `--sdk static --verify-version` exit `0` | DONE |
| Five-viewport visual capture and report | `ui_visual_tester` | `desktop-4k`, `laptop-standard`, `tablet-portrait`, `mobile-ios`, `mobile-compact`; report `PASSED` 5/5 | DONE |
| Independent focused regression | `qa_tester` | Publisher + visual-audit suite → `24 passed` | DONE |
| Secret/safety verdict | `code_reviewer` | No leaks or unresolved red gate; release evidence reviewed | DONE |
| Rule, skill, ticket, plan, and catalog synchronization | `business_analyst` | Paths documented and `sync_ai_agent_ecosystem.py --check` green | DONE |
| Dispatch, retry/HITL control, final decision | `orchestrator` | No `READY_FOR_PROD` until every row is green | DONE |

**RACI**: `orchestrator` is Accountable; the listed sub-agents are Responsible for their rows; `code_reviewer`, `qa_tester`, and `business_analyst` are Consulted on safety, test, and governance evidence; the owner is Informed and becomes the HITL approver when production mutation or a three-cycle unresolved defect requires authorization.

**Mandatory release sequence**:

```bash
python3 -m pytest -q tests/test_publish_space_hf.py
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --dry-run
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --check-health
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --verify-version
python3 scripts/run_visual_layout_audit.py --url https://pphothidaen-horoconsultant-core-backend.static.hf.space --scenario v3-consensus --no-server
python3 -m pytest -q tests/test_publish_space_hf.py project/tests/test_visual_layout_audit.py
python3 -m pytest -q tests/test_hf_release_governance.py
python3 scripts/sync_ai_agent_ecosystem.py --check
```

**Release gate**: no `READY_FOR_PROD` if any command exits non-zero, any required artifact is missing, any version surface is stale/duplicate/composite, any required asset is unreachable, any viewport fails, or any result remains indeterminate. An indeterminate is resolved only by a named manual reviewer recording the current artifact, timestamp, review basis, and explicit pass/fail sign-off. Route failure to the responsible sub-agent; after three failed remediation cycles, stop and escalate to HITL.

**Historical evidence**: publisher `16 passed`; publisher + visual audit `24 passed`; governance contract suite passed in the implementation session (count may evolve with the contract); Static health and exact version green for `1.0.0.6c351ba` / `6c351ba`; visual report `PASSED` 5/5 with screenshots under `project/tests/screenshots/visual_audit/`; automated gradient indeterminates are closed by the documented final manual screenshot review. It cannot close `TICKET-V3UI-007`.

**Manual reviewer sign-off — 2026-08-25**: `root/orchestrator` and `code_reviewer` reviewed `project/tests/artifacts/visual_layout_report.json` plus the current five `*_horo_v3_consensus.png` screenshots. The rendered gradient status text, claim content, controls, and semantic boundaries are readable at every canonical viewport. Decision: **PASS** for the 30 automated gradient indeterminates in these artifacts only; a new capture invalidates this sign-off and requires review again.

### Planning continuation evidence — 2026-08-24

- `python3 scripts/sync_ai_agent_ecosystem.py --check`: PASS; all required platform, governance, Antigravity, and Codex synchronization checks are green.
- Focused v3 engine/router, visual-audit, rendering, and frontend regression suite: `41 passed`.
- Production-version/PWA/report-export regression suite: `11 passed, 5 skipped`; optional-browser skips are retained as environment limitations.
- `node --check project/static/app.js`, `node --check public/app.js`, and `git diff --check`: PASS.
- Planning disposition: `TICKET-META-009` and local QA `TICKET-V3UI-005` are DONE; `TICKET-V3UI-006` remains PARTIAL only for HITL deployment/post-deploy verification; `CP-06-HANDOFF` remains READY for handoff with the browser rerun limitation recorded.
- Full-suite safety review: `READY_FOR_PROD`; secret scan PASS with `0` leaks. Test-generated fixture mutations were restored before this evidence update.
- Final visual evidence review: the light PASS and explicit-dark TENSION post-fix screenshots were inspected and remain readable across the long populated v3 result surface. The tracked `visual_layout_report.json` remains the honest pre-final `WARNING` artifact; the separate post-fix evidence JSON is the authoritative local measurement record.
- No deployment, publish, credential, or secret mutation was performed; the authorized lockfile changes are limited to `uv.lock` and `rust_core/Cargo.lock` and are documented in the ticket above.

---

## 🚀 SPRINT: Pre-QA Receipt-v2 Lanes, Alias Smoke Dispatch, Formal QA & Push — 2026-08-26
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md` — GRILL REPORT 2026-08-26T02:14:00+07:00)
**Sprint Tracking Lead**: `orchestrator` (Antigravity / Claude Sonnet 4.6 Thinking)

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-ORCH-SPRINT-001` | `developer` | Execute 4 serial pre-QA lanes (validator pkg → parser hardening → v2 adoption → v2 AGY condition) | TODO | None |
| `TICKET-ORCH-SPRINT-002` | `qa_tester` | Combined formal QA — 4-suite pytest exit 0 | TODO | `TICKET-ORCH-SPRINT-001` |
| `TICKET-ORCH-SPRINT-003` | `devops` | `git diff --check`, secret scan, ecosystem `--sync`/`--check`, atomic commit + push | TODO | `TICKET-ORCH-SPRINT-002` |
| `TICKET-ORCH-SPRINT-004` | `orchestrator` | HITL-gated `codex1` alias dispatch (RC2-004/attempt-1); chain to `codex2`/`agy1`/`agy2` only on valid receipt | TODO | `TICKET-ORCH-SPRINT-003` |

---

### 🎫 TICKET-ORCH-SPRINT-001 | `developer` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: M (serial execution of 4 bounded lanes)
**Depends On**: None
**Blocks**: `TICKET-ORCH-SPRINT-002`

#### Lane 1 — Validator Packaging (XS)
- **Owned files**: `pyproject.toml`, `requirements.txt`, `uv.lock`
- **Action**: Declare `jsonschema>=4.23,<5`; regenerate `uv.lock`; no CI workflow, source, schema, or test changes.
- **Acceptance**: `py_compile` on owned files passes; `git diff --name-only HEAD -- pyproject.toml requirements.txt uv.lock` shows only those three files; scoped diff exits 0.

#### Lane 2 — AGY Parser/Evidence Hardening (S)
- **Owned files**: `scripts/multiagent_prompt_command.py` only
- **Action**: Reject duplicate/non-finite JSON; keep failure reasons content-free; redact decoded prompt content; sanitize before finalization/hash/persistence; bind AGY process/session evidence. One sanitized `WorkResult`. No external retry.
- **Acceptance**: `py_compile scripts/multiagent_prompt_command.py` exits 0; scoped diff shows only that file; all lane-2 targeted tests remain green.

#### Lane 3 — Receipt-v2 Policy/Template Adoption (S)
- **Owned files**: `.agents/config/multiagent_model_policy.yaml`, `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`
- **Action**: New governed receipts use canonical v2; v1 remains legacy; `Z` timestamp contract aligned; generated mirrors change only through prescribed sync.
- **Acceptance**: YAML and Markdown parse cleanly; scoped diff shows only those two files; no `.codex/agents/` file hand-edited.

#### Lane 4 — Receipt-v2 AGY Conditional Requirement (XS)
- **Owned files**: `.agents/schemas/multiagent-dispatch-receipt-v2.schema.json` only
- **Action**: Require `process_or_session_id` for `provider: agy`; enforce `Z` timestamp contract; preserve Codex compatibility and receipt-v1.
- **Acceptance**: Schema parses as valid JSON; `jsonschema` Draft 2020-12 metaschema validates; scoped diff shows only that file.

#### Combined Evidence
- All four lanes frozen, `py_compile` per owned file exits 0, scoped diff per lane exits 0, no unowned file changed.

---

### 🎫 TICKET-ORCH-SPRINT-002 | `qa_tester` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: M
**Depends On**: `TICKET-ORCH-SPRINT-001` (all four lanes DONE)
**Blocks**: `TICKET-ORCH-SPRINT-003`

#### Detailed Instructions
1. Run exact combined formal QA command:
   ```bash
   python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py tests/test_multiagent_prompt_command_r4.py
   ```
2. Record: exit code, total passed/failed/skipped counts, wall-clock duration.
3. Confirm: no new test file was modified by the QA runner.
4. Trim output to summary line only before reporting to orchestrator.

#### Acceptance Criteria
- [ ] Exit code `0`.
- [ ] Zero test failures (pre-documented expected legacy assertion deltas are allowed only if explicitly named in lane evidence).
- [ ] Scoped diff over test files exits 0 (no test modification by QA runner).

---

### 🎫 TICKET-ORCH-SPRINT-003 | `devops` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: S
**Depends On**: `TICKET-ORCH-SPRINT-002` (QA DONE)
**Blocks**: `TICKET-ORCH-SPRINT-004`

#### Detailed Instructions
1. **Diff check**: `git diff --check HEAD` — must exit 0.
2. **Secret scan**: `python3 project/core/code_reviewer.py --scan-secrets` — must report 0 leaks.
3. **Ecosystem sync**: `python3 scripts/sync_ai_agent_ecosystem.py --sync` — must exit 0 with `[OK]` for all required checks.
4. **Ecosystem verify**: `python3 scripts/sync_ai_agent_ecosystem.py --check` — must exit 0 with all `[OK]`.
5. **Stage and commit** (excluding `project/api_router.py`, `project/static/version.json`, `project/data/distillation_checklist.json`):
   ```bash
   git add -A
   git reset HEAD project/api_router.py project/static/version.json project/data/distillation_checklist.json
   git commit -m "feat(orchestration): implement pre-QA receipt-v2 lanes, parser hardening, and formal QA verification"
   ```
6. **Push**: `git push origin main` — must complete without error.

#### Acceptance Criteria
- [ ] `git diff --check HEAD` exits 0.
- [ ] Secret scan: 0 leaks.
- [ ] Ecosystem `--sync` + `--check` both exit 0 with all `[OK]`.
- [ ] Commit created with exact message; excluded files not included.
- [ ] `git push origin main` exits 0.
- [ ] `git log --oneline -1` confirms the commit SHA and message.

---

### 🎫 TICKET-ORCH-SPRINT-004 | `orchestrator` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: S
**Depends On**: `TICKET-ORCH-SPRINT-003` (commit + push DONE)
**Blocks**: None (final gate)

#### Detailed Instructions
1. Verify `TICKET-ORCH-SPRINT-003` push evidence is confirmed.
2. Confirm RC2-004 dispatch prerequisites: focused taxonomy QA (from RC2-004 spec) and read-only isolation review are satisfied or explicitly waived with reason.
3. If prerequisites met: authorize `codex1` read-only CLI lane dispatch, recording as `RC2-004/codex1/attempt-1`.
4. Gate decision on `codex1` result:
   - Valid receipt → record metadata (content-free), authorize bounded `codex2` attempt, and proceed per the RC2-004 chain.
   - Invalid contract / `NEEDS_HITL` → fail closed; record as terminal for this session; do NOT dispatch `codex2`/`agy1`/`agy2`.

#### Acceptance Criteria
- [ ] RC2-004 dispatch prerequisites evaluated and decision recorded.
- [ ] `codex1` attempt result recorded as `RC2-004/codex1/attempt-1` (valid receipt OR typed `NEEDS_HITL`).
- [ ] Gate decision documented in `plans/plan.md` and this ticket.
- [ ] No automatic retry or root-session alias invocation.
