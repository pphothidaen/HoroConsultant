# Hermes Agent Team — Operational Governance Policy

**Project**: HoroConsultant (GitHub: `pphothidaen/HoroConsultant`)  
**Jira**: Cloud Project `KAN` — Epic `KAN-38`  
**Effective**: 2026-09-21  
**Owner**: Lead Autonomous DevOps & Systems Integration Agent

---

## 1. Agent Governance & Operational Rules

### 1.1 Branch & PR Hygiene Enforcement
- **PR Title Format**:  
  ```
  [KAN-NN] Short description
  [KAN-NN][KAN-MM] Short description (cross-cutting)
  ```
- **Branch Naming**:
  ```
  feat/KAN-NN-short-description
  fix/KAN-NN-short-description
  docs/KAN-NN-short-description
  chore/KAN-NN-short-description
  ```
- **Linked Jira Issue**: Each PR **must** link a valid Jira issue in the Development Panel.

### 1.2 Fail-Safe Policy
- **Critical Security Detection** → Block + human approval required
- **Unhandled Merge Conflicts** → Block + alert human
- **Schema Mismatch (e.g., test provenance)** → Block + require remediation

---

## 2. Git Hooks & CI/CD Skill Actions

### 2.1 Pre-commit Hook
**.githooks/pre-commit-jira-check**
- Validates branch name matches `feat/KAN-NN-...` / `fix/KAN-NN-...`

### 2.2 Pre-push Hook
**.githooks/pre-push-jira-validate**
- Rejects force-push to shared branches (Human Authority Boundary)

### 2.3 GitHub Actions
**.github/workflows/jira-governance.yml**
- Triggers: `pull_request: [opened, edited, synchronize, reopened]`
- Job 1: `validate-pr-title` — enforces `[KAN-NN]` prefix regex
- Job 2: `notify-agent-on-failure` — webhooks Hermes on CI failure

---

## 3. Responsibilities & Boundaries Matrix

| Capability | Autonomous Scope | Human Authority Only |
|---|---|---|
| Branch validation | ✅ Validate PR titles, branch names, linked Jira keys | ❌ Merging to `main`/production |
| Git hooks enforcement | ✅ Pre-commit checks, commit message lint | ❌ Force-pushing over history |
| Jira sync | ✅ Auto-link PR ↔ Issue, comment on PR | ❌ Workflow scheme changes |
| CI/CD automation | ✅ Trigger workflows, verify status checks | ❌ Approving production deploy |
| Issue transitions | ✅ In Review ↔ In Progress ↔ Resolved | ❌ Done transition (final sign-off) |
| Security scans | ✅ Detect & flag secrets/vulnerabilities | ❌ Bypassing security findings |

---

## 4. CI Self-Healing

- **Auto-trigger** `pre-deployment-safety-audit` workflow on PR edit
- **Fail-fast** on any missing Jira key or provenance mismatch
- **Fallback webhook** → Hermes orchestrator on CI_FAILURE event
- **Rollback policy**: If merge conflict detected post-CI, auto-revert to HEAD of `main`

---

## 5. Release Management

- All issues in Sprint E linked to **Fix Version/s**: `Sprint E Incident Closure`
- Release criteria: 100% tests pass, 0 secret leaks, 0 schema mismatches
- Post-merge: Auto-publish `ReleaseNotes.md` to `docs/`
