---
title: "AI-Assisted SDLC — HoroConsultant"
subtitle: "AI-Assisted Software Development Lifecycle Analysis"
author: "HoroConsultant DevOps Team"
date: "2026-10-30"
---

# AI-Assisted SDLC — HoroConsultant

**Report:** High-Level Summary of AI-Assisted Software Development Lifecycle  
**Date:** 2026-10-30  
**Project:** HoroConsultant (pphothidaen/HoroConsultant)  
**Sources:** `.github/workflows/*`, `.githooks/*`, `.agents/rules/*`, `scripts/*`, `HOWTO.md`, `AGENTS.md`

---

## 1. Executive Summary

### 1.1 Summary Sentence

> **AI assists in all SDLC phases except final decision-making.** AI codes, checks quality, and performs security checks, then releases to production. Humans make final decisions in 3 points: **Scope / Priority**, **Quality Acceptance**, **Release Authorization**.

### 1.2 Key Conclusions

| Topic | Summary |
|---|---|
| **AI Covers** | All phases from intake → code → test → review → deploy |
| **Human Authority** | 3 points: scope/priority, quality acceptance, release approval (HITL) |
| **Fail-Closed** | Multi-layer gate system (pre-commit, pre-push, CI, post-deploy) — **Local hooks = Advisory (non-blocking); CI/Pre-merge = Hard Fail-Closed Gate** |
| **Primary AI Roles** | `developer`, `qa_tester`, `code_reviewer`, `orchestrator`, `devops` |
| **Human Primary Roles** | `ba_intake`, `business_analyst`, `HITL reviewer` |

---

## 2. Table of Contents

1. Executive Summary
2. Table of Contents
3. Where AI Assists in SDLC
4. AI vs Human Decision Matrix
5. SDLC Phase Breakdown
6. Verification & Security Scan Flow
7. Diagram: SDLC Flow with AI
8. Conclusion
9. Appendix — References

---

## 3. Where AI Assists in SDLC

### 3.1 How AI Helps

| Step | AI Does | Reliability |
|---|---|---|
| **1. Intake** | `ba_intake`, `lead_ba` — draft tickets, specs, requirements | AI drafts, Human reviews scope |
| **2. Branching** | `orchestrator` — split 6-lane work, create branch | AI creates branch, dispatch |
| **3. TDD (Test-First)** | `qa_tester` + `tdd_gate.py` | Write **Integration Tests → Unit Tests** (Red) → Green → manifest |
| **4. Code Implementation** | `developer` | Write production code (after TDD GREEN) |
| **5. Code Review** | `code_reviewer.py` — Secret scan, AST audit, **Complexity & Boundary check** | AI reviews Surface (Layer 1) → Human reviews Intent (Layer 2) |
| **6. Pre-commit** | `pre-commit` hook | AI summarizes test provenance, Jira label (Advisory) |
| **7. Pre-push** | `pre-push` hook | AI verifies TDD state, provenance, **Risk-tiered lanes** (Advisory) |
| **8. Post-commit** | `post_commit_check.py` | AI summarizes docs sync, INDEX.md |
| **9. Post-deploy** | `post-deploy-tdd.yml` (Team Red/Blue) | AI attack simulation + validation |
| **10. Maintenance** | **Autonomous feedback loop** | AI generates `intent.md`/`ATOMIC_TICKET.md` from Production findings |
| **11. Production** | `dod-production-gate.yml` + HITL | AI verify + Human approve |

---

## 4. AI vs Human Decision Matrix

| Step | System | Who Helps | Who Decides |
|---|---|---|---|
| **Intake** | `ba_intake`, `lead_ba` | 🤖 AI + 👤 Human | 👤 Human (scope, priority) |
| **Bootstrap / Design (ADR)** | `docs/PROJECT.md`, `docs/adr/` | 🤖 AI (draft) + 👤 Human | 👤 Human (architectural boundary) |
| **Branch + Dispatch** | `orchestrator` | 🤖 AI | — |
| **TDD: Integration Tests** | `qa_tester` + `tdd_gate.py` | 🤖 AI | — |
| **TDD: Unit Tests** | `qa_tester` + `tdd_gate.py` | 🤖 AI | — |
| **Code Implementation** | `developer` | 🤖 AI | — |
| **Code Review — Layer 1 (Surface)** | `code_reviewer.py` | 🤖 AI | — |
| **Code Review — Layer 2 (Intent)** | `code_reviewer.py` + PR | 🤖 AI (pre-filter) + 👤 Human | 👤 Human (merge PR, intent/complexity/boundary) |
| **Pre-commit Gate** | `pre-commit` hook | 🤖 AI | — (Advisory, non-blocking) |
| **Pre-push Gate** | `pre-push` hook | 🤖 AI | — (Advisory, non-blocking) |
| **Post-commit Verify** | `post_commit_check.py` | 🤖 AI | — |
| **Post-deploy TDD** | `post-deploy-tdd.yml` | 🤖 AI | — |
| **Maintenance Loop** | Autonomous (Red/Blue → intent.md) | 🤖 AI | 👤 Human (triage escalation) |
| **Release Gate** | `dod-production-gate.yml` | 🤖 AI + 👤 **HITL** | 👤 HITL (approve/release) |
| **Production Deploy** | `deploy-render.yml`, `deploy-vercel.yml` | 👤 **Human** | 👤 Human (manual dispatch) |

---

## 5. SDLC Phase Breakdown

### 5.1 Phase 1: Intake & Planning

**System:** `ba_intake`, `lead_ba` (business_analyst)  
**AI Does:** Draft tickets (ATOMIC_TICKET.md), specs (plans/plan.md), 9-Dim grill  
**Human Decides:** Scope, priority, business commitment

| System | AI Does | Human Does |
|---|---|---|
| `ba_intake` | 9-Dim grill intake, patterns from Gemini MCP | scope, priority, business commitment |
| `lead_ba` | Register tickets, adjust config | Approve scope, check quality |

---

### 5.2 Phase 1.5: Bootstrap & Design Governance (ADR) ⭐ *NEW*

**System:** `docs/PROJECT.md`, `docs/adr/`  
**AI Does:** Draft `PROJECT.md` (architecture baseline, tech stack, runtime constraints), draft ADR for architectural decisions  
**Human Decides:** Architectural boundary, tech stack approval, ADR acceptance

| Step | System | AI Does | Human Decides |
|---|---|---|---|
| 1 | `docs/PROJECT.md` | Draft architecture baseline, tech stack, runtime constraints | Approve baseline, lock tech stack |
| 2 | `docs/adr/` | Draft ADR for Tier 3 changes (core, security, model promotion) | Accept/Reject ADR before TDD starts |
| 3 | `tdd_gate.py` | Check ADR exists for Tier 3 changes | Override only with documented rationale |

> **Rule:** Tier 3 changes (core engine, security, model promotion) **must have accepted ADR** before entering TDD phase. `tdd_gate.py` enforces this as a hard fail-closed gate.

---

### 5.3 Phase 2: Branch & Dispatch

**System:** `orchestrator` (Master Orchestrator)  
**AI Does:** Split requirement → atomic tasks, create branch `feat/KAN-NN-description`, dispatch subagents  
**Human:** Full automated process

---

### 5.4 Phase 3: TDD (Test-First Development) — **Integration → Unit Order** ⭐ *UPDATED*

**System:** `qa_tester` + `tdd_gate.py`  
**AI Does:** Write tests (Red) → Green → manifest  
**Human:** Does not write tests  
**Note:** TDD before developer coding (HOWTO.md 3.13)  
**Enforced Order:** **Integration Tests → Unit Tests → Implementation Code**

| Order | Status | System | Notes |
|---|---|---|---|
| 1 | Backlog | `ba_intake` | In ticket |
| 2 | **TDD RED (Integration)** | `qa_tester` | Write failing integration test first |
| 3 | **TDD RED (Unit)** | `qa_tester` | Write failing unit test |
| 4 | **TDD GREEN** | `qa_tester` + `tdd_gate.py` | All tests pass + manifest |
| 5 | Review (Layer 1: AI) | `code_reviewer.py` | AST, Secret, Syntax, Complexity |
| 6 | Review (Layer 2: Human) | PR + Human | Intent, Complexity O(n), Boundary, Algorithm |
| 7 | Done | CI | merge + CI verification |

---

### 5.5 Phase 4: Code Implementation

**System:** `developer` (Senior Developer)  
**AI Does:** Write production code (`project/**`)  
**Human:** Does not write code  
**Condition:** Start coding only after TEST_BASELINE_VERIFIED (TDD GREEN)  
**Forbidden:** Do not edit tests retroactively (FROZEN_TEST_CHANGED)

---

### 5.6 Phase 5: Code Review — **Layered Review** ⭐ *UPDATED*

**System:** `code_reviewer.py` + GitHub Actions CI  
**AI Does (Layer 1 — Surface & Static Filter):**
- Secret scan (API keys, tokens, private keys)
- AST syntax audit (null bytes, surrogate encoding, compile check)
- Kaggle CUDA dependency safety
- Notebook syntax & dependency lock compliance
- **Cyclomatic / Cognitive complexity analysis**
- **Memory retention pattern detection** (streaming vs full-load)
- **Algorithmic complexity flags** (O(n²) loops, nested iterations)

**Human Does (Layer 2 — Intent & PR Merge Gate):**
- Does code match actual intent? (Intent alignment)
- Can it handle heavy load? (Load/stress reasoning)
- Does it respect system boundaries? (Boundary respect)
- Is the algorithm appropriate? (O(n) vs O(n²))
- **Merge PR** (Orchestrator prepares PR, Human clicks merge)

> **Rule:** Critical/Regulated code (Tier 3) **must have Human Intent Review before Merge** — cannot flow to single Release Gate only.

---

### 5.7 Phase 6: Pre-commit & Pre-push Gates

**System:** `.githooks/pre-commit`, `.githooks/pre-push`  
**AI Does:**
- pre-commit: test provenance verify, Jira label check
- pre-push: TDD state machine, provenance check, per-commit coverage, **Risk-tier detection**

| System | Check | Output |
|---|---|---|
| `.githooks/pre-commit` | `test_provenance_guard.py staged` + `jira_label_gate.py` | exit 0/1, **advisory (non-blocking)** |
| `.githooks/pre-push` | `tdd_gate.py` + `test_provenance_guard.py` | exit 0/1, **advisory (non-blocking)** |

> **Clarification:** Local hooks = **Fast Advisory** (warn, never block offline work).  
> **Hard Fail-Closed Gates** = GitHub Actions CI (`ci.yml`, `ai_cicd.yml`) + Pre-merge checks.

---

### 5.8 Phase 7: CI/CD Verification

**System:** `.github/workflows/ai_cicd.yml`, `ci.yml`, `gitleaks.yml`  
**AI Does:** Code review, security audit, static analysis

| Workflow / System | Check | Environment |
|---|---|---|
| `ai_cicd.yml` (AI Safety Audit) | `code_reviewer.py --review --use-python` | GitHub Actions CI (Hard Gate) |
| `ci.yml` (Unified CI) | pytest, test provenance, doc sync | GitHub Actions CI (Hard Gate) |
| `gitleaks.yml` | Secret scan | GitHub Actions CI (Hard Gate) |
| `code-review.yml` (Agent-based code review) | Agent review | GitHub Actions CI (Hard Gate) |

---

### 5.9 Phase 8: Post-Deployment TDD

**System:** `post-deploy-tdd.yml`  
**AI Does:**
- **Team Red:** attack simulation (`redteam_attack.py`)
- **Team Blue:** validation (`blueteam_validate.py`)
- **Auto-create `intent.md` / `ATOMIC_TICKET.md` on failure** → feed back to Phase 1

**Human:** Does not write (but triage escalation from auto-generated tickets)

---

### 5.10 Phase 9: Release & Production

**System:** `dod-production-gate.yml`, `deploy-render.yml`, `deploy-vercel.yml`  
**AI Does:**
- Verify DoD criteria (100% test, secrets 0, doc sync)
- Release notes, tag, push, worktree clean
**Human:** HITL approval (release, data safety, model promotion)

| Step | Workflow | Trigger Mode |
|---|---|---|
| DoD verification | `dod-production-gate.yml` | GitHub Actions CI (Hard Gate) |
| HF Docker deploy | `deploy-render.yml` | Manual dispatch (Human) |
| Vercel deploy | `deploy-vercel.yml` | Manual dispatch (Human) |

---

### 5.11 Phase 10: Autonomous Maintenance & Feedback Loop ⭐ *NEW*

**System:** `post-deploy-tdd.yml` → auto-generate intake artifacts  
**Closed Loop:**
1. Production anomaly detected (Red/Blue success, monitoring alert, user report)
2. Autonomous diagnosis → root cause analysis
3. Synthesize `intent.md` or new `ATOMIC_TICKET.md` with full audit trail
4. Feed back to **Phase 1 (Intake)** automatically
5. Orchestrator picks up, runs through SDLC with full context

> **Metrics tracked:** Cost per Attempt, Verification Tax, Signal-to-Noise, Post-Deploy Escape Rate (see Appendix)

---

## 6. Verification & Security Scan Flow

### 6.1 When Code Review + Security/Static Scan is Verified

| Stage | Tool / Hook | What is Checked | Mode |
|---|---|---|---|
| **Local (pre-commit)** | `pre-commit` hook | Test provenance, Jira label | **Advisory (non-blocking, read-only)** |
| **Local (pre-push)** | `pre-push` hook | TDD state, provenance, risk-tier | **Advisory (non-blocking, read-only)** |
| **GitHub Actions CI** | `ai_cicd.yml` | `code_reviewer.py --review --use-python` | **Security audit + AST + static scan (Hard Gate)** |
| **GitHub Actions CI** | `ci.yml` | pytest, test provenance, doc sync | **Unified CI (Hard Gate)** |
| **POST-Deploy** | `post-deploy-tdd.yml` | Team Red + Team Blue | **Production-like (Hard Gate)** |
| **Release Gate** | `dod-production-gate.yml` | DoD verification + HITL | **Release gate (Hard Gate + HITL)** |

---

## 7. Diagram: SDLC Flow with AI

```plantuml
@startuml
skinparam backgroundColor #1B2430
skinparam defaultFontName "Arial"
skinparam roundcorner 12
skinparam ActorBackgroundColor #2E4A6B
skinparam ActorFontColor #FFFFFF
skinparam BoxBackgroundColor #3A4A62

title HoroConsultant SDLC Lifecycle (Hooks + CI + Release Gate + Production + Maintenance Loop)

rectangle "SDLC Lifecycle Totality" as SDLC {
  box "🖥️ LOCAL (Developer Mac)" AIS {
    participant "BA\n(business_analyst /\nba_intake)" as BA
    participant "QA\n(qa_tester)" as QA
    participant "PRE-COMMIT" as PRE_COMMIT
    participant "PRE-PUSH" as PRE_PUSH
    participant "Developer\n(developer)" as DEV
  }

  box "📡 GITHUB ACTIONS CI" AIS {
    participant "CI\n(Unified CI)" as CI
    participant "AI_CICD\n(AI Safety Audit)" as AICI
    participant "JIRA-GOV\n(jira-governance)" as JIRA_GOV
  }

  box "🧪 POST-DEPLOY TDD" AIS {
    participant "TEAM RED\n(attack simulation)" as TEAM_RED
    participant "TEAM BLUE\n(validation)" as TEAM_BLUE
  }

  box "🔄 MAINTENANCE LOOP" AIS {
    participant "AUTO-DIAGNOSE\n(root cause)" as DIAGNOSE
    participant "INTENT GENERATOR\n(intent.md / ATOMIC_TICKET.md)" as INTENT_GEN
  }

  box "🚪 RELEASE GATE (dod-production-gate.yml)" AIS {
    participant "ORCH\n(orchestrator)" as ORCH
    participant "HITL" as HITL
    participant "DEVOPS" as DEVOPS
  }

  box "🏭 PRODUCTION" AIS {
    participant "HF Docker\npphothidaen/horoconsultant-core-backend\n(sdk: docker)" as HF_SPACE
    participant "Vercel\nhttps://horo-consultant-psi.vercel.app" as VERCEL
  }

  participant "TDD GATE\n(tdd_gate.py)\nTDD RED->GREEN->Review->Done" as TDD_GATE
  participant "PROVENANCE GUARD\n(test_provenance_guard.py)" as PROV_GUARD
  participant "DOC SYNC\n(run_doc_sync.sh)" as DOC_SYNC
  participant "CODE REVIEW\n(code_reviewer.py)" as CODE_REV
  participant "SECRET SCAN" as SEC_SCAN
  participant "POST-COMMIT CHECK\n(post_commit_check.py)" as POST_CHECK
  participant "ADR CHECK\n(docs/adr/)" as ADR_CHECK
}

BA -> QA: 9-Dim grill specs -> ATOMIC_TICKET.md / plans/plan.md
BA -> QA: ticket READY (agent-* label)

QA -> ADR_CHECK: Check ADR exists for Tier 3 changes
ADR_CHECK -> QA: Pass / Block (fail-closed)

QA -> TDD_GATE: Integration tests first (Red)
TDD_GATE -> TDD_GATE: Backlog -> TDD RED (failing integration test)

QA -> TDD_GATE: Unit tests (Red)
TDD_GATE -> TDD_GATE: TDD RED (Unit) -> TDD GREEN
TDD_GATE -> PROV_GUARD: test provenance verified TEST_BASELINE_VERIFIED

QA -> PRE_COMMIT: commit (test_provenance_guard.py + jira_label_gate.py)
PRE_COMMIT -> PRE_COMMIT: advisory, console only (exit 0/1, non-blocking)

DEV -> TDD_GATE: source code (Test-Baseline trailer)
TDD_GATE -> TDD_GATE: TDD GREEN -> Review

QA -> PRE_PUSH: push (tdd_gate.py + test_provenance_guard.py)
PRE_PUSH -> PRE_PUSH: per-commit coverage, risk-tier detection

DEV -> JIRA_GOV: PR open (KAN-NN prefix) Jira sync
JIRA_GOV -> JIRA_GOV: PR title regex, exit on failure, sync Issue: Review

DEV -> CI: push / PR (feature branch)
DEV -> AICI: push / PR
AICI -> AICI: code_reviewer.py --review --use-python\nsecurity audit, AST, secret scan
CI -> CI: test_provenance_guard.py verify-pr\nconfig drift detection\ndoc sync (run_doc_sync.sh)

TEAM_RED -> TEAM_RED: attack simulation (redteam_attack.py)
TEAM_BLUE -> TEAM_BLUE: validation (blueteam_validate.py)
TEAM_RED -> TEAM_BLUE: parallel + Jira auto-create on failure

TEAM_BLUE -> DIAGNOSE: auto-diagnose root cause
DIAGNOSE -> INTENT_GEN: synthesize intent.md / ATOMIC_TICKET.md
INTENT_GEN -> BA: feedback to Phase 1 (Intake)

TEAM_BLUE -> DEVOPS: evidence bundle (release notes, tag, push, clean worktree)
DEVOPS -> ORCH: automated review (DoD verification)
ORCH -> ORCH: 100% tests green, secrets 0, tag + push + worktree clean
ORCH -> HITL: HITL approval (release, data safety, model promotion)
HITL --> DEVOPS: approve / reject

DEVOPS -> HF_SPACE: HF Docker deploy (sdk: docker) rollback revision record
DEVOPS -> VERCEL: Vercel deploy gateway/API
HF_SPACE -> VERCEL: full path: Vercel -> Render -> HF Space
DEVOPS -> ORCH: 100% DONE ticket complete, archive plans (22-rule)
@enduml
```

---

## 8. Conclusion

AI covers code writing, testing, code review, security scan, and the entire release pipeline. Humans only decide 3 points: **scope/priority**, **quality approval**, **release authorization** — the whole system is fail-closed through multiple layers of gates.

---

## 9. Appendix — References

### 9.1 Systems (Files & Workflows)

| Check | File/Workflow | Line/Trigger |
|---|---|---|
| AI code implementation | `developer` specialist | AGENTS.md |
| AI test-first | `qa_tester`, `tdd_gate.py` | HOWTO.md 3.13 |
| AI code review | `code_reviewer.py` | ai_cicd.yml, ci.yml |
| AI security scan | `code_reviewer.py --review` | ai_cicd.yml |
| AI pre-commit gate | `pre-commit` hook | scripts/pre-commit |
| AI pre-push gate | `pre-push` hook | scripts/pre-push |
| AI post-commit verify | `post_commit_check.py` | scripts/post_commit_check.py |
| AI post-deploy TDD | `post-deploy-tdd.yml` | .github/workflows/ |
| ADR gate | `docs/adr/` | tdd_gate.py (Tier 3) |

### 9.2 CI/CD Systems

| System | Trigger | Environment |
|---|---|---|
| Unified CI (ai_cicd.yml) | push / PR | **CI (GitHub Actions)** |
| Unified CI (ci.yml) | push / PR | **CI (GitHub Actions)** |
| Jira Governance (jira-governance.yml) | pull_request / push | **CI (GitHub Actions)** |
| Post-deploy TDD | manual | **Production** |
| Release Gate (dod-production-gate.yml) | manual | **Release** |
| Secret scan (gitleaks.yml) | push / PR | **CI (GitHub Actions)** |

### 9.3 AI-SDLC Governance & ROI Metrics ⭐ *NEW*

| Metric | Definition | Target | Measurement Point |
|---|---|---|---|
| **Cost per Attempt / Completed Ticket** | Token cost + agent loops per ticket to pass `tdd_gate.py` | < $0.50/ticket | `tdd_gate.py` + token ledger |
| **Verification Tax (PR Review Time)** | Human minutes spent reviewing/approving at HITL gates | < 15 min/PR | GitHub PR timestamps |
| **Signal-to-Noise Ratio (AI Reviewer)** | `code_reviewer.py` true positives / (true positives + false positives) | > 80% | Reviewer feedback log |
| **Post-Deploy Escape Rate** | Issues caught by Team Red/Blue or Production / Total issues | < 5% | Post-deploy + incident log |
| **Retry Loop Count** | Agent fix iterations before human escalation | ≤ 3 retries | Agent execution logs |
| **Tier Distribution** | % tickets by Tier 1/2/3 | Tier 1 > 40% | Jira labels + branch naming |

### 9.4 Retry Limits & Cost Governance ⭐ *NEW*

| Component | Max Retries | Escalation | Cost Cap |
|---|---|---|---|
| `qa_tester` (TDD Red→Green) | 3 | Escalate to `lead_ba` + Human | 50K tokens |
| `developer` (Implementation) | 3 | Escalate to `code_reviewer` + Human | 100K tokens |
| `code_reviewer.py` (Layer 1) | 2 (re-scan) | Human Layer 2 mandatory | 20K tokens |
| Post-deploy Red/Blue | 1 (re-run) | Immediate Human triage | 30K tokens |

> **Hard Rule:** If an Agent loops beyond `MAX_RETRIES` → **Stop immediately**, create a Jira ticket with `ESCALATION` label → Human decides.

### 9.5 Industry References

| Standard | Reference | Application in AI-SDLC |
|---|---|---|
| **NIST SP 800-218 (SSDF)** | Secure Software Development Framework v1.1 | Secure coding practices, vulnerability management, supply chain security — mapped to `code_reviewer.py` Layer 1 gates |
| **NIST AI RMF 1.0** | AI Risk Management Framework | Trustworthy AI principles (valid, reliable, safe, secure, accountable, explainable, privacy-enhanced, fair) — mapped to HITL gates and Red/Blue testing |
| **ISO/IEC 42001:2023** | AI Management System | AI governance, risk assessment, lifecycle management — mapped to ADR governance and Tier 3 approval |
| **OWASP Top 10 for LLM** | OWASP LLM Top 10 (2025) | Prompt injection, insecure output handling, excessive agency — mapped to `code_reviewer.py` secret scan and boundary checks |
| **SLSA (Supply-chain Levels for Software Artifacts)** | SLSA v1.0 | Build integrity, provenance, hermetic builds — mapped to `test_provenance_guard.py` and provenance manifests |

---

*Report generated 2026-10-30.  Version: v1.0.0 · Git SHA: ae2269d87f000b651a971300c0c3b60195791279  Platform: macOS (Apple Silicon) · Git: pphothidaen/HoroConsultant · CI: GitHub Actions*