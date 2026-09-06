---
name: orchestrator-delegation
description: Coordinate bounded work across specialist lanes with ticket, lane, and context bindings.
owner: orchestrator
responsibility: multi-agent-orchestration
responsible_agents:
  - orchestrator
  - default
  - hermes
---

# Orchestrator Delegation Skill

Coordinate bounded work across specialist lanes with atomic task declaration and strict context bindings.

## Purpose

The orchestrator manages intake, decomposition, specialist selection, context binding, scheduling, and evidence collection. Implementation, QA, review, and release actions are delegated to designated specialist subagents.

## Mandatory Delegation Protocol

Before dispatching any subagent, the orchestrator MUST bind the complete resolution context:

### 1. Atomic Ticket & Lane Declaration
- Break down objectives into atomic tickets in `atomic_tasks.md` with explicit IDs (`TICKET-<DOMAIN>-<NUM>`).
- Assign a distinct `lane_id` (e.g. `TICKET-<DOMAIN>-<NUM>-<LANE>`) for every parallel or sequential execution unit.
- Enforce strict single-editor file/module resource ownership to prevent concurrent write conflicts.

### 2. Context & Security Identity Binding
Every dispatch must bind the full security identity validated via `scripts/resolve_agent_context.py`:
- **Ticket ID & Lane ID**: Pinned identifiers matching approved context entries.
- **Approved-Context Digest**: SHA-256 digest of the approved ticket context definition.
- **Role, Actions & All Paths**: Explicit declaration of the agent role, permitted actions, and all touched paths.
- **Resolver Result**: Resolved capability allowlist, active closures, and effective toolsets.
- **Authority Constraint**: Generated mirrors and filesystem mtimes are never authority; canonical `.agents/` definitions are the sole authority.

### 3. Specialist Role Mapping
Select the most specific role matching the ticket's technical layer:
- `business_analyst`: Specifications, requirements decomposition, live docs sync.
- `developer`: Code writing, module implementation, bug remediation.
- `qa_tester`: Test design, regression verification, test-provenance tracking.
- `devops`: Infrastructure, deployment gates, release verification.
- `code_reviewer`: Pre-deployment read-only code review, security audits.
- `ux_ui_designer`: Color palettes, design tokens, accessibility auditing.
- Metaphysics Masters: Canonical metaphysical reasoning grounded in deterministic tools.

### 4. Fail-Closed Validation
Any subagent invocation missing a declared Ticket ID, Lane ID, approved-context digest, or resolver result is strictly invalid and fails closed (`BLOCKED: UNBOUND_SPECIALIST_OR_CONTEXT`).

## Handoff Contract Template

Every delegated lane prompt must include:
```text
Task: <TICKET-ID> - <Title>
Lane ID: <LANE-ID>
Role: <Specialist-Role>
Approved Context Digest: <SHA-256>
Actions: [<action-1>, <action-2>]
Touched Paths: [<path-1>, <path-2>]
Resolved Skills: [<skill-1>, <skill-2>]
Ownership: <Files/Directories>
Boundary: Strictly read-only outside assigned ownership.
Instruction: Load assigned skills dynamically via `view_file` at Step 1. Work only within assigned ownership.
Stop Condition: DONE with evidence, BLOCKED with reason, or NEEDS_HITL.
```

## Reporting Protocol

- All reports must use pure ASCII logs only:
  - `[OK]`: Subagent dispatched with verified context binding.
  - `[ERROR]`: Unbound context or unauthorized capability detected.
  - `[WARNING]`: Suboptimal lane partitioning identified.
  - `[INFO]`: Delegation receipt recorded.
