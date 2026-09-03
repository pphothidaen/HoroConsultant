---
name: sdlc-aisdlc-workflow
description: AI SDLC governance from requirements decomposition to QA, release, and post-deploy.
owner: orchestrator
responsibility: sdlc-workflow
responsible_agents:
  - orchestrator
  - business_analyst
  - developer
  - qa_tester
  - devops
---

# SDLC / AI SDLC Workflow Skill

Govern the full AI SDLC lifecycle across all phases with fail-closed gates, atomic task tracking, specialist delegation, and continuous verification.

## SDLC Phase Lifecycle

1. **Phase 0: Requirement Intake & Grill Gate (`requirement-grill-gate`)**
   - 9-Dimension intake interview led by `business_analyst` / `orchestrator`.
   - Produces GRILL REPORT with decision (`APPROVED`, `WAIVED`, or `BLOCKED`).

2. **Phase 1: Architecture & Planning (`bsa-doc-skill-management`)**
   - Specification in `plans/plan.md`.
   - Atomic task decomposition in `atomic_tasks.md` with explicit specialist role assignments and required skill lists.

3. **Phase 2: Implementation (`developer`, Metaphysics Masters)**
   - Pure ASCII logging (`[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`).
   - Single editor per module/file ownership.

4. **Phase 3: QA & Verification (`qa_tester`, `code_reviewer`)**
   - Pytest execution, contract verification, visual regression (`qa-e2e-testing`, `ui-visual-auditor`).
   - 100% test pass rate requirement.

5. **Phase 4: Safety & Review (`code_reviewer`)**
   - Secret scan, dependency audit, AST syntax verification.

6. **Phase 5: Release & Deployment (`devops`, `hf-static-release-verification`, `devops-deployment`)**
   - Multi-environment deployments (HF Spaces, Cloudflare Pages, Azure Container Apps, Vercel).
   - Live health and exact-cardinality version checks.

7. **Phase 6: Plan Archival & Governance Sync (`business_analyst`, `orchestrator`)**
   - Archive completed plans to `plans/archive/YYYY-MM-DD-<release>/`.
   - Compile `ReleaseNotes.md`.
