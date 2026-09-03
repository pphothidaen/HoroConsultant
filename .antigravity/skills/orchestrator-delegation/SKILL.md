---
name: orchestrator-delegation
description: Coordinate bounded work across specialist lanes with atomic ticket and skill bindings.
owner: orchestrator
responsibility: multi-agent-orchestration
responsible_agents:
  - orchestrator
  - default
  - hermes
---

# Orchestrator Delegation Skill

Coordinate bounded work across specialist lanes with atomic task declaration and skill bindings.

## Purpose

The orchestrator manages intake, decomposition, specialist selection, skill binding, scheduling, and evidence collection. It delegates all implementation, QA, review, and release actions to designated specialist subagents.

## Mandatory Delegation Protocol

Before dispatching any subagent, the orchestrator MUST perform these four steps:

### 1. Atomic Task / Ticket Declaration
- Break down broad objectives into atomic tickets recorded in `atomic_tasks.md` with explicit IDs (`TICKET-<DOMAIN>-<NUM>`).
- Define exact scope, acceptance criteria, boundaries/exclusions, and stop condition (`DONE`, `BLOCKED`, `NEEDS_HITL`).
- Require single-editor file/module resource ownership to prevent concurrent write conflicts.

### 2. Specialist Selection (Agent Matrix)
Select the most specific role matching the ticket's technical layer:
- **`business_analyst`**: Requirements decomposition, live docs sync, plan governance.
- **`developer`**: Code writing, bug fixes, module implementations.
- **`qa_tester`**: Test suite execution, failure triage, regression verification.
- **`devops`**: Environment checks, release gates, PR merging, deployments.
- **`code_reviewer`**: Pre-deployment safety audit, secret scans, dependency audits.
- **`ux_ui_designer`**: Color design tokens, Five Elements palettes, WCAG contrast.
- **`ui_visual_tester`**: Multi-viewport layout audits, screenshot comparisons.
- **Metaphysics Masters**: Canonical metaphysics domain reasoning and calculations.

### 3. Related Skill Binding
Explicitly bind the required modular skills from the Skills Catalog to the subagent prompt/instructions:
- QA tasks: `[qa-e2e-testing, ai-inference-verifier, hf-static-release-verification]`
- DevOps tasks: `[devops-deployment, hf-static-release-verification, multi-account-agent-orchestration]`
- Developer tasks: `[bazi-calculator, rag-search, sdlc-aisdlc-workflow]`
- BSA tasks: `[bsa-doc-skill-management, agile-governance]`
- UI/UX tasks: `[web-color-design, ui-visual-auditor]`

### 4. Fail-Closed Validation
Any subagent invocation missing a declared Ticket ID, specialist role assignment, or required skill list is strictly invalid and fails closed (`BLOCKED: UNBOUND_SPECIALIST_OR_SKILL`).

## Handoff Contract Template

Every delegated lane prompt must include:
```text
Task: <TICKET-ID> - <Title>
Role: <Specialist-Role>
Required Skills: [<skill-1>, <skill-2>]
Ownership: <Files/Directories>
Boundary: Read-only outside assigned ownership.
Instruction: You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
Stop Condition: DONE with evidence, BLOCKED with reason, or NEEDS_HITL.
```

