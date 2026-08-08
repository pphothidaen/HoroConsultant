# 🎓 LESSONS LEARNED & PROBLEM AVOIDANCE DATABASE
> **Project:** HoroConsultant — Computational Metaphysics Engine  
> **Purpose:** Single Source of Truth to prevent past bugs, environment warnings, and workflow failures from ever happening again.

---

## 📌 Critical Lessons & Prevention Protocols

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
- **Lesson Learned**:
  1. **Vercel Lambda Package Limit (250MB)**: Heavy C binaries (`faiss-cpu`, `uvloop`) in `requirements.txt` cause Lambda cold-start import crashes. When Lambdas crash (HTTP 500), Vercel omits `Access-Control-Allow-Origin` headers, causing browsers to report a false-positive CORS error.
  2. **Hugging Face Free Tier Limits**: HF free tier only supports **Static** Spaces (`sdk: static`). Free Docker Spaces require a PRO subscription (`402 Payment Required`). Proxying `/api/*` from Vercel to a Static HF Space returns 404 HTML.
  3. **Fly.io Idle Resets**: Non-existent or suspended Fly.io containers (`horoconsultant-core-backend.fly.dev`) return `net::ERR_CONNECTION_RESET`.
- **Prevention Protocol**:
  - **Vercel**: Keep `requirements.txt` lightweight (<15MB, remove `faiss-cpu`, `uvloop`, `pytest`, `timezonefinder`). Add `sys.path` root initialization in `api/index.py`, `runtime.txt` specifying `python-3.11`, and a global `@app.exception_handler(Exception)` in `project/main.py` guaranteeing CORS headers on all errors.
  - **Hugging Face**: Use `sdk: static` for free static UI hosting (`pphothidaen-horoconsultant-core-backend.static.hf.space`).
  - **Client Web UI (`app.js`)**: Use dynamic `${getApiBaseUrl()}/health` for health pings instead of hardcoded Fly.io URLs.


