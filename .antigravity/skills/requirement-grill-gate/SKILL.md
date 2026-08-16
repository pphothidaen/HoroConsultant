---
name: requirement-grill-gate
description: "Pre-plan 9-dim grill gate, block unconfirmed scope, and decompose sub-agent tickets."
---

# 🔥 Requirement-Grill Gate Skill

> **Purpose**: Proactively interview the user with clarifying questions before every task to establish a crystal-clear, granular scope, blocking all code work until requirements are fully grilled, signed off, and decomposed into agent-specific tickets.  
> **Gate Enforcer**: Orchestrator agent (`orchestrator`) / Requirement Grill Agent  
> **Gate Status Badges**: `✅ APPROVED` · `⚠️ WAIVED` · `🚫 BLOCKED`

---

## 🏛️ Architecture & Process Flow

```
User Request
     │
     ▼
┌────────────────────────────────────────────────────────┐
│               REQUIREMENT-GRILL GATE                   │
│                                                        │
│  Step 1 ─ Context Auto-Scan (Orchestrator)             │
│  Step 2 ─ Grill Interview (9 Dimensions, 1-by-1)       │
│  Step 3 ─ Gate Decision (APPROVED / WAIVED / BLOCKED)  │
│  Step 4 ─ Prepend GRILL REPORT → /plans/plan.md        │
│  Step 5 ─ Decompose Tickets → PROJECT_TASKS.md         │
│  Step 6 ─ Post-Grill Task Flow Tracking Verification   │
└────────────────────────────────────────────────────────┘
     │
     ▼  (only if ✅ APPROVED or ⚠️ WAIVED)
Phase 1: Planning & Implementation Delegation
```

---

## 📋 Step 1 — Context Auto-Scan (Orchestrator Autonomy)

Before prompting the user with questions, the Orchestrator MUST read the codebase and rule files to auto-populate low-risk answers:

| Source File | Data Extracted |
|---|---|
| `/plans/plan.md` | Existing scope baseline, previous architecture decisions |
| `PROJECT_TASKS.md` | Active sprint status, unfinished tickets in `DOING`/`TODO` |
| `.agent_rules.md` | Locked dependencies (`transformers==4.44.2`, `peft==0.12.0`, `accelerate==0.33.0`) |
| `.agents/rules/05-security-privacy.md` | Security and data privacy requirements |
| `.agents/rules/06-secrets-policy.md` | 2-tier secrets policy & Doppler integration |
| `.agents/rules/07-infrastructure-constraints.md` | Infrastructure limits, Fly.io, HF Spaces constraints |
| `project/`, `rust_core/`, `api/` | Impacted code modules and API endpoints |

**Auto-Answer & Tiering Rules**:
- **LOW Risk** (locked dependencies, standard SLA, unchanged infra): Auto-populate and tag as `[AUTO]` in the Grill Report.
- **HIGH Risk** (architecture impact, affected sub-agents, risk & rollback): Auto-populate recommendations from context and ask user to confirm or adjust.
- **CRITICAL Risk** (scope boundaries, acceptance criteria, unconfirmed assumptions, breaking changes): Explicitly ask the user one question at a time using `ask_question`.

---

## 🎯 Step 2 — The 9-Dimension Grill Interview

The Orchestrator conducts an interactive interview asking questions **one at a time**:

### Dimension 1 — Scope Boundary `[CRITICAL]`
- **In-Scope**: Explicit list of features, components, and files to be added or modified.
- **Out-of-Scope**: Explicit exclusions (what must NOT be touched or refactored).
- **Interface Stability**: Public APIs, CLI commands, or schemas that must remain backward-compatible.

### Dimension 2 — Requirement Delta `[HIGH]`
- **Deltas**: What changed compared to the previous sprint/plan in `plans/plan.md`.
- **Deprecations**: Any deprecated code or dead code to be removed per the Migration Dead-Code Cleanup Mandate.

### Dimension 3 — Acceptance Criteria `[CRITICAL]`
- **Measurable Thresholds**: Every deliverable must have at least one testable acceptance criterion (e.g. 100% pytest pass rate, zero secret leaks, specific API status 200).
- **Verification Mapping**: Map each criterion to its test runner (`pytest`, `scripts/run_button_regression.py`, `scripts/run_e2e_screenshots.py`, or manual review).

### Dimension 4 — Constraint Checks `[HIGH]` (Auto-Scanned + Confirmed)
- **Dependency Locks**: Strict verification that locked versions (`transformers==4.44.2`, `peft==0.12.0`, `accelerate==0.33.0`) are respected.
- **Secrets Policy**: Adherence to 2-Tier Priority Secrets Policy (`.agents/rules/06-secrets-policy.md`).
- **Kaggle Accelerator Lock**: Confirmation that `kernel-metadata.json` accelerator (`NvidiaTeslaT4`) is untouched.
- **Pure ASCII Logging**: Subprocess log outputs strictly follow `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.

### Dimension 5 — Architecture & Sub-Agent Impact `[HIGH]`
- **Assigned Agents**: Identify which sub-agents are required (`orchestrator`, `developer`, `qa_tester`, `devops`, `domain_master`).
- **Dependency Graph**: Specify execution sequence (e.g. Orchestrator Plan → Developer Code → QA Test → DevOps Release → Code Reviewer Audit).
- **Sync Requirement**: Check if agent definitions or skills require `python3 scripts/sync_sdlc_agents.py --sync` and `python3 scripts/sync_codex_agents.py --sync`.

### Dimension 6 — Assumption Register `[CRITICAL]`
- **Identification**: Uncover unverified assumptions in the user request.
- **Classification**: Tag each item as `[CONFIRMED]`, `[PENDING-OWNER]`, or `[WAIVED]`.
- **Gate Blocker**: Any unresolved `[PENDING-OWNER]` item blocks the gate unless explicitly waived.

### Dimension 7 — Risk Assessment & Rollback Strategy `[HIGH]`
- **Failure Modes**: Top failure risks (e.g. test breakage, deployment timeout, PyO3 compilation error).
- **Rollback Strategy**: Git commit revert plan, env rollback, or feature flag toggle.

### Dimension 8 — Token & Cost Budget Strategy `[HIGH]`
- **Model Routing**: Ensure high-reasoning models (`Claude 3.7 Sonnet` / `Gemini 3.6 Flash High`) handle planning/grilling, while execution delegates to efficient models (`DeepSeek-V3` / `Gemini 3.6 Flash Standard` / `Gemini 3.5 Flash-Lite`).
- **Log Trimming**: Mandate QA/DevOps log filtering to conserve token quota.

### Dimension 9 — Metaphysics & Domain Engine Check `[HIGH]`
- **Domain Scope**: Does this task touch BaZi (`bazi-calculator`), Zi Wei Dou Shu, Qi Men Dun Jia, Da Liu Ren, I Ching, Feng Shui, Western Astro, or Vedic Astro?
- **Canonical Alignment**: Textual validation against canonical classics (`滴天髓`, `子平真詮`, `煙波釣叟歌`, `協紀辨方書`).
- **HITL Routing**: Determine if conflicting interpretations need routing to the HITL Review Queue (`project/hitl_router.py`).

---

## 🚦 Step 3 — Gate Decision & Enforcement

The Orchestrator evaluates the gate status:

| Gate Status | Trigger Condition | SDLC Action |
|---|---|---|
| ✅ **APPROVED** | All CRITICAL dimensions answered + all `[PENDING-OWNER]` items resolved | Proceed to Step 4, 5, 6 and Phase 1 Planning |
| ⚠️ **WAIVED** | Non-critical questions skipped with explicit user confirmation | Proceed with logged waivers in GRILL REPORT |
| 🚫 **BLOCKED** | Any CRITICAL dimension unanswered OR unconfirmed `[PENDING-OWNER]` assumption | **HALT EXECUTION**. Do NOT assign Phase 2 implementation |

---

## 📄 Step 4 — Write GRILL REPORT to `/plans/plan.md`

Prepend the structured report at the top of `/plans/plan.md`:

```markdown
---
## 🔥 GRILL REPORT — <TASK_TITLE>
**Date**: <ISO-8601 timestamp>  
**Grilled By**: orchestrator  
**Gate Status**: ✅ APPROVED | ⚠️ WAIVED | 🚫 BLOCKED  

### D1 — Scope Boundary
- **IN**: ...
- **OUT**: ...

### D2 — Requirement Delta
- **Changed**: ...
- **Cleaned Up (Dead Code)**: ...

### D3 — Acceptance Criteria
| # | Criterion | Verification Tool | Responsible Agent |
|---|---|---|---|
| 1 | ... | pytest / script / UI | qa_tester |

### D4 — Constraints & Safeguards
- Locked Deps: Confirmed unchanged
- Secrets: Doppler Tier-2 compliant
- Kaggle Accelerator: Locked (NvidiaTeslaT4)
- Pure ASCII Logging: Enforced

### D5 — Sub-Agent Allocation & Dependencies
- Assigned Sub-Agents: `orchestrator`, `developer`, `qa_tester`, `devops`, `domain_master`
- Dependency Chain: Plan → Dev → QA → DevOps → Review

### D6 — Assumption Register
| # | Assumption | Status |
|---|---|---|
| 1 | ... | [CONFIRMED] / [WAIVED] |

### D7 — Risk & Rollback
- Risk: ...
- Rollback: `git revert HEAD` / config rollback

### D8 — Token Efficiency Strategy
- Orchestrator: High Reasoning
- Developer / QA: Standard / Flash-Lite with Log Trimming

### D9 — Metaphysics Domain Alignment
- Engines Involved: ...
- HITL Review Required: Yes / No

### ⚠️ Waivers (if any)
- None

### 🚫 Blockers (if any)
- None
---
```

---

## 🎫 Step 5 — Deconstruct into Sub-Agent Tickets in `PROJECT_TASKS.md`

Upon achieving `✅ APPROVED` or `⚠️ WAIVED`, the Orchestrator MUST append a new **Sprint / Session Block** in `PROJECT_TASKS.md` containing dedicated, specialized tickets for each assigned sub-agent:

```markdown
## 🚀 SPRINT: <Sprint Name / Goal Title> — <Date>
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-001` | `orchestrator` | Architecture Blueprint & Spec Finalization | TODO | None |
| `TICKET-002` | `developer` | Code Implementation & Unit Tests | TODO | `TICKET-001` |
| `TICKET-003` | `qa_tester` | E2E & Regression Suite Verification | TODO | `TICKET-002` |
| `TICKET-004` | `devops` | Release Packaging & Environment Audit | TODO | `TICKET-003` |
| `TICKET-005` | `code_reviewer` | Pre-Deploy Audit & Post-Deploy E2E Check | TODO | `TICKET-004` |

---

### 🎫 TICKET-001 | `orchestrator` | [STATUS: TODO]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-002`  
#### Detailed Instructions
1. Finalize `/plans/plan.md` with complete technical specifications.
2. Verify dependency constraints and agent tool configurations.
#### Acceptance Criteria
- [ ] `/plans/plan.md` complete and signed off.
- [ ] Task handoff to `developer` initiated.

---

### 🎫 TICKET-002 | `developer` | [STATUS: TODO]
**Priority**: CRITICAL  
**Depends On**: `TICKET-001`  
**Blocks**: `TICKET-003`  
#### Detailed Instructions
1. Implement features according to technical specifications in `project/`, `rust_core/`, or `api/`.
2. Follow Pure ASCII logging standard (`[OK]`, `[ERROR]`, `[INFO]`).
3. Remove dead code / legacy functions as mandated.
#### Acceptance Criteria
- [ ] Source code implemented without syntax/lint errors.
- [ ] Module inline documentation completed.

---

### 🎫 TICKET-003 | `qa_tester` | [STATUS: TODO]
**Priority**: CRITICAL  
**Depends On**: `TICKET-002`  
**Blocks**: `TICKET-004`  
#### Detailed Instructions
1. Run pytest suite: `python3 -m pytest -v --ignore=project/kaggle_kernel`.
2. Run UI button regression suite: `python3 scripts/run_button_regression.py`.
3. Run Playwright E2E screenshots: `python3 scripts/run_e2e_screenshots.py`.
4. Provide trimmed ASCII log snippets for any failures.
#### Acceptance Criteria
- [ ] 100% test pass rate across all suites.

---

### 🎫 TICKET-004 | `devops` | [STATUS: TODO]
**Priority**: HIGH  
**Depends On**: `TICKET-003`  
**Blocks**: `TICKET-005`  
#### Detailed Instructions
1. Audit environment variables (`.env`, `.env.production`).
2. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
3. Verify HF Space publishing payload: `python3 scripts/publish_space_hf.py --dry-run`.
#### Acceptance Criteria
- [ ] Zero secret leaks detected.
- [ ] Deploy payload dry-run succeeds.

---

### 🎫 TICKET-005 | `code_reviewer` / `orchestrator` | [STATUS: TODO]
**Priority**: CRITICAL  
**Depends On**: `TICKET-004`  
**Blocks**: None (Delivery Gateway)  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Ensure status is `READY_FOR_PROD`.
3. Post-deployment verification and final summary delivery.
#### Acceptance Criteria
- [ ] Status `READY_FOR_PROD` verified.
- [ ] Live docs updated and synchronized.
```

---

## 🔍 Step 6 — Post-Grill Task Flow Tracking Verification

The Orchestrator acts as the continuous Task Manager to guarantee work flows seamlessly to completion:

1. **Active Assignment Guard**: Before dispatching work to a sub-agent, the Orchestrator updates the ticket from `TODO` to `DOING`.
2. **Handoff Verification**: When a sub-agent finishes its task, it returns results to Orchestrator. The Orchestrator verifies output against the ticket's Acceptance Criteria and updates ticket to `DONE`.
3. **Blocker Escalation**: If a sub-agent hits an error, the ticket is marked `BLOCKED`, and the Orchestrator bounces the bug report back to the responsible agent (e.g. QA fail → Developer fix).
4. **End-to-End Closure**: No goal is marked complete until all sprint tickets reach `DONE` and post-deploy E2E verification passes 100%.

---

## ⚡ Quick Reference

- **Mandatory Trigger**: Before any planning or code modification.
- **Gate Controller**: `orchestrator`
- **Output Artifacts**:
  - GRILL REPORT in `/plans/plan.md`
  - Specialized Sub-Agent Tickets in `PROJECT_TASKS.md`
- **Hard Rule**: Strict blocking if CRITICAL dimensions or assumptions are unconfirmed.
