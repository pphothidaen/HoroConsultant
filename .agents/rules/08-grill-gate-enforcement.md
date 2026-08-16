# Rule 08: Requirement-Grill Gate & Sub-Agent Task Board Enforcement

## 🎯 Mandatory Requirement-Grill Gate Policy

Before starting any implementation (Phase 2), writing code, or generating new feature plans, the **Master Orchestrator (`orchestrator`)** and **Grill Agent (`requirement-grill-gate`)** MUST execute the proactive requirement-grill interview pass.

---

## 🛡️ Core Rules & Gate Enforcement

1. **Mandatory Proactive Grilling Before Every Task**:
   - The Grill Agent / Orchestrator MUST act as a proactive, thorough requirement interviewer.
   - For every new task, feature request, or architectural modification, the agent MUST proactively ask clarifying questions (covering UI/UX expectations, edge cases, data structures, and acceptance criteria) using `ask_question` or interactive inquiry to achieve the most granular, detailed scope before code execution.
   - Low-risk questions (locked dependencies, standard SLAs) may be auto-answered from codebase context with `[AUTO]` tags.
   - Critical and ambiguous questions MUST be explicitly confirmed with the user.

2. **Strict Blocking Behavior (`🚫 BLOCKED`)**:
   - If any CRITICAL dimension or ambiguous requirement is unresolved and not explicitly waived by the user, the Orchestrator MUST block execution.
   - Delegation to `developer` or writing code while the gate is in `🚫 BLOCKED` status is strictly prohibited.

3. **Structured GRILL REPORT in `/plans/plan.md`**:
   - The grill outcome must be prepended to `/plans/plan.md` with an explicit badge: `✅ APPROVED`, `⚠️ WAIVED`, or `🚫 BLOCKED`.

4. **Decomposition into Sub-Agent Tickets in `PROJECT_TASKS.md`**:
   - Upon gate approval, the Orchestrator MUST create a new Sprint / Session block in `PROJECT_TASKS.md`.
   - Tickets must be partitioned per assigned sub-agent (`orchestrator`, `developer`, `qa_tester`, `devops`, `domain_master`).
   - Each ticket MUST contain:
     - Ticket ID (e.g. `TICKET-001`)
     - Assigned Agent
     - Priority & Dependencies (`Depends On`, `Blocks`)
     - Specialized, detailed step-by-step instructions
     - Measurable Acceptance Criteria
     - Clear Definition of Done

5. **Sub-Agent Workflow Tracking & Handoff Management**:
   - The Orchestrator manages ticket lifecycle transitions: `TODO` → `DOING` → `DONE` (or `BLOCKED`).
   - Sub-agents must execute only their assigned tickets and hand off results back to the Orchestrator.
   - No task or goal is considered complete until all tickets in the sprint block reach `DONE` and post-deploy E2E regression testing passes 100%.
