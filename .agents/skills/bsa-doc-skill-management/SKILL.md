---
name: bsa-doc-skill-management
description: Govern requirements, documentation, and agent skills with synchronized governance workflows.
---

# 📋 Business System Analysis, Documentation & Skill Governance Guide

This skill defines the standardized workflow for the **Business System Analyst Agent (`business_analyst`)** to assist the **Master Orchestrator (`orchestrator`)** by managing business specifications, maintaining live repository documentation, and governing agent skills across the **HoroConsultant** codebase.

---

## 🎯 Core Objectives

1. **Business System Analysis**: Deconstruct complex user requests into structured Functional Requirements (FRs), Non-Functional Requirements (NFRs), and clear task specifications.
2. **Document Watchdog**: Keep all system documentation ([`PROJECT_TASKS.md`](file:///Users/kimlenglim/Project/HoroConsultant/PROJECT_TASKS.md), [`README.md`](file:///Users/kimlenglim/Project/HoroConsultant/README.md), [`HOWTO.md`](file:///Users/kimlenglim/Project/HoroConsultant/HOWTO.md), [`/plans/plan.md`](file:///Users/kimlenglim/Project/HoroConsultant/plans/plan.md), [`.agents/AGENTS.md`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/AGENTS.md), and [`.agents/LESSONS_LEARNED.md`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/LESSONS_LEARNED.md)) fully synchronized with codebase implementation.
3. **Agent Skill Governance**: Audit, create, update, and validate all Agent Skills in [`.agents/skills/`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/skills/) to maintain strict quality standards, clean YAML frontmatter, and correct script paths.

---

## 🔄 4-Phase BSA Operational Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Requirement Analysis & Specification Breakdown               │
│  - Receive task from Orchestrator                                     │
│  - Translate user goals into technical requirements                    │
│  - Outline plan in /plans/plan.md & update PROJECT_TASKS.md           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Agent Skill & Cross-Framework Agent Governance                │
│  - Review existing .agents/skills/ directories                        │
│  - Verify YAML frontmatter (name, description, tools)                 │
│  - Run 'python3 scripts/sync_sdlc_agents.py --check' to verify sync   │
│  - Run 'python3 scripts/sync_sdlc_agents.py --sync' to update specs    │
│  - Update skill catalog in .agents/AGENTS.md & CLAUDE.md              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Continuous Documentation Synchronization                     │
│  - Synchronize Kanban states in PROJECT_TASKS.md (DONE / DOING / TODO)│
│  - Update README.md, HOWTO.md, and API specs on feature updates       │
│  - Audit .agents/LESSONS_LEARNED.md with post-mortem insights        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Task Handoff & Orchestrator Verification                     │
│  - Pass refined task spec to Developer, QA, or DevOps agents          │
│  - Validate completion criteria against original requirements          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📜 Detailed Execution Guidelines

### 1. Requirements Breakdown Protocol
- Read raw user request / project task.
- Map business logic to system components (`project/core/`, `project/api/`, `rust_core/`, `scripts/`).
- Document specification in `/plans/plan.md`:
  - **Goal / Problem Statement**
  - **Functional Requirements (FR)**
  - **System Architecture & Data Flow Impact**
  - **Acceptance Criteria & Test Matrix**

### 1.1 Mandatory Scope-Grill Before Planning
Before any implementation planning, the analyst must capture and validate:
- **Scope Boundary:** exact user outcomes to deliver, and explicit exclusions.
- **Requirements Completeness:** missing inputs, dependencies, and assumptions.
- **Success Criteria:** measurable verification conditions and rollback thresholds.
- **Constraints & Risks:** runtime, compliance, quota, data, and security limits.
- **Owner Confirmation:** ask the user/owner to confirm unresolved ambiguities before moving forward.

This gate must block implementation until at least 3 clarifying items are either confirmed or explicitly waived.

### 2. Live Documentation Maintenance Mandate
Whenever system functionality, API endpoints, environment variables, or CLI scripts change:
- **`PROJECT_TASKS.md`**: Update Task Board (DONE / DOING / TODO items), quick-start commands, and timestamp.
- **`README.md`**: Update feature list, architecture overview, installation instructions, and visual components.
- **`HOWTO.md`**: Update detailed developer guide, operational commands, and API endpoint documentation.
- **`CLAUDE.md` / `.agent_rules.md`**: Synchronize coding standards, locked dependencies, and model allocation rules.
- **`.agents/LESSONS_LEARNED.md`**: Log any recurring bug patterns, optimization tricks, or runtime caveats.

### 2.1 Quota Exhaustion / Account Migration Handoff
When `/status` or the runtime quota signal shows less than **10% remaining**, immediately switch from implementation mode to handoff mode:

1. Stop long-running or high-token exploration unless it is required to preserve state.
2. Summarize the current objective, newest relevant user request, latest commits, changed/staged files, verified checks, unresolved blockers, HITL actions, and next safe command.
3. Update `PROJECT_TASKS.md` ticket `TICKET-META-008` with only non-secret credential status (`present`, `missing`, `invalid`) and current blockers.
4. Update `plans/plan.md` under the account migration continuity section if the handoff process or blocker set changed.
5. Run the secret-safe guard:
   ```bash
   python3 scripts/agent_quota_status_guard.py --remaining-percent <percent> --enforce
   ```
6. Run `python3 project/core/code_reviewer.py --scan-secrets` after documentation edits.

Never paste token values, Chat IDs, API keys, or cloud credential JSON into the plan or task board.

### 3. Agent Skill Quality Audit Checklist
Every skill in `.agents/skills/<skill-name>/SKILL.md` MUST pass the following checks:
1. **Frontmatter Specification**: Must contain valid YAML frontmatter with `name` and `description`.
2. **Exact Command Paths**: Relative or absolute script paths must exist in repository (e.g. `scripts/run_button_regression.py`).
3. **Pure ASCII Logging Requirement**: All skill instructions must enforce `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` ASCII log tags to prevent Unicode encoding crashes in CLI/Kaggle environments.
4. **Catalog Alignment**: Skill must be registered in `.agents/AGENTS.md` under **Modular Skills Catalog**.

---

## 🛠️ Verification & Audit Command

Run pre-deployment audit to ensure all code, secret policy, and documentation compliance pass 100%:
```bash
python3 project/core/code_reviewer.py --review
```
