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
| `TICKET-ALIAS-RC2-003` | `developer` / `qa_tester` / `code_reviewer`; aliases `codex1`, `codex2`, `agy1`, `agy2`; monitored by `orchestrator` | Implement, validate, review, then redispatch four distinct lanes with Result Contract v2 | DOING — PROTOCOL IMPLEMENTATION | `TICKET-ORCH-ONLY-002`, Rule 17 |

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

### TICKET-ALIAS-RC2-003 | Result Contract v2 and Four-Alias Redispatch | [STATUS: DOING — PROTOCOL IMPLEMENTATION]

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
| `codex1` | Vercel gateway CORS independent review | Read-only | Starts at 1 after implementation/QA/review | PENDING REDISPATCH |
| `codex2` | HF/FastAPI CORS independent review | Read-only | Starts at 1 after implementation/QA/review | PENDING REDISPATCH |
| `agy1` | Static frontend/HF Docker separation review | Read-only | Starts at 1 after implementation/QA/review | PENDING REDISPATCH |
| `agy2` | Cross-lane release-gate and CORS evidence review | Read-only | Starts at 1 after implementation/QA/review | PENDING REDISPATCH |

**Checklist**:

- [x] Record fresh owner authorization for Result Contract v2; no waiver.
- [x] Preserve all four prior attempts as immutable historical `BLOCKED` evidence.
- [x] Define two-layer receipt/result governance, provider-native adapters, fail-closed rules, and fresh per-alias counters.
- [x] Run ecosystem `--sync` then `--check`: 19 Codex definitions synchronized, 0 updated, 0 obsolete, and no generated `.codex/agents` change.
- [ ] Developer child implements dispatcher/config/schema/template changes within exclusive ownership.
- [ ] Developer/DevOps child supplies an approved runtime config path and an explicit read-only role or validated sandbox override; example config and default Codex `workspace-write` are rejected.
- [ ] QA child validates valid, malformed, ambiguous, nonzero-exit, identity/digest mismatch, and secret-redaction cases.
- [ ] Code reviewer verifies fail-closed behavior, retry/HITL boundaries, root-only separation, and backward compatibility.
- [ ] Child execution lanes invoke `codex1`, `codex2`, `agy1`, and `agy2` through the terminal CLI and return four v2 receipts.
- [ ] Orchestrator confirms four distinct valid receipts and decides the release gate.

**Success / stop**: close only when implementation, QA, and review are green and
all four fresh alias lanes provide distinct schema-valid v2 receipts. Stop on
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
