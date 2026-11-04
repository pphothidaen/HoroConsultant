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

### 1.1 สรุป 1 ประโยค

> **AI ช่วยทุกขั้นตอนของ SDLC ยกเว้นการตัดสินใจสุดท้าย** — AI เขียนโค้ด ตรวจสอบคุณภาพ ตรวจสอบ security ปล่อยไปยัง production แต่มนุษย์ตัดสินใจสุดท้ายใน 3 จุด: **Scope / Priority**, **Quality Acceptance**, **Release Authorization**

### 1.2 ข้อสรุปหลัก

| หัวข้อ | สรุป |
|---|---|
| **AI Covers** | ทุกขั้นตอนตั้งแต่ intake → code → test → review → deploy |
| **Human Authority** | 3 จุด: scope/priority, quality acceptance, release approval (HITL) |
| **Fail-Closed** | ระบบ gate หลายชั้น (pre-commit, pre-push, CI, post-deploy) — **Local hooks = Advisory (non-blocking); CI/Pre-merge = Hard Fail-Closed Gate** |
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

### 3.1 ไว้ดูง่าย: AI ช่วยที่ไหนบ้าง

| ขั้นตอน | AI ทำอะไร | ความน่าเชื่อถือ |
|---|---|---|
| **1. Intake** | `ba_intake`, `lead_ba` — ร่าง ticket, spec, requirement | AI ร่าง, Human ตรวจสอบ scope |
| **2. Branching** | `orchestrator` — แบ่งงาน 6-lane, สร้าง branch | AI สร้าง branch, dispatch |
| **3. TDD (Test-First)** | `qa_tester` + `tdd_gate.py` | เขียน **Integration Tests → Unit Tests** (Red) → Green → manifest |
| **4. Code Implementation** | `developer` | เขียน production code (หลัง TDD GREEN) |
| **5. Code Review** | `code_reviewer.py` — Secret scan, AST audit, **Complexity & Boundary check** | AI ตรวจสอบ Surface (Layer 1) → Human ตรวจสอบ Intent (Layer 2) |
| **6. Pre-commit** | `pre-commit` hook | AI สรุป test provenance, Jira label (Advisory) |
| **7. Pre-push** | `pre-push` hook | AI ตรวจสอบ TDD state, provenance, **Risk-tiered lanes** (Advisory) |
| **8. Post-commit** | `post_commit_check.py` | AI สรุป docs sync, INDEX.md |
| **9. Post-deploy** | `post-deploy-tdd.yml` (Team Red/Blue) | AI attack simulation + validation |
| **10. Maintenance** | **Autonomous feedback loop** | AI สร้าง `intent.md`/`ATOMIC_TICKET.md` ใหม่จาก Production findings |
| **11. Production** | `dod-production-gate.yml` + HITL | AI verify + Human approve |

---

## 4. AI vs Human Decision Matrix

| ขั้นตอน | ระบบที่ใช้ | ใครช่วย | ใครตัดสินใจ |
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

**ระบบ:** `ba_intake`, `lead_ba` (business_analyst)  
**AI ทำ:** ร่าง ticket (ATOMIC_TICKET.md), spec (plans/plan.md), 9-Dim grill  
**มนุษย์ตัดสินใจ:** Scope, priority, business commitment

| ระบบ | AI ทำ | มนุษย์ทำ |
|---|---|---|
| `ba_intake` | 9-Dim grill intake, patterns from Gemini MCP | scope, priority, business commitment |
| `lead_ba` | ลงทะเบียน ticket, ปรับ config | อนุมัติ scope, ตรวจสอบ quality |

---

### 5.1.5 Phase 1.5: Bootstrap & Design Governance (ADR) ⭐ *NEW*

**ระบบ:** `docs/PROJECT.md`, `docs/adr/`  
**AI ทำ:** ร่าง Architecture baseline, Tech stack, Runtime constraints, ADR drafts  
**มนุษย์ตัดสินใจ:** Architectural boundary, system scope, design decisions

| Artifact | Purpose | Owner |
|---|---|---|
| `docs/PROJECT.md` | Architecture baseline, tech stack, runtime constraints, non-functional requirements | Architect / Lead BA |
| `docs/adr/*.md` | Architecture Decision Records — immutable design decisions with context & consequences | Architect + Human approval |
| `tdd_gate.py` pre-check | Validates ADR exists for core changes before allowing TDD RED | Orchestrator (fail-closed) |

> **Rule:** ไม่มี ADR สำหรับ Core Engine / Security / Model Promotion → ไม่ผ่าน TDD Gate (Tier 3)

---

### 5.2 Phase 2: Branch & Dispatch

**ระบบ:** `orchestrator` (Master Orchestrator)  
**AI ทำ:** แบ่ง requirement → atomic tasks, สร้าง branch `feat/KAN-NN-description`, dispatch subagents  
**Risk-Tiered Lanes:**  
- **Tier 1 (Fast-track):** Docs / Config / Trivial Fix → ข้าม TDD เต็มรูปแบบ, ใช้ Linter + Doc Sync + Fast Merge  
- **Tier 2 (Standard):** Feature work → รัน AI-SDLC ปกติ (Integration → Unit → Code → Review)  
- **Tier 3 (Core/Security/Model):** บังคับ Full Cycle + ADR + Red/Blue Simulation + HITL Approval

**ไม่มีมนุษย์:** กระบวนการอัตโนมัติเต็มรูปแบบ

---

### 5.3 Phase 3: TDD (Test-First Development) — **Integration First** ⭐ *UPDATED*

**ระบบ:** `qa_tester` + `tdd_gate.py`  
**AI ทำ:** เขียน **Integration Tests → Unit Tests** (Red) → Green → manifest  
**มนุษย์:** ไม่เขียน test  

**ลำดับที่บังคับ (Enforced by `tdd_gate.py`):**

1. **Integration Tests (Red)** — พิสูจน์การเชื่อมต่อระหว่างโมดูล / End-to-End Business Logic  
2. **Unit Tests (Red)** — ฟังก์ชันระดับรายการ (mock ได้แค่ unit เอง)  
3. **All Tests Green** — รัน pytest ผ่านทั้งชุด  
4. **Provenance Manifest** — `plans/test_provenance/*KAN-XX*.json` (ยกเว้น Tier 1 docs-only)

> **เหตุผล:** ป้องกัน **Shallow Verification** (AI เขียน unit test mock ตัวเองให้ผ่าน แต่ integration พัง)

---

### 5.4 Phase 4: Code Implementation

**ระบบ:** `developer` (Senior Developer)  
**AI ทำ:** เขียน production code (`project/**`)  
**มนุษย์:** ไม่เขียน code  
**เงื่อนไข:** เริ่มเขียน code เฉพาะหลัง TEST_BASELINE_VERIFIED (TDD GREEN)  
**ข้อห้าม:** ไม่แก้ไข test ย้อนหลัง (FROZEN_TEST_CHANGED)

| ลำดับ | สถานะ | ระบบ | หมายเหตุ |
|---|---|---|---|
| 1 | Backlog | `ba_intake` | อยู่ใน ticket |
| 2 | **TDD RED (Integration)** | `qa_tester` | เขียน integration test ล้มเหลวครั้งแรก |
| 3 | **TDD RED (Unit)** | `qa_tester` | เขียน unit test ล้มเหลวครั้งแรก |
| 4 | **TDD GREEN** | `qa_tester` + `tdd_gate.py` | ทดสอบผ่าน + manifest |
| 5 | Review (Layer 1: AI) | `code_reviewer.py` | AST, Secret, Syntax, Complexity |
| 6 | Review (Layer 2: Human) | PR + Human | Intent, Complexity O(n), Boundary, Algorithm |
| 7 | Done | CI | merge + ตรวจสอบ CI |

---

### 5.5 Phase 5: Code Review — **Layered Review** ⭐ *UPDATED*

**ระบบ:** `code_reviewer.py` + GitHub Actions CI  
**AI ทำ (Layer 1 — Surface & Static Filter):**  
- Secret scan (API keys, tokens, private keys)  
- AST syntax audit (null bytes, surrogate encoding, compile check)  
- Kaggle CUDA dependency safety  
- Notebook syntax & dependency lock compliance  
- **Cyclomatic / Cognitive complexity analysis**  
- **Memory retention pattern detection** (streaming vs full-load)  
- **Algorithmic complexity flags** (O(n²) loops, nested iterations)

**มนุษย์ทำ (Layer 2 — Intent & PR Merge Gate):**  
- โค้ดตรงตามเจตนาจริงไหม (Intent alignment)  
- รับโหลดหนักได้ไหม (Load/stress reasoning)  
- เคารพขอบเขตระบบไหม (Boundary respect)  
- ใช้อัลกอริทึมที่เหมาะสมไหม (O(n) vs O(n²))  
- **กด Merge PR** (Orchestrator เตรียม PR, Human กด merge)

> **Rule:** Critical/Regulated code (Tier 3) ต้องมี Human Intent Review ก่อน Merge — ห้ามปล่อยไหลไปรอ Release Gate จุดเดียว

---

### 5.6 Phase 6: Pre-commit & Pre-push Gates

**ระบบ:** `.githooks/pre-commit`, `.githooks/pre-push`  
**AI ทำ:**  
- pre-commit: test provenance verify, Jira label check  
- pre-push: TDD state machine, provenance check, per-commit coverage, **Risk-tier detection**

| ระบบ | ตรวจสอบ | ออกผล |
|---|---|---|
| `.githooks/pre-commit` | `test_provenance_guard.py staged` + `jira_label_gate.py` | exit 0/1, **advisory (non-blocking)** |
| `.githooks/pre-push` | `tdd_gate.py` + `test_provenance_guard.py` | exit 0/1, **advisory (non-blocking)** |

> **Clarification:** Local hooks = **Fast Advisory** (warn, never block offline work).  
> **Hard Fail-Closed Gates** = GitHub Actions CI (`ci.yml`, `ai_cicd.yml`) + Pre-merge checks.

---

### 5.7 Phase 7: CI/CD Verification

**ระบบ:** `.github/workflows/ai_cicd.yml`, `ci.yml`, `gitleaks.yml`  
**AI ทำ:** Code review, security audit, static analysis

| Workflow / ระบบ | สิ่งที่ตรวจสอบ | สภาพแวดล้อม (Environment) |
|---|---|---|
| `ai_cicd.yml` (AI Safety Audit) | `code_reviewer.py --review --use-python` | GitHub Actions CI (Hard Gate) |
| `ci.yml` (Unified CI) | pytest, test provenance, doc sync | GitHub Actions CI (Hard Gate) |
| `gitleaks.yml` | Secret scan | GitHub Actions CI (Hard Gate) |
| `code-review.yml` (Agent-based code review) | Agent review | GitHub Actions CI (Hard Gate) |

---

### 5.8 Phase 8: Post-Deployment TDD

**ระบบ:** `post-deploy-tdd.yml`  
**AI ทำ:**  
- **Team Red:** attack simulation (`redteam_attack.py`)  
- **Team Blue:** validation (`blueteam_validate.py`)  
- **Auto-create `intent.md` / `ATOMIC_TICKET.md` on failure** → feed back to Phase 1

**มนุษย์:** ไม่เขียน (แต่ triage escalation จาก auto-generated tickets)

---

### 5.9 Phase 9: Release & Production

**ระบบ:** `dod-production-gate.yml`, `deploy-render.yml`, `deploy-vercel.yml`  
**AI ทำ:**  
- Verify DoD criteria (100% test, secrets 0, doc sync)  
- Release notes, tag, push, worktree clean  
**มนุษย์:** HITL approval (release, data safety, model promotion)

| ขั้นตอน | Workflow | รูปแบบการ Trigger |
|---|---|---|
| DoD verification | `dod-production-gate.yml` | GitHub Actions CI (Hard Gate) |
| HF Docker deploy | `deploy-render.yml` | Manual dispatch (Human) |
| Vercel deploy | `deploy-vercel.yml` | Manual dispatch (Human) |

---

### 5.10 Phase 10: Autonomous Maintenance & Feedback Loop ⭐ *NEW*

**ระบบ:** `post-deploy-tdd.yml` → auto-generate intake artifacts  
**วงจรปิด (Closed Loop):**  
1. Production anomaly detected (Red/Blue success, monitoring alert, user report)  
2. Autonomous diagnosis → root cause analysis  
3. Synthesize `intent.md` or new `ATOMIC_TICKET.md` with full audit trail  
4. Feed back to **Phase 1 (Intake)** automatically  
5. Orchestrator picks up, runs through SDLC with full context

> **Metrics tracked:** Cost per Attempt, Verification Tax, Signal-to-Noise, Post-Deploy Escape Rate (see Appendix)

---

## 6. Verification & Security Scan Flow

### 6.1 เมื่อไหน ที่มีการตรวจสอบ Code Review + Security/Static Scan

| ช่วงเวลา (Stage) | เครื่องมือ/Hook | สิ่งที่ตรวจสอบ | ลักษณะการทำงาน (Mode) |
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

title HoroConsultant SDLC ライフサイクル (Hooks + CI + Release Gate + Production + Maintenance Loop)

rectangle "SDLC ライフサイクル วงจร totality" as SDLC {
  box "🖥️ LOCAL (Developer Mac)" AIS {
    participant "BA\n(business_analyst /\nba_intake)" as BA
    participant "QA\n(qa_tester)" as QA
    participant "PRE-COMMIT" as PRE_COMMIT
    participant "PRE-PUSH" as PRE_PUSH
    participant "Developer\n(developer)" as DEV
  }

  box "📡 GITHUB ACTIONS CI" AIS {
    participant "CI.yml\n(Unified CI)" as CI
    participant "AI_CICD.yml\n(AI Safety Audit)" as AICI
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
TDD_GATE -> TDD_GATE: TDD RED -> TDD RED (failing unit test)

QA -> TDD_GATE: All tests pass + provenance manifest
TDD_GATE -> TDD_GATE: TDD RED -> TDD GREEN
TDD_GATE -> PROV_GUARD: test provenance verified TEST_BASELINE_VERIFIED

QA -> PRE_COMMIT: commit (test_provenance_guard.py + jira_label_gate.py)
PRE_COMMIT -> PRE_COMMIT: advisory, console only (exit 0/1, non-blocking)

DEV -> TDD_GATE: source code (Test-Baseline trailer)
TDD_GATE -> TDD_GATE: TDD GREEN -> Review

DEV -> CODE_REV: PR open (Layer 1: AI Surface)
CODE_REV -> CODE_REV: secret scan, AST, complexity, memory, boundary
CODE_REV -> HITL: PR ready for Layer 2 (Human Intent Review)
HITL -> DEV: Merge PR (Human clicks merge)

DEV -> PRE_PUSH: push (tdd_gate.py + test_provenance_guard.py)
PRE_PUSH -> PRE_PUSH: per-commit coverage, docs-only exemption (KAN-180), risk-tier

DEV -> JIRA_GOV: PR open (KAN-NN prefix) Jira sync
JIRA_GOV -> JIRA_GOV: PR title regex, exit on failure, sync Issue: Review

DEV -> CI: push / PR (feature branch)
DEV -> AICI: push / PR
AICI -> AICI: code_reviewer.py --review --use-python\nsecurity audit, AST, secret scan, complexity
CI -> CI: test_provenance_guard.py verify-pr\nconfig drift detection\ndoc sync (run_doc_sync.sh)

TEAM_RED -> TEAM_RED: attack simulation (redteam_attack.py)
TEAM_BLUE -> TEAM_BLUE: validation (blueteam_validate.py)
TEAM_RED -> TEAM_BLUE: parallel + Jira auto-create on failure

TEAM_BLUE -> DIAGNOSE: failure evidence bundle
DIAGNOSE -> INTENT_GEN: root cause + audit trail
INTENT_GEN -> BA: new ATOMIC_TICKET.md / intent.md (closed loop)

TEAM_BLUE -> DEVOPS: success evidence bundle (release notes, tag, push, clean worktree)
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

AI ครอบคลุมการเขียนโค้ด, testing, code review, security scan, และ release pipeline ทั้งหมด แต่มนุษย์เพียงตัดสินใจ 3 จุด: **scope/priority**, **quality approval**, **release authorization** — ทั้งระบบ fail-closed ผ่าน gate หลายชั้น โดย **Local hooks = Advisory**, **CI/Pre-merge = Hard Gate** และมี **Maintenance Loop** ปิดวงจรกลับสู่ Intake

---

## 9. Appendix — References

### 9.1 ระบบ (Files & Workflows)

| ตรวจสอบ | ไฟล์/Workflow | ไลน์/Trigger |
|---|---|---|
| AI code implementation | `developer` specialist | AGENTS.md |
| AI test-first (Integration → Unit) | `qa_tester`, `tdd_gate.py` | HOWTO.md 3.13 |
| AI code review (Layer 1 + 2) | `code_reviewer.py` | ai_cicd.yml, ci.yml |
| AI security scan | `code_reviewer.py --review` | ai_cicd.yml |
| AI pre-commit gate | `pre-commit` hook | scripts/pre-commit |
| AI pre-push gate | `pre-push` hook | scripts/pre-push |
| AI post-commit verify | `post_commit_check.py` | scripts/post_commit_check.py |
| AI post-deploy TDD | `post-deploy-tdd.yml` | .github/workflows/ |
| AI maintenance loop | auto-diagnose + intent-gen | post-deploy-tdd.yml |
| ADR governance | `docs/adr/`, `docs/PROJECT.md` | tdd_gate.py pre-check |

### 9.2 ระบบ CI/CD

| ระบบ / Workflow | Trigger | ประเภทสภาพแวดล้อม |
|---|---|---|
| Unified CI (ci.yml) | push / PR | **CI (GitHub Actions) — Hard Gate** |
| AI Safety Audit (ai_cicd.yml) | push / PR | **CI (GitHub Actions) — Hard Gate** |
| Jira Governance (jira-governance.yml) | pull_request / push | **CI (GitHub Actions) — Hard Gate** |
| Post-deploy TDD | manual / schedule | **Production — Hard Gate** |
| Release Gate (dod-production-gate.yml) | manual | **Release — Hard Gate + HITL** |
| Secret scan (gitleaks.yml) | push / PR | **CI (GitHub Actions) — Hard Gate** |

---

### 9.3 AI-SDLC Governance & ROI Metrics ⭐ *NEW*

| Metric | Definition | Target | Measurement Point |
|---|---|---|---|
| **Cost per Attempt / Completed Ticket** | Token cost + agent loops per ticket to pass `tdd_gate.py` | < $0.50/ticket | `tdd_gate.py` + token ledger |
| **Verification Tax (PR Review Time)** | Human minutes spent reviewing/approving at HITL gates | < 15 min/PR | GitHub PR timestamps |
| **Signal-to-Noise Ratio (AI Reviewer)** | `code_reviewer.py` true positives / (true positives + false positives) | > 80% | Reviewer feedback log |
| **Post-Deploy Escape Rate** | Issues caught by Team Red/Blue or Production / Total issues | < 5% | Post-deploy + incident log |
| **Retry Loop Count** | Agent fix iterations before human escalation | ≤ 3 retries | Agent execution logs |
| **Tier Distribution** | % tickets by Tier 1/2/3 | Tier 1 > 40% | Jira labels + branch naming |

---

### 9.4 Retry Limits & Cost Governance ⭐ *NEW*

| Component | Max Retries | Escalation | Cost Cap |
|---|---|---|---|
| `qa_tester` (TDD Red→Green) | 3 | Escalate to `lead_ba` + Human | 50K tokens |
| `developer` (Implementation) | 3 | Escalate to `code_reviewer` + Human | 100K tokens |
| `code_reviewer.py` (Layer 1) | 2 (re-scan) | Human Layer 2 mandatory | 20K tokens |
| Post-deploy Red/Blue | 1 (re-run) | Immediate Human triage | 30K tokens |

> **Hard Rule:** หาก Agent วนลูปเกิน `MAX_RETRIES` → **หยุดทันที** สร้าง Jira ticket พร้อม `ESCALATION` label → Human ตัดสินใจ

---

*Report generated 2026-10-30.  
Platform: macOS (Apple Silicon) · Git: pphothidaen/HoroConsultant · CI: GitHub Actions*