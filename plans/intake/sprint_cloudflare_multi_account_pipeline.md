# Grill Intake Report: Cloudflare Multi-Account Workers Deployment Pipeline & Secret Synchronization

**Date:** 2026-10-13  
**Intake Lead:** `ba_intake`  
**Task ID:** `TICKET-INTAKE-CF-HERMES-001`  
**Lane ID:** `TICKET-INTAKE-CF-HERMES-001-LANE`  
**Resolved Skills:** `[requirement-grill-gate, bsa-doc-skill-management]`  
**Ownership:** `plans/intake/sprint_cloudflare_multi_account_pipeline.md`  
**Gate Status:** `BLOCKED` (Pending `CF_API_TOKEN_HERMES` token value from `pansakorn.pho@gmail.com`)  
**Next Phase:** Handoff to `lead_ba` for ticket decomposition in `ATOMIC_TICKET.md` and `plans/plan.md`  

---

## 1. Executive Summary & Context

[INFO] Initiating 9-Dimension Grill Intake assessment for Cloudflare Multi-Account Workers Deployment Pipeline and Secret Synchronization.

The HoroConsultant infrastructure operates three distinct Cloudflare accounts hosting isolated Workers services. Historically, single-account conflation in deployment configurations and CI/CD workflows caused authentication and authorization conflicts. Specifically, previous workflows attempted to use a token associated with `gemini.web.bridge@gmail.com` (account `d91b1a43a188b73be61833adee445111`) to deploy Workers belonging to `pansakorn.pho@gmail.com` (account `bda49e4e77e00609cb1ef68561b0d9eb`), triggering Cloudflare API Error 10007 ("This Worker does not exist on your account").

Recent remediation (KAN-269) consolidated the primary Worker entry point on `project/static/_worker.js` and separated config files, but full operational pipeline execution and automated deployment across all environments remain blocked pending the generation and provisioning of the dedicated `CF_API_TOKEN_HERMES` credential.

This intake package establishes the strict multi-account boundary, audits Doppler `horo-consultant/prd` synchronization against GitHub Actions secrets, and sets forth the prerequisite acceptance criteria for sprint execution.

---

## 2. Multi-Account Cloudflare Architecture Topology

| Account Descriptor | Account Email / Owner | Cloudflare Account ID | Assigned Worker(s) | Config File | GitHub Actions Deploy Workflow | GitHub Action Secret Name |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Horo Root / Core** | `pansakorn.pho@gmail.com` | `bda49e4e77e00609cb1ef68561b0d9eb` | `horoconsultant` (Production) | `wrangler.toml` | `.github/workflows/workers-builds.yml` | `CF_API_TOKEN` |
| **Hermes Harness** | `pansakorn.pho@gmail.com` | `bda49e4e77e00609cb1ef68561b0d9eb` | `horoconsultant`, `hermes-harness-hooks`, `hermes-harness-hooks-staging` | `wrangler.hermes.toml` | `.github/workflows/workers-hermes.yml` | `CF_API_TOKEN_HERMES` |
| **Gemini Bridge** | `gemini.web.bridge@gmail.com` | `d91b1a43a188b73be61833adee445111` | `prod` (`prod.gemini-web-bridge.workers.dev`) | `wrangler.gemini.toml` | `.github/workflows/workers-gemini.yml` | `CF_API_TOKEN_GEMINI` |
| **AIPass Bridge** | `taijustarrett417@gmail.com` | `db2b77716a826311bbf9d104e125f540` | `aipass-web-bridge` (Durable Object `EXT_HUB`) | `wrangler.aipass.toml` | `.github/workflows/workers-aipass.yml` | `CF_API_TOKEN_AIPASS` |

[WARNING] Account `bda49e4e77e00609cb1ef68561b0d9eb` is owned by `pansakorn.pho@gmail.com`. Any attempt by `gemini.web.bridge@gmail.com` tokens to deploy workers in this account fails immediately with Cloudflare API Error 10007.

---

## 3. Nine-Dimension Assessment Matrix (D1-D9)

| Dimension | Severity | Assessment Status | Grounded Specification & Scope Definition |
| :--- | :--- | :--- | :--- |
| **D1: Scope Boundary** | **CRITICAL** | `[BLOCKED]` | **IN-SCOPE:**<br>1. Workflows: `.github/workflows/workers-builds.yml`, `.github/workflows/workers-hermes.yml`, `.github/workflows/workers-gemini.yml`, `.github/workflows/workers-aipass.yml`.<br>2. Doppler Project Config: Secret alignment for `horo-consultant/prd`.<br>3. GitHub Secrets Verification: Validation of `CF_API_TOKEN_HERMES` and `CF_API_TOKEN_GEMINI` (and related `CF_API_TOKEN`, `CF_API_TOKEN_AIPASS`).<br>4. Deployment script verification: `scripts/deploy-worker.sh` account routing.<br>5. Regression tests: `tests/test_kan269_worker_entrypoint_consolidation.py`, `tests/test_cloudflare_deploy.py`, `tests/test_wrangler_hermes.py`.<br><br>**OUT-OF-SCOPE:**<br>1. Changing existing secret names in production or Doppler (must remain backward-compatible).<br>2. Modifying core FastAPI backend application routes (`project/routers/**`, `project/core/**`).<br>3. Modifying Vercel gateway deployment (`deploy-vercel.yml`, `api/index.js`).<br>4. Modifying Render deployment infrastructure (`deploy-render.yml`). |
| **D2: Requirement Delta** | **HIGH** | `[BLOCKED]` | Migration from legacy monolithic deploy script (`workers-builds.yml.legacy`) using a single overloaded `CF_API_TOKEN` to fully isolated multi-account CI/CD pipelines. Wrangler v4 requires mapping each account-specific secret into the runner environment variable `CLOUDFLARE_API_TOKEN` prior to invocation. Pipeline cannot be marked complete until the missing Hermes token is provisioned. |
| **D3: Acceptance & Stop Conditions** | **CRITICAL** | `[BLOCKED]` | **Acceptance Criteria:**<br>1. Every workflow file accurately references its designated account secret.<br>2. `npx wrangler whoami --config <config>` succeeds in CI and returns the matching account ID without Error 10007.<br>3. `npx wrangler deploy --dry-run` produces clean bundle artifacts without missing entry points or schema errors.<br>4. Doppler `horo-consultant/prd` has non-colliding secrets documented and mapped.<br>5. 100% pass rate in Pytest suite for Cloudflare configuration and workflow integrity.<br><br>**Stop Conditions:**<br>1. Any cross-account token invocation detected in CI immediately fails-closed.<br>2. Deployment pipeline must NOT proceed to production rollout while `CF_API_TOKEN_HERMES` remains missing/unverified. |
| **D4: Inputs, Constraints & Dependencies** | **HIGH** | `[CONFIRMED]` | **Inputs:** Cloudflare API custom tokens with permissions: `Workers Scripts: Edit`, `KV Storage: Edit`, `R2 Storage: Edit` (where provisioned), `Zone Settings: Read`.<br>**Constraints:** Wrangler v4 only reads `CLOUDFLARE_API_TOKEN` from environment; `CF_API_TOKEN` cannot be used directly as the execution environment variable name.<br>**Dependencies:** Doppler CLI v3+, GitHub Actions runner Node 20, Cloudflare API v4 availability. |
| **D5: Architecture & Ownership** | **HIGH** | `[CONFIRMED]` | Strict role and file ownership boundaries:<br>- `ba_intake`: Intake grill gate (`plans/intake/**`).<br>- `lead_ba`: Work decomposition and tickets (`ATOMIC_TICKET.md`, `plans/plan.md`).<br>- `dev_lead` / `developer_api`: Cloudflare configuration files and GitHub Actions workflows.<br>- `qa_tester`: Automated test verification in `tests/`.<br>- Account Owners: `pansakorn.pho@gmail.com` owns root and Hermes accounts; `gemini.web.bridge@gmail.com` owns Gemini bridge account; `taijustarrett417@gmail.com` owns AIPass bridge account. |
| **D6: Assumption Register** | **CRITICAL** | `[CONFIRMED]` | 1. `wrangler.toml` and `wrangler.hermes.toml` both target account `bda49e4e77e00609cb1ef68561b0d9eb`.<br>2. `workers-builds.yml` serves production deployment for `horoconsultant` using `CF_API_TOKEN`.<br>3. `workers-hermes.yml` requires its own secret `CF_API_TOKEN_HERMES` created under `pansakorn.pho@gmail.com`.<br>4. `[[r2_buckets]]` remains absent in configs until R2 is explicitly provisioned on the account (prevents Error 10042). |
| **D7: Risk, Recovery & Security** | **CRITICAL** | `[BLOCKED]` | **Risk:** Deployment failure and outage if cross-account tokens are interchanged (Error 10007).<br>**Security Boundary:** Tokens are account-scoped with minimal least-privilege. No secret values committed to git (monitored by Gitleaks). Doppler tokens downloaded to `.env` for local dev only.<br>**Recovery Protocol:** Wrangler deploys are versioned and immutable; failed deploys leave previous active deployment running. Immediate rollback via Cloudflare dashboard or re-running prior commit workflow. Gate is `BLOCKED` until credential security is validated. |
| **D8: Budget & Evidence Strategy** | **HIGH** | `[CONFIRMED]` | Operations remain within Cloudflare Workers standard/free tier allocation. Test verification utilizes `--dry-run` bundler avoiding network/deploy billing charges. Evidence records will include Wrangler dry-run bundle hashes, `wrangler whoami` identity verification receipts, and pure ASCII test logs. |
| **D9: Metaphysics Domain & HITL Gate Check** | **CRITICAL** | `[BLOCKED]` | **Human-In-The-Loop (HITL) Gate:**<br>Account owner (`pansakorn.pho@gmail.com`) MUST generate a Cloudflare API Token for account `bda49e4e77e00609cb1ef68561b0d9eb` and save it to GitHub Actions Secret `CF_API_TOKEN_HERMES` and Doppler `horo-consultant/prd`. Until human action is completed, automated pipelines for Hermes Workers cannot deploy. |

---

## 4. Key Discovery from Kapture Audit

[ERROR] Historical Deployment Root Cause (Error 10007):
During the Kapture audit and KAN-269 remediation, the root cause of deployment failures on `workers-hermes.yml` and `workers-builds.yml` was identified:
- The token stored or proposed for `CF_API_TOKEN_HERMES` was sourced from `gemini.web.bridge@gmail.com` (`d91b1a43a188b73be61833adee445111`).
- The Worker `horoconsultant` resides on `pansakorn.pho@gmail.com` (`bda49e4e77e00609cb1ef68561b0d9eb`).
- Attempting to manage or deploy a Worker across account boundaries causes Cloudflare API to return:
  ```text
  Error 10007: This Worker does not exist on your account.
  ```
- Resolution: Each account MUST have a dedicated API token created directly within that account's Cloudflare Dashboard.

---

## 5. Doppler & GitHub Actions Secret Alignment Specification

```text
Doppler Project: horo-consultant
Doppler Config:  prd

Required Synchronization Matrix:
+------------------------+-------------------------------------+-----------------------------+-----------------------+
| Cloudflare Account     | Account ID                          | Doppler Secret Name         | GitHub Secret Name    |
+------------------------+-------------------------------------+-----------------------------+-----------------------+
| pansakorn.pho@gmail    | bda49e4e77e00609cb1ef68561b0d9eb    | CF_API_TOKEN_HERMES         | CF_API_TOKEN_HERMES   |
| pansakorn.pho@gmail    | bda49e4e77e00609cb1ef68561b0d9eb    | CF_API_TOKEN                | CF_API_TOKEN          |
| gemini.web.bridge@...  | d91b1a43a188b73be61833adee445111    | CF_API_TOKEN_GEMINI         | CF_API_TOKEN_GEMINI   |
| taijustarrett417@...   | db2b77716a826311bbf9d104e125f540    | CF_API_TOKEN_AIPASS         | CF_API_TOKEN_AIPASS   |
+------------------------+-------------------------------------+-----------------------------+-----------------------+
```

[WARNING] Existing secret names MUST NOT be renamed. Downstream CI workflows and local helper scripts rely on these exact variable keys.

---

## 6. Actionable Acceptance Checklist for Lead BA Decomposition

When `lead_ba` decomposes this intake package into `ATOMIC_TICKET.md` and updates `plans/plan.md`, the following ticket tasks must be tracked:

- [ ] **TICKET-CF-01 (HITL Blocked):** Operator `pansakorn.pho@gmail.com` provisions custom Cloudflare API token for Account `bda49e4e77e00609cb1ef68561b0d9eb` and populates GitHub Secret `CF_API_TOKEN_HERMES`.
- [ ] **TICKET-CF-02:** Validate and synchronize `CF_API_TOKEN_HERMES` and `CF_API_TOKEN_GEMINI` into Doppler `horo-consultant/prd`.
- [ ] **TICKET-CF-03:** Run automated CI dry-run validation for all 4 workflows (`workers-builds.yml`, `workers-hermes.yml`, `workers-gemini.yml`, `workers-aipass.yml`).
- [ ] **TICKET-CF-04:** Execute full test suite (`pytest tests/test_kan269_worker_entrypoint_consolidation.py tests/test_cloudflare_deploy.py tests/test_wrangler_hermes.py`) and verify 100% pass rate.
- [ ] **TICKET-CF-05:** Verify `scripts/deploy-worker.sh` routes all three accounts (`hermes`, `gemini`, `aipass`) correctly.

---

## 7. Gate Status & Handoff Recommendation

- **Intake Status:** `BLOCKED`
- **Blocker Item:** Pending human operator generation and insertion of `CF_API_TOKEN_HERMES` for account `bda49e4e77e00609cb1ef68561b0d9eb`.
- **Handoff Target:** `lead_ba`
- **Handoff Action:** `lead_ba` will register the formal sprint tickets in `ATOMIC_TICKET.md` and formulate execution sequence in `plans/plan.md`, keeping implementation paused at the gate until the blocker is cleared.

[OK] Grill intake documentation completed and committed to `plans/intake/sprint_cloudflare_multi_account_pipeline.md`.
