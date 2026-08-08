---
name: devops-deployment
description: >-
  DevOps & Release Engineering skill. Details secrets synchronization via Doppler, Hugging Face Spaces deployment,
  Docker Compose orchestration, Vercel gateway rewrites, and pre-deployment security scanning.
---

# 🚀 DevOps & Deployment Skill Guide

This skill provides operational runbooks for environment management, secrets synchronization, container orchestration, and cloud platform deployment.

---

## 🛠️ DevOps Execution Runbooks

### 1. Secret Leakage Audit
Scan the entire codebase for unmasked API keys or leaked secrets before any release:
```bash
python3 project/core/code_reviewer.py --scan-secrets
```
*Requirement*: `secret_leaks_found: 0`, `status: PASSED`.

### 2. Doppler Secrets Synchronization
Sync secrets from Doppler Vault to `.env` / `.env.production`:
```bash
python3 scripts/sync_doppler_secrets.py
```

### 3. Hugging Face Spaces Publishing & Dry Run
- **Audit Payload (Dry Run)**:
  ```bash
  python3 scripts/publish_space_hf.py --dry-run
  ```
- **Publish Live Demo**:
  ```bash
  python3 scripts/publish_space_hf.py
  ```
*Target Space*: `https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend`

### 4. Docker Compose Production Bootstrap
Verify local/prod container environment:
```bash
# Build and run background services
docker compose up --build -d

# Check health of services (app, ollama, redis)
docker compose ps

# View application logs
docker compose logs app --tail=100 -f
```

### 5. Pre-Deployment Safety Audit
Run comprehensive pre-deployment safety audit:
```bash
python3 project/core/code_reviewer.py --review
```
*Requirement*: `overall_status: READY_FOR_PROD`.

### 6. Post-Deployment Live Version Verification
Verify that live production backend and static web UI are serving the latest Git commit version (`v1.0.0.{git_commit}`):
```bash
python3 scripts/publish_space_hf.py --verify-version
```
*Requirement*: `Verification: ✅ PASSED (LATEST VERSION CONFIRMED)`.
