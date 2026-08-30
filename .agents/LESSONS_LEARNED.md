# 🎓 LESSONS LEARNED & PROBLEM AVOIDANCE DATABASE
> **Project:** HoroConsultant — Computational Metaphysics Engine  
> **Purpose:** Single Source of Truth to prevent past bugs, environment warnings, and workflow failures from ever happening again.

---

## 📌 Critical Lessons & Prevention Protocols

### 0. Test history must be evidence, not a green-suite narrative

- **Issue experienced**: source and tests were changed together in a dirty
  worktree, while the configured pre-commit hook also ran version stamping and
  staged unrelated files. A later green suite could not prove that tests were
  written before implementation or remained unchanged.
- **Lesson learned**: passing tests do not establish test-first provenance.
  Preserve a test-only commit, exact hashes, red or negative-control evidence,
  ancestry, and separated source commits in Git history.
- **Prevention protocol**: use `test-provenance-v1`, the read-only hook,
  required `Test Provenance` CI, controlled superseding baselines, and the final
  code-reviewer history audit. Mark reconstructed history
  `NON_TDD_RECONSTRUCTED`; never rewrite it into a false TDD claim.

---

### 1. 🔒 Kaggle Accelerator & Metadata Stage Locking
- **Issue Experienced**: `create_kernel_files()` was overwriting `kernel-metadata.json` with custom `machine_shape` strings on every `--push`, causing accelerator settings to toggle or fail when Kaggle quotas changed.
- **Lesson Learned**: Never mutate or recreate `kernel-metadata.json` if it already exists on disk.
- **Prevention Protocol**:
  - `create_kernel_files()` checks `if METADATA_FILE.exists()` and logs `[PRESERVE]`, preserving existing metadata 100% untouched.
  - Standard metadata uses `"accelerator": "gpu"` without hardcoding unwanted machine shapes.
  - Enforced in Rule 7 (`.agents/AGENTS.md`).

---

### 2. 🔐 2-Tier Priority Secrets Loader Architecture
- **Issue Experienced**: Warnings about missing `HF_TOKEN` or `GH_TOKEN` when secrets were only loaded from local `.env` or partially loaded from Kaggle Secrets.
- **Lesson Learned**: Enforce a strict 2-Tier Priority Loader order with explicit warning notices.
- **Prevention Protocol**:
  - **1st Priority**: `DOPPLER SECRETS STORE` (via Doppler CLI or `DOPPLER_TOKEN` API).
  - **Doppler Miss Warning**: Output `[WARNING] Secret '{key}' not found in 1st Priority (DOPPLER). Falling back to 2nd Priority ({platform})...`
  - **2nd Priority**: `PLATFORM SECRETS STORE` (`UserSecretsClient` on Kaggle for all 7 keys: `APP_SUPABASE_KEY`, `APP_SUPABASE_URL`, `DOPPLER_TOKEN`, `GH_TOKEN`, `HF_TOKEN`, `KAGGLE_TOKEN`, `WANDB_KEY`).
  - Enforced in Rule 6 (`.agents/rules/06-secrets-policy.md`).

---

### 3. 🛠️ Triton 3.x Compatibility & PyTorch / BNB CUDA Mismatches
- **Issue Experienced**: `bitsandbytes` in Kaggle Python 3.12 failed with `ModuleNotFoundError: No module named 'triton.ops'` and emitted CUDA library binary warnings.
- **Lesson Learned**: Triton 3.x removed `triton.ops`. `bitsandbytes` needs a lightweight mock shim when `triton.ops` is imported.
- **Prevention Protocol**:
  - Apply Python mock shim `sys.modules['triton.ops']` in `cloud_train_orchestrator.py` and `notebook.ipynb` before importing `bitsandbytes` or `peft`.
  - Set `BITSANDBYTES_NOWELCOME=1` to silence BNB welcome warning noise.

---

### 4. 🏷️ Dataset Fingerprint Hashing Warnings
- **Issue Experienced**: `datasets.map(format_example)` emitted `Parameter 'function'=<function format_example> couldn't be hashed properly` because inner nested closures cannot be pickled cleanly.
- **Lesson Learned**: Always use top-level module functions for `dataset.map()`.
- **Prevention Protocol**:
  - Move `format_example` to a top-level module function `_format_conversation_example(example)` in `cloud_train_orchestrator.py`.

---

### 5. 🔤 Pure ASCII Logging Guard
- **Issue Experienced**: Subprocess output containing emoji characters caused `UnicodeEncodeError: 'charmap' codec can't encode character` when piped through `ipykernel` or non-UTF-8 terminals.
- **Lesson Learned**: Standardize all logging to use pure ASCII tags.
- **Prevention Protocol**:
  - Use `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`, `[START]`, `[MODEL]`, `[CHECK]` tags instead of raw unicode emojis in logging handlers.

---

### 6. 🔄 Pre-Development Kaggle Sync Rule
- **Issue Experienced**: Modifying local code without checking remote Kaggle state resulted in kernel version drift or out-of-sync outputs.
- **Lesson Learned**: Always sync remote status prior to code edits.
- **Prevention Protocol**:
  - Agents MUST run `python3 scripts/kaggle_notebook_manager.py --status` (and `--pull` if updated) before starting any development or modifying code.
  - Enforced in Rule 6 (`.agents/AGENTS.md`).

---

### 7. 🌐 Geocoding Offline Fallback & Network Fault-Tolerance Protocol
- **Issue Experienced**: Nominatim Geocoding API threw `"ไม่พบสถานที่ดังกล่าว"` when OpenStreetMap timed out, returned 404, or when frontend was loaded from static CDN without a Python backend API connection.
- **Lesson Learned**: Never rely solely on external 3rd-party network geocoding APIs without a pre-cached offline fallback dictionary.
- **Prevention Protocol**:
  - Implement dual-layer (Client-side & Server-side) offline location lookup table (`CLIENT_LOCATION_DICT` & `OFFLINE_LOCATIONS`) covering major Thai provinces, districts, and international cities.
  - If network geocoding fails or runs on static host, automatically resolve coordinates from the pre-cached offline dictionary without throwing user-facing errors.

---

### 8. 🔐 Decoupled Admin Auth & Strict Email Whitelist Governance
- **Issue Experienced**: Static frontend host showed `"Email authentication failed"` when calling backend `/admin/auth/google` because no API server listened at the relative static URL, and unauthorized emails were confusingly rejected without clear status.
- **Lesson Learned**: Strict admin authorization must enforce `ADMIN_ALLOWED_EMAILS=pansakorn@gmail.com,kimlenglim.work@gmail.com` with client-side authorized fallback when operating on static Edge CDNs.
- **Prevention Protocol**:
  - Enforce strict whitelist `ADMIN_ALLOWED_EMAILS` restricting access exclusively to `pansakorn@gmail.com` and `kimlenglim.work@gmail.com`.
  - Provide authorized client-side authentication fallback for static CDNs so admin users can seamlessly access Admin Panel and HITL Studio across all environments.

---

### 9. 🌐 Multi-Cloud Serverless CORS & Package Size Limit Protocol
- **Issue Experienced**: Executing `curl` against `https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret` from origin `https://pphothidaen-horoconsultant-core-backend.static.hf.space` yielded a CORS error / `FUNCTION_INVOCATION_FAILED (500)` and `health` returned `(failed) net::ERR_CONNECTION_RESET`.
- **Definitive Root Cause (2026-08-09 confirmed)**: `api/main.py` contained `from project.main import app as fastapi_app` at **module level** (line 12). This forced Vercel to import the entire FastAPI stack (FAISS, RAG, apscheduler, swisseph, all astrology engines) at Lambda cold-start. The heavy dependency chain crashed the Lambda → `FUNCTION_INVOCATION_FAILED (HTTP 500)`. When a Lambda returns a bare 500, Vercel omits `Access-Control-Allow-Origin` headers entirely → browsers see a misleading CORS error (the real error is the import crash, not CORS).
- **Lesson Learned**:
  1. **Never import project.main in api/main.py**: `api/main.py` is the Vercel serverless entry point. It MUST remain lightweight — no FAISS, no RAG, no heavy engines at module level. The `_dispatch` / `handler` functions are self-contained and never needed `project.main`.
  2. **Vercel Lambda Package Limit (250MB)**: Heavy C binaries (`faiss-cpu`, `uvloop`) in `requirements.txt` cause Lambda cold-start crashes.
  3. **CORS error ≠ CORS bug**: When a Vercel Lambda crashes before returning ANY response, the browser reports a CORS error because `Access-Control-Allow-Origin` is absent. Always check `X-Vercel-Error: FUNCTION_INVOCATION_FAILED` in response headers first.
  4. **Hugging Face Free Tier Limits**: HF free tier only supports **Static** Spaces (`sdk: static`). Free Docker Spaces require a PRO subscription (`402 Payment Required`).
  5. **Fly.io Idle Resets**: Non-existent or suspended Fly.io containers return `net::ERR_CONNECTION_RESET`.
- **Prevention Protocol (Updated Fix)**:
  - **api/main.py**: Remove ALL `project.main` imports. Use lazy imports with `try/except` fallback only inside function bodies. Add `_safe_dispatch()` wrapper that guarantees CORS headers on every response including uncaught exceptions.
  - **runtime.txt**: Pin `python3.11` so Vercel uses a consistent runtime.
  - **CORS fallback**: If `project.core.cors` import fails, use an inline CORS header builder that reads `CORS_ALLOWED_ORIGINS` env var directly (no dependencies).
  - **requirements.txt**: Keep lightweight (< 15MB): `fastapi`, `pydantic`, `httpx`, `python-dotenv`, `numpy`, `geopy`, `pyyaml`, `aiofiles` only.
  - **Post-deploy verification**: Run `python3 scripts/run_vercel_prod_curl_regression.py` after every Vercel deploy to verify all 3 endpoints pass with CORS headers.
  - **Client Web UI (`app.js`)**: Use dynamic `${getApiBaseUrl()}/health` for health pings instead of hardcoded Fly.io URLs.

### 10. 🔍 Code Reviewer `.venv` False-Positive Secret Scan Bug
- **Issue Experienced**: `python3 project/core/code_reviewer.py --review` returned `BLOCKED` status with 3 "CRITICAL Kaggle API Token" secret leaks found in `.venv/lib/python3.11/site-packages/_pytest/pathlib.py`, `pip/_internal/metadata/__init__.py`, and `numpy/tests/test_configtool.py`. These are NOT real secrets — they are internal pattern strings inside pip/pytest/numpy source code that match the `kg_[A-Za-z0-9_-]{20,}` regex pattern.
- **Root Cause**: The exclusion list used `"venv"` as a path part check, but the actual virtual environment directory is named `.venv` (with a dot prefix). Since `".venv"` != `"venv"`, the path parts check never matched, allowing the scanner to enter and scan all 3,000+ third-party package files.
- **Lesson Learned**: When using `path.parts` for directory exclusion, always use the exact directory name (including leading dot for hidden directories). A `.venv` directory has the path part `".venv"`, not `"venv"`.
- **Prevention Protocol**:
  - The exclusion list in `CodeReviewer.scan_secrets()` (line 68) now includes both `"venv"` AND `".venv"` explicitly.
  - Also added `"wandb"`, `"node_modules"`, and `".vercel"` to prevent similar false positives from other third-party tool directories.
  - Fixed result: scanner now audits 1,077 project files (down from 4,156), 0 secrets found, status correctly `READY_FOR_PROD`.
  - **Verification**: After fix, run `python3 project/core/code_reviewer.py --review` and confirm `"overall_status": "READY_FOR_PROD"` and `"scanned_files": ~1077`.

---

### 11. 🌐 Hugging Face Space URL & Endpoint Topology Disconnect
- **Issue Experienced**: Calling `curl 'https://pphothidaen-horoconsultant-core-api.hf.space/api/v1/bazi/calculate'` or `.../interpret` from Origin `https://pphothidaen-horoconsultant-core-backend.static.hf.space` failed with `HTTP 404 (Not Found)`.
- **Definitive Root Cause**:
  1. **Space Hostname Mismatch**: The deployed Hugging Face Space under `pphothidaen` is named `pphothidaen/horoconsultant-core-backend` (not `core-api`).
  2. **Static SDK vs Backend API**: `pphothidaen/horoconsultant-core-backend` is deployed under `sdk: static` (HTML/JS/CSS frontend CDN) which serves static files only and cannot execute Python FastAPI backend code directly.
  3. **API Routing Architecture**: The API routes (`/api/v1/bazi/calculate`, `/api/v1/bazi/interpret`, `/api/v2/*`) must be directed to the active backend gateway (e.g. `https://horo-consultant-psi.vercel.app` or local `http://localhost:8000` / Docker backend) with CORS origin matching the static space.
- **Prevention Protocol & Verification**:
  - Added [`project/tests/test_api_integration_suite.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_api_integration_suite.py) containing 19 integration tests validating all v1 and v2 API endpoints, CORS preflight (`OPTIONS`), and exact browser headers from `https://pphothidaen-horoconsultant-core-backend.static.hf.space`.
  - Verified 19/19 integration tests pass 100%.

---

### 12. ⚡ Native Transformers Trainer Standard over Fragmented SFTTrainer Wrappers
- **Issue Experienced**: SFTTrainer across TRL versions 0.7.x through 0.15.x introduced breaking signature changes (`dataset_text_field`, `max_seq_length`, `processing_class` vs `tokenizer`), causing runtime crashes (`ValueError: Unable to create tensor... features ('text') have excessive nesting`).
- **Definitive Root Cause**: TRL's `SFTTrainer` encapsulates custom dataset collators and defaults `dataset_text_field = 'text'`, conflicting with datasets that are already pre-tokenized into `input_ids` and `attention_mask`.
- **Lesson Learned**: For causal language modeling with pre-tokenized datasets and LoRA adapters, standard `transformers.Trainer` with `peft.get_peft_model()` and `transformers.DataCollatorForLanguageModeling(mlm=False)` provides 100% deterministic stability with zero breaking changes across all cloud platforms.
- **Prevention Protocol**:
  - `scripts/cloud_train_orchestrator.py` wraps `model = get_peft_model(model, peft_config)` and instantiates native `transformers.Trainer`.
  - Enforced in `tests/test_notebook_syntax.py::test_dataset_pre_tokenization_pipeline`.

---

### 13. 🔍 Python Closure Variable Scope Ordering & Static AST Quality Gate
- **Issue Experienced**: `NameError: cannot access free variable 'max_seq_length' where it is not associated with a value in enclosing scope` at line 763.
- **Definitive Root Cause**: Assigning `max_seq_length = 1024` *after* defining an inner function closure (`_tokenize_batch`) that referenced `max_seq_length` made Python treat `max_seq_length` as an unbound local variable at the time `_tokenize_batch` was invoked.
- **Lesson Learned**: Python functions must declare and initialize all configuration parameters and hyperparameters at the top of the function scope before any closures or dataset map operations.
- **Prevention Protocol**:
  - Move all hyperparameter definitions to the very top of `run_training_pipeline()`.
  - Enforce static AST linting via `tests/test_notebook_syntax.py::test_python_closure_variable_scope_hygiene` which walks AST trees to detect any closure referencing variables assigned later in the parent function.

---

### 14. 🔗 Cloud Execution Traceability & Kaggle-GitHub Synchronization Protocol
- **Issue Experienced**: Kaggle kernel executed an older GitHub commit because local files were modified without a preceding `git push origin main`, causing confusion between local code state and cloud execution logs.
- **Definitive Root Cause**: Kaggle kernels dynamically clone `https://github.com/pphothidaen/HoroConsultant.git` (`origin/main`). If local edits are not pushed to GitHub before `kaggle kernels push`, the cloud GPU runs the previous commit.
- **Lesson Learned**: Pushing to Kaggle must always be preceded by a Git synchronization check, and the cloud kernel must explicitly log the exact commit hash it is running.
- **Prevention Protocol**:
  - `scripts/kaggle_notebook_manager.py` implements `check_git_sync_safety()` before executing `--push`, alerting if uncommitted changes or unpushed commits exist.
  - Cell 2 in `notebook.ipynb` prints `[GIT] Cloud Environment Active Commit: <hash> (<message>)` at startup for 100% log traceability.
  - `kaggle_notebook_manager.py` enforces `--force` on all output download operations to guarantee fresh logs.
---

### 15. 🎯 PyTorch Target Tensor Dtype Invariance (`torch.long` Labels Enforcement)
- **Issue Experienced**: `NotImplementedError: "nll_loss_backward_reduce_cuda_kernel_2d_index" not implemented for 'Float'` during `trainer.train()` backward pass.
- **Definitive Root Cause**: In PyTorch CrossEntropyLoss and NLLLoss, the target `labels` tensor must strictly be of integer index type (`torch.long` / `int64`). If `labels` is autocast, scaled, or passed as `torch.float32`/`torch.float16`, the CUDA autograd backward kernel throws `NotImplementedError` for `'Float'`.
- **Lesson Learned**: Always enforce explicit `torch.long` integer dtype conversion on `labels` and `input_ids` inside custom DataCollator and `Trainer.compute_loss()`, regardless of model weight precision or mixed precision (`fp16`) training settings.
- **Prevention Protocol**:
  - `SafeDataCollator` in `scripts/cloud_train_orchestrator.py` explicitly converts `batch["labels"] = batch["labels"].to(torch.long)`.
  - Registered `_safe_compute_loss` wrapper on `transformers.Trainer` that ensures `inputs["labels"] = inputs["labels"].long()`.
  - Enforced via `tests/test_notebook_syntax.py::test_safe_data_collator_and_long_dtype_loss_guard`.

### 16. 🚫 BaZi Canonical Calculation Blocker & No-Fabricated-Fallback Policy
- **Issue Experienced**: The browser pre-rendered a simplified chart and the Vercel gateway could return a hardcoded chart when the canonical backend was unavailable. This produced incorrect Hour/Month pillars, including a false `癸未` result instead of the verified Ratchaburi `辛亥` result.
- **Root Cause**: Calculation logic was duplicated across client JavaScript, gateway fallback handlers, and the canonical Python/Rust engine. Backend health was treated as advisory, and incomplete responses were rendered as successful charts.
- **Lesson Learned**: BaZi calculation is blocker-grade. Only the canonical backend may authorize a chart; client-side calculation is preview-only and must never be rendered as authoritative or used for interpretation/storage.
- **Prevention Protocol**:
  - Frontend requires backend health before calculation and opens a BLOCKER modal with retry/admin actions on failure.
  - Frontend validates that `year`, `month`, `day`, and `hour` pillars exist before rendering.
  - Vercel returns HTTP 503 `canonical_bazi_unavailable` instead of fabricated chart data when the backend is unavailable.
  - API responses preserve Ten Gods, Pillar Phase, Stars, and hidden-stem metadata.
  - The golden vector `1985-08-26 23:03:00`, Ratchaburi, UTC+7 must equal `辛亥 / 丁酉 / 甲申 / 乙丑` and remain covered by Python/Rust parity tests.

### 17. 🧾 Static-Space Health and Version Gates Must Be SDK-Aware and Fail Closed
- **Issue Experienced**: The release command treated a Static Hugging Face Space as a Docker API by probing `/health`, while version verification could pass when the retired Fly backend was unavailable or when only one client asset loaded. Re-publishing also risked stale or composite version labels.
- **Root Cause**: Health topology and release evidence were not separated by SDK. The verifier used first-match and substring checks, so duplicate version declarations could hide a later stale runtime value.
- **Lesson Learned**: Static health is evidence from the rendered root plus valid production `version.json`; Docker health is evidence from `/health`. A production version gate must require every declared version/cache surface exactly once and match the expected release.
- **Prevention Protocol**:
  - Static `--check-health` checks `/` and `/version.json`; Docker retains `/health`.
  - Static `--verify-version` requires HTTP 200 and exact version/commit coherence across `version.json`, `index.html`, `app.js`, `sw.js`, and `v3_tokens.css`.
  - `CURRENT_PAGE_VERSION`, footer version, four cache-busting references, `CLIENT_APP_VERSION`, and service-worker cache version must each occur exactly once; missing, duplicate, stale, composite, malformed, or unreachable evidence fails the command with a non-zero exit code.
  - Regression coverage includes idempotent stamping, duplicate declarations, missing assets, network errors, SDK-specific health behavior, and CLI failure exit status.
  - Post-change evidence: publisher suite `16 passed`; combined publisher and visual-audit regression `24 passed`; live Static health and exact-version checks passed for `1.0.0.6c351ba` / `6c351ba`.

### 18. 🧭 Ready Deployment Does Not Prove Gateway Configuration or Release Identity

- **Issue Experienced**: A Vercel production deployment was `READY` and served
  the correct merged SHA, but every proxied API call returned HTTP 503. The
  canonical HF Docker backend itself returned 200. Separately, its health body
  exposed `version/git_commit=unknown`, and the five-viewport audit found a
  clipped mobile tab, long-content clipping, and a 3.8:1 chevron contrast pair.
- **Root Cause**:
  1. Vercel production had no `HF_BACKEND_URL`; the gateway correctly rejected
     the absent canonical origin as `backend_not_configured`.
  2. Historical executable bits contradicted the frozen `100644` HF payload
     contract, while a first remediation test incorrectly tried to weaken that
     contract.
  3. The version stamper still emitted legacy metadata after the publisher had
     moved to immutable `release_source_*` provenance.
  4. HF runtime images have neither provider commit environment data nor a Git
     checkout, so dynamic Git lookup alone cannot expose release identity.
- **Lesson Learned**: Deployment readiness, backend reachability, gateway
  configuration, exact release identity, API behavior, and rendered UI quality
  are distinct gates. A green result from one may not substitute for another.
- **Prevention Protocol**:
  - Verify required environment-variable **names/scopes** before redeploying;
    never print values or assume a prior deployment inherited a missing entry.
  - Keep an exact env-entry ID and prior production deployment as rollback
    anchors, then prove the canonical alias and `x-deploy-sha` after redeploy.
  - When a frozen test conflicts with an established contract, stop source
    work and use a test-only superseding baseline. Preserve the original commit
    and cutoff; never amend or silently rewrite it.
  - Stamp a closed five-field metadata object from one immutable source commit,
    keep public/backend UI surfaces mirrored, and validate its SHA-256 digest.
  - In a Git-less image, accept baked identity only after env/file/Git fallbacks
    are exhausted and the closed metadata schema, version binding, full source
    revision, and digest all validate. Tampered metadata returns `unknown`.
  - Require live API E2E plus all five visual viewports. Mobile content height
    and contrast failures block a full `READY_FOR_PROD` claim even when API
    recovery is complete.

### 19. Revoked Codex OAuth Tokens Block Native Delegation Before Project Aliases

- **Issue experienced**: native delegated-agent creation and official OpenAI
  documentation access both failed with HTTP `401` and `token_revoked`, while
  local repository commands still worked. The failure was initially easy to
  confuse with the project routes `codex1`, `codex2`, `agy1`, or `agy2`.
- **Root cause**: the active Codex runtime used ChatGPT OAuth credentials under
  `~/.ai-accounts/codex/account3`; its refresh token had been revoked. Native
  collaboration failed before any project alias, provider route, model, quota,
  or ticket command was invoked.
- **Lesson learned**: distinguish the Codex runtime account directory from
  project provider aliases. A native collaboration error that explicitly says
  `token_revoked` is an authentication failure of the active Codex account, not
  evidence that a project alias or provider account is broken.
- **Recovery protocol**:
  1. Inspect only non-secret metadata: active account directory, `auth_mode`,
     credential-file presence/mtime, and the exact sanitized error. Never print
     access, identity, or refresh tokens.
  2. Re-authenticate only the affected account:
     `CODEX_HOME=~/.ai-accounts/codex/account3 codex logout`, followed by
     `CODEX_HOME=~/.ai-accounts/codex/account3 codex login --device-auth`.
  3. The human opens `https://auth.openai.com/codex/device` and enters the
     one-time code. Never persist that code in repository evidence or logs.
  4. Verify with the same account directory and `codex login status`; require
     `Logged in using ChatGPT` before retrying native delegation.
  5. Retry the smallest bounded delegated action first. Preserve the original
     ticket scope and do not treat re-authentication as new provider, Git,
     deployment, or production authorization.

---

### 20. ⚡ Fast-Track Auto-Remediation & Remote Truth-First Protocol

- **Issue Experienced**:
  1. **Multi-round status assumption loops**: Local agents inferred remote CI or platform deployment status from stale local timestamps or optimistic assumptions rather than inspecting live remote states, causing redundant triage rounds and circular diagnostics.
  2. **Test provenance intermediate cutoff traps**: In multi-baseline PR lifecycles, intermediate baseline manifests triggered false-positive ancestry or cutoff violations when evaluated against subsequent intermediate or unmerged commits without topological awareness.
  3. **CI test runner timeouts**: Sequential test runs hanging indefinitely or exceeding CI timeout budgets on heavy integration and RAG test suites due to unisolated background processes or unhandled socket connections.
- **Root Causes**:
  1. **Decoupled remote truth**: Modifying local code or documentation without first fetching and verifying authoritative remote state (`git fetch origin`, live gateway `/health` and `/version.json`, cloud platform status).
  2. **Non-topological baseline evaluation**: Evaluating historical baseline manifests linearly instead of determining topological branch ancestry and explicit superseding manifest cutoffs.
  3. **Monolithic test suites**: Executing integration, AST syntax, and unit test suites serially without fail-fast thresholds or process isolation.
- **Fast-Track Solutions**:
  1. **Single-Turn Triage Bundle**: Package diagnostic commands (ecosystem sync check, test provenance PR verification, live gateway probe) into a single deterministic turn rather than waiting across multiple polling iterations.
  2. **Remote Truth-First Preflight**: Enforce an immediate `git fetch origin` and live remote query before formulating remediation plans or modifying state.
  3. **Topological Cutoff Isolation**: Resolve multi-baseline PR lineages using topological ordering and ancestor-bounded verification windows to isolate superseded manifests.
  4. **Fail-Fast Parallel Testing**: Partition test suites with per-test timeouts, fail-fast failure gates (`pytest -x -q`), and deterministic sub-process cleanup.
- **Prevention and Recovery Protocol**:
  1. **Remote Preflight**: Always run `git fetch origin` and query live target endpoints before starting triage or claiming production status.
  2. **Ecosystem & Provenance Gate**: Execute `python3 scripts/sync_ai_agent_ecosystem.py --check` and `python3 scripts/test_provenance_guard.py verify-pr origin/main HEAD` as standard triage bundles.
  3. **Isolated Cutoff Registration**: When updating test baselines across iterations, register explicit `supersedes` relationships in `plans/test_provenance/` manifests.
  4. **Fail-Fast Parallel Testing**: Run partitioned test commands (`pytest tests/test_notebook_syntax.py`, `pytest project/tests/test_api_integration_suite.py`) with explicit timeouts.
  5. **Pure ASCII & SSoT Discipline**: Maintain pure ASCII logging (`[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`) and synchronize all documentation updates to Single Source of Truth across agent directories.
