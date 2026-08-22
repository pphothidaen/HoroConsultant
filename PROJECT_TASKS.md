# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last Updated: 2026-08-22 18:56 (Asia/Bangkok) — revalidated quota/account-migration guard, agent ecosystem sync, focused health/router regressions, and secret scan. Parent release gates remain blocked only on documented external Azure, canonical-HF, release-CI, authorized-production-Playwright, and operator credential handoff gates.*

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
- `python3 scripts/agent_quota_status_guard.py --remaining-percent 9 --enforce` → warning emitted for `<10%` quota and confirmed required handoff markers in `PROJECT_TASKS.md` and `plans/plan.md`.
- `python3 project/core/code_reviewer.py --scan-secrets` → PASSED: `0` leaks across `1,530` files (2026-08-22 18:56).

---

## 📊 TASK BOARD (KANBAN)

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
| `TICKET-META-001` | `orchestrator` / `business_analyst` | Consolidate and execute the five-branch metaphysics roadmap, six-domain question/forecast alignment benchmark, and six TODO workstreams | DOING | None |
| `TICKET-META-002` | `domain_master` / `developer` | Implement and test the five-branch deterministic metaphysics calculation modules | DONE | `TICKET-META-001` |
| `TICKET-META-003` | `developer` | Execute OCR/RAG ingestion, dataset generation, fine-tuning, model fusion, MCP, and visualizer integration | DONE | `TICKET-META-001` |
| `TICKET-META-004` | `developer` / `qa_tester` | Implement six-domain question/forecast alignment, focused prompting, debate routing, and validator benchmarks | DONE | `TICKET-META-001` |
| `TICKET-META-005` | `devops` / `developer` | Reconcile active/future `plan.md` platform work: providers, observability, CI/CD, governance, and release architecture | BLOCKED | `TICKET-META-001` |
| `TICKET-META-006` | `qa_tester` / `code_reviewer` / `business_analyst` | Run full QA, security, synchronization, release evidence, and final Kanban documentation handoff | BLOCKED | `TICKET-META-002`..`005` |
| `TICKET-META-007` | `orchestrator` / `business_analyst` | Refresh sub-agent delegation governance and Claude Code three-level command-control examples | DONE | `TICKET-META-001` |
| `TICKET-META-008` | `orchestrator` / `business_analyst` / `devops` | Preserve account-migration continuity and quota-exhaustion handoff, including active blockers, non-secret credential status, and safe resume commands | DOING | `TICKET-META-005`, `TICKET-META-006` |

### 🎫 TICKET-META-001 | `orchestrator` / `business_analyst` | [STATUS: DOING]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: Future implementation, QA, release, and production handoff tickets derived from this scope.

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
- [ ] CI/CD, secret scan, agent synchronization, pre-deployment review, and required E2E/UI regression gates pass before release.
  - **Current status:** Full local QA (`code_reviewer --review --use-python`) is now READY_FOR_PROD, but release closure remains blocked by unresolved external/environmental gates: `HF_BACKEND_SPACE_ID` + HF canonical backend health checks (`G-META-006-BACKEND`), Azure RBAC remediation (`G-META-005-AZURE`), and external Playwright authorization for production E2E (`G-META-006-PW`).
  - **Next action:** Execute the consolidated release gate matrix once external blockers are cleared and attach the all-green evidence bundle.
  - **Gate Ref:** `G-META-001-CORE`.
- [ ] `PROJECT_TASKS.md`, the four source plans, and the final delivery evidence are synchronized with the actual implementation state.
  - **Current status:** Cross-links are in place; final lockstep still waits on unresolved external release gates and environment blockers (live backend deployment + Azure RBAC + production Playwright), not local QA determinism.
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

### 🎫 TICKET-META-008 | `orchestrator` / `business_analyst` / `devops` | [STATUS: DOING]
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
  - `a6467e5` — Telegram notification secret config support.
  - `87ecc84` — Persist Telegram Chat ID from bot/webhook updates.
- Telegram runtime check: bot token is present locally; `TELEGRAM_CHAT_ID` key exists but is still empty in `.env` until a stopped/non-competing bot update is captured or the operator provides the numeric ID.
- GitHub CLI: current `gh auth status` reports account `pphothidaen` token invalid; do not rely on `gh secret set` until re-authenticated.
- Doppler CLI: `doppler me` reports no token in keyring; do not claim Doppler sync completion until `doppler login` or a valid `DOPPLER_TOKEN` is provided.
- Local secret hygiene: expired `GH_TOKEN` was removed from `.env` and `.env.production`; latest secret scan remains `0` leaks across `1,530` files.
- Dirty files outside the Telegram/account-continuity scope remain uncommitted and must be reviewed by batch before quarantine or cleanup.
- Governance enforcement: `scripts/agent_quota_status_guard.py` checks `/status`/runtime quota signals; `.agents/hooks/pre_tool_check.py` and `.claude/hooks/pre_tool_guard.py` invoke it when quota status is present, and `bsa-doc-skill-management` defines the low-quota handoff workflow. Focused guard regression and explicit `--remaining-percent 9 --enforce` validation passed on 2026-08-22.

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
- [ ] GitHub CLI is re-authenticated and Telegram secrets are synced to GitHub Actions without printing values.
- [ ] Doppler CLI/API auth is available and `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are synced without printing values.
- [ ] Final handoff includes clean scoped commits and a reviewed disposition for unrelated dirty files.

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

### 🎫 TICKET-META-005 | `devops` / `developer` | [STATUS: BLOCKED]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`, `TICKET-META-003`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Reconcile every active or future section of `plan.md` with implementation or a child ticket. Cover hybrid provider failover, Grafana/observability, CI/CD, multi-cloud deployment, skill and agent synchronization, release safeguards, caching/rate limits/security, and future model circuit-breaking architecture. Do not reopen historical `DONE` phases without contrary evidence.

#### Current Blocker
- Azure production workflow (`Azure Container Apps — Production Deployment`) is blocked by service-principal RBAC. Latest run logs show:
  - `AuthorizationFailed` for `Microsoft.Resources/subscriptions/resourcegroups/read`
  - `AuthorizationFailed` for `Microsoft.Resources/subscriptions/resourcegroups/write`
  over scope `/subscriptions/0aca09b2-2917-4d8f-aef8-1a4da965d7dc/resourcegroups/gh-action-app-31835489966-22-rg`.
- The workflow now resolves placeholders in `AZURE_CREDENTIALS` and proceeds through `azure/login`; failure occurs during provisioning.

#### Acceptance Criteria
- [x] Each active/future plan section has an owner, ticket, dependency, and measurable gate.
- [ ] Provider, observability, CI/CD, security, and agent-sync checks pass for the implemented scope.
  - **Current status (BLOCKED):** Agent sync passes (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`), but provider/observability/CI/security convergence remains blocked by external deployment/CI issues and local environment constraints captured in the full local QA and code review run.
  - **Next action:** Reconcile remaining provider/observability/CI/security failures once deployment and environment blockers are resolved, then rerun the release gate matrix.
  - **Gate Ref:** `G-META-005-SECURE`.
- [x] Rollback and release evidence is recorded before production claims.

### 🎫 TICKET-META-006 | `qa_tester` / `code_reviewer` / `business_analyst` | [STATUS: BLOCKED]
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
- [ ] Docker backend deployment: static HF publish to `pphothidaen/horoconsultant-core-backend` succeeded on 2026-08-21 17:12 (+07) and stamped `v1.0.0.4b9c373`; canonical HF verification now passes static UI but still fails backend (`project/tests/backend-release-check-hf-canonical.json` is `1/3`: static `200`, `/health` `404`, deterministic API `404`).
- **Current status:** Blocked by missing/unfinished Docker backend publish to the canonical HF Space. The local approval reviewer requires explicit approval for uploading the 69.78 MB backend payload to `pphothidaen/horoconsultant-core-backend` before execution can continue.
  - **Runtime evidence:** HF dry-run authenticated as `pphothidaen`; static publish completed; canonical live verifier wrote `project/tests/backend-release-check-hf-canonical.json` with backend/API `404`.
- **Next action:** Explicitly approve Docker backend upload to `pphothidaen/horoconsultant-core-backend`, publish Docker payload, wait for Space startup, then rerun canonical HF and Vercel checks side-by-side before deciding gate closure.
  - **Gate Ref:** `G-META-006-BACKEND`.
- [ ] Azure canonical backend deployment: workflow `Azure Container Apps — Production Deployment` reaches `azure/login` but fails in `Deploy to Azure Container Apps` with RBAC `AuthorizationFailed` on resource-group read/write.
  - **Current status:** RBAC grant was applied on 2026-08-21 for service principal `2e0f6d36-99da-4c75-a07c-bf6299da2180` / object id `d730cc3c-aa0d-4b01-98db-828ec4a6eeda` as `Contributor` on `rg-horoconsult`; local `az group show` confirms Resource Group read access and `provisioningState: Succeeded`.
  - **Runtime credential evidence:** Operator-provided role assignment output plus local `az group show`; run `32472307078` built/pushed Docker successfully but failed at `Azure Login` because `creds` lacked required service-principal fields; workflow fix `bcac542` was pushed and rerun as `32472681936`, which then failed earlier at `Resolve Azure credentials` with `Missing resolved credential field: clientId`.
  - **Next action:** Replace GitHub `AZURE_CREDENTIALS` with complete service-principal JSON or configure `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`, and `AZURE_TENANT_ID` as Actions secrets, then rerun `Azure Container Apps — Production Deployment` and confirm post-login provisioning plus `/health` pass.
  - **Gate Ref:** `G-META-005-AZURE`.
- [ ] HF Docker canonical backend: workflow `32016627926` now has canonical `HF_BACKEND_SPACE_ID` defaulted in CI; live canonical health evidence still fails (`/health` unavailable, static `404`) and `0/2` in local synthetic checks.
- **Current status:** Static canonical HF is now live; backend is still unavailable until Docker publish is explicitly approved and completed.
  - **Runtime evidence:** `project/tests/backend-release-check-hf-canonical.json` shows static `200`, backend `/health` `404`, deterministic API `404`; Vercel-side check remains split at `2/3` in `project/tests/backend-release-check.json`.
- **Next action:** Publish Docker backend after explicit payload approval, then verify `/health` endpoint availability.
  - **Gate Ref:** `G-META-006-BACKEND`.
- [ ] Release CI remains pending external confirmation for the previously reported Rust formatting drift and Bandit B602 findings.
  - **Current status:** Local Rust formatting, Rust vector/security tests, MLOps Python compilation, and the exact CI Bandit command all pass; Bandit reports no issues across `project/` and `scripts/` (`36,112` lines). A repository-wide search also finds no `shell=` usage. External release CI still needs to reproduce the result.
  - **Next action:** Rerun the release CI workflow and attach its Bandit/Rust artifacts before clearing this external gate.
  - **Gate Ref:** `G-META-005-RUSTCI`.
- [x] Rust/Python full-review wrapper completion: wrapper command path confirmed; accepted commands are `--review --use-python` and `--review`.
  - **Current status:** `python3 project/core/code_reviewer.py --review --use-python` and `python3 project/core/code_reviewer.py --review` both execute successfully and deterministically in this workspace with `READY_FOR_PROD`.
  - **Next action:** Capture this pass in the consolidated `G-META-006-WRAPPER` evidence bundle.
  - **Gate Ref:** `G-META-006-WRAPPER`.
- [ ] Live production Playwright E2E: pending explicit authorization for production execution.
  - **Current status:** Current smoke run reaches target and presets, but returns `503` on `POST /api/v1/bazi/interpret`, then fails UI waits (`#location_search` fill timeout and interpretation-tab click timeout).
  - **Runtime blocker:** Direct socket/DNS checks are failing in this workspace, so Playwright runs hit API fallback and partial UI execution before full auth/authorization checks can complete.
  - **Next action:** Obtain authorization and run the production Playwright E2E from an environment with runnable Playwright browser binaries.
  - **Gate Ref:** `G-META-006-PW`.

#### Acceptance Criteria
- [ ] Required pytest, UI regression, E2E, secret scan, and code-review gates pass.
  - **Current status (BLOCKED):** Local `code_reviewer --review --use-python` passes (`READY_FOR_PROD`), and current unknowns are restricted to external/environmental gate proofs (`HF_BACKEND_SPACE_ID`, Azure RBAC, and external Playwright authorization).
  - **Next action:** Clear all unresolved items in `Current Verification Evidence`, rerun consolidated gate matrix, then flip this acceptance only when every gate is green in one run.
  - **Gate Ref:** `G-META-001-CORE`.
- [x] Agent definitions are synchronized with zero drift.
  - **Current status:** Sync checks are passing in the current workspace run (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`), and drift was confirmed resolved in the latest evidence pass.
  - **Next action:** Re-run both sync checks after every future manifest or agent-role update and attach the output alongside the final lock-step snapshot.
  - **Gate Ref:** `G-META-001-SYNC`.
- [x] All child tickets have evidence-backed `DONE`, `BLOCKED`, or remaining `TODO` status.
  - **Current status:** `TICKET-META-001`..`004` are `DONE`; `TICKET-META-005` and `TICKET-META-006` remain `BLOCKED` while external gate proofs are still pending.
  - **Next action:** Promote these to explicit `DONE` or `BLOCKED` only after each unresolved gate item has closure evidence recorded in one audit run.
  - **Gate Ref:** `G-META-001-SYNC`.
- [ ] Parent ticket is moved to `DONE` only after the complete audit passes.
  - **Current status:** Parent remains `DOING` until unresolved audit and release blockers from `Current Verification Evidence` are cleared.
  - **Next action:** Move to `DONE` only when all unresolved `Current Verification Evidence` items are closed and evidence archive is finalized.
  - **Gate Ref:** `G-META-001-SYNC`.

### Unresolved Gate Recovery Actions
- Local checks completed in this workspace:
  - `cargo fmt --manifest-path rust_core/Cargo.toml --all` completed successfully.
  - `cd rust_core && cargo fmt --all -- --check` completed successfully.
  - Local `project/mlops` scan shows no `shell=True` / `os.system` subprocess anti-patterns tied to Bandit B602 in a literal string search.
- Exact CI Bandit command now passes locally on 2026-08-21; CI runner confirmation is still required for release closure.
- 2026-08-21 blocker investigation: HF canonical probes fail at status `0` (DNS/socket/egress or remote Space availability); Azure login succeeds but target resource-group authorization fails; local CI/Rust/Bandit gates pass; production Playwright still needs authorized browser egress. The Azure workflow now includes a target-access preflight with remediation output.
- Confirm canonical `HF_BACKEND_SPACE_ID` fallback path is active in CI and rerun Docker backend and HF canonical backend deployment checks.
- Repair Azure runtime Azure RBAC by granting the workflow identity `resourceGroups/read` + `resourceGroups/write` (or equivalent) on the target deployment resource group, then rerun Azure promotion workflow.
- Confirm local Rust formatting (`cargo fmt`) is clean, rerun Bandit in an environment where it is installed, then clear both findings in the same release CI run.
- Re-run the Rust/Python full-review wrapper after hang investigation and confirm wrapper convergence.
- Obtain external birth-data execution authorization and rerun production Playwright E2E.

#### Unresolved Gate Ownership & Validation
| Gate ID | Gate | Owner | Action/Validation target |
|---|---|---|---|
| `G-META-006-BACKEND` | `HF_BACKEND_SPACE_ID` + Docker/HF backend deployment smoke checks | `devops` | Explicitly approve and publish the 69.78 MB Docker payload to `pphothidaen/horoconsultant-core-backend`, then verify canonical HF `/health` and API availability. |
| `G-META-005-AZURE` | `AZURE RBAC` remediation (`Azure Container Apps — Production Deployment`) | `devops` | RBAC is granted and local Resource Group read preflight passes; fix GitHub Azure credential secrets, rerun `Azure Container Apps — Production Deployment`, and confirm both login and provisioning stages pass. |
| `G-META-005-RUSTCI` | Rust formatter + Bandit `B602` remediation (`project/mlops`) | `developer`, `code_reviewer` | Apply formatter/bandit fixes and rerun release CI to clear the red security/format gate. |
| `G-META-006-WRAPPER` | Full-review wrapper convergence | `code_reviewer` | Confirm the wrapper target command, run `python3 project/core/code_reviewer.py --review --use-python`, and confirm deterministic completion. |
| `G-META-006-PW` | Production Playwright egress authorization + run | `qa_tester` | Capture permission evidence, rerun production Playwright E2E, and archive run logs/artifacts. |
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
| `G-META-006-PW` | `python3 scripts/run_prod_e2e_playwright.py --profile full`<br/>`HORO_PUBLIC_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_prod_e2e_playwright.py --profile smoke` |
| `G-META-006-FULLQA` | `python3 -m pytest -q project/tests/` |
| `G-META-005-SECURE` | `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py -q`<br/>`python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py -q`<br/>`python3 scripts/grafana_cloud_exporter.py --check-connection --dry-run` |
| `G-META-001-CORE` | `python3 scripts/run_quality_gate.py`<br/>`python3 project/core/code_reviewer.py --scan-secrets`<br/>`python3 scripts/run_button_regression.py` |
| `G-META-001-SYNC` | `git status --short PROJECT_TASKS.md plans/*.md`<br/>`git diff -- PROJECT_TASKS.md plans/metaphysics_learning_roadmap.md plans/plan.md plans/question_forecast_alignment_spec.md plans/todo_tasks_plan.md` |


## 📣 RELEASE NOTES (historical completion archive)
Full historical completion details are tracked in [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).

## 📋 Release Handoff Checklist
Use [docs/RELEASE_HANDOFF_CHECKLIST.md](docs/RELEASE_HANDOFF_CHECKLIST.md) for the current gate-by-gate closure matrix and remaining operator actions before marking final ticket completion.
