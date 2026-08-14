# Rule 07 — Infrastructure & Deployment Constraints

> **Effective Date:** 2026-08-15  
> **Last Updated:** 2026-08-15  
> **Scope:** All agents (Orchestrator, Developer, DevOps, QA, Code Reviewer)

---

## 🚫 Fly.io — REMOVED FROM PROJECT

Fly.io has been **permanently removed** from the HoroConsultant project.

### Mandatory Actions
1. **Do NOT** create, reference, or suggest Fly.io deployments.
2. **Do NOT** generate or modify `fly.toml`, `.fly/` directory, or any Fly.io configuration files.
3. **Do NOT** reference `FLY_API_TOKEN` or any Fly.io secrets in code, docs, or configs.
4. **Ignore** any legacy Fly.io references found in existing files — treat them as deprecated artifacts to be cleaned up.
5. When performing deployment tasks, **skip Fly.io entirely** and use the approved deployment targets below.

### Cleanup Mandate
Any agent encountering Fly.io references in codebase files (configs, docs, scripts, env files) **MUST** flag them for removal during the current task or create a cleanup sub-task.

---

## ⚠️ Azure Container Apps — INGRESS BLOCKED

Azure Container Apps **cannot enable ingress** in the current environment configuration.

### Constraints
1. **Do NOT** rely on Azure Container Apps as a publicly reachable backend endpoint.
2. **Do NOT** configure Vercel gateway or any reverse proxy to route traffic to Azure Container Apps URLs.
3. **Do NOT** suggest Azure Container Apps as a production deployment target until the ingress issue is explicitly resolved by the user.
4. Azure-related environment variables (`AZURE_RESOURCE_GROUP`, `AZURE_CONTAINER_APP`, `AZURE_CONTAINER_APP_URL`, `AZURE_CREDENTIALS`) remain in `.env.example` for future reference but are **non-functional** for production routing.

### Impact on Architecture
- The Vercel serverless middleend gateway (`api/index.js`) **MUST NOT** proxy to Azure Container Apps.
- Backend traffic routing must use the approved deployment targets listed below.

---

## ✅ Approved Deployment Targets

| Target | Role | Status |
|---|---|---|
| **Hugging Face Spaces** | Static UI hosting + Backend API | ✅ Active |
| **Vercel Serverless** | Edge middleend gateway & health checks | ✅ Active |
| **Docker (Local)** | Local development & testing | ✅ Active |
| **Fly.io** | ~~Container hosting~~ | ❌ **REMOVED** |
| **Azure Container Apps** | ~~Backend hosting~~ | ❌ **INGRESS BLOCKED** |

---

## 🔄 Deployment Architecture (Current)

```
Client → Vercel Edge Gateway → Hugging Face Spaces Backend (FastAPI/Uvicorn)
                             → /health (Vercel standalone handler)
```

All production traffic MUST route through the Vercel → HF Spaces pipeline until alternative backend hosting is approved by the user.
