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
