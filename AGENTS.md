# HoroConsultant — Codex Instructions

## Codex compatibility boundary

- `.agents/` and `.antigravity/` remain the legacy multi-agent configuration. Do not rename, delete, or manually rewrite those definitions for Codex work.
- `.agents/skills/*/SKILL.md` are native Codex skills and are discovered from this repository.
- `.agents/agents/*/agent.json` is the compatibility-layer source. `.codex/agents/*.toml` is generated output and must not be edited manually.
- After changing legacy agent definitions, skills, Claude rules, or routing config, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`. Use `python3 scripts/sync_ai_agent_ecosystem.py --check` for read-only validation.

## Working with Codex subagents

- Decompose work into atomic tasks/tickets (`ATOMIC_TICKET.md`), select a matching specialist from `.codex/agents/` / Specialist List, and explicitly bind the required modular skills before dispatching. Unbound dispatches fail closed.
- Generated role prompts preserve legacy responsibilities. Provider/model allocations inside those legacy prompts are historical context; each Codex subagent inherits the active Codex model.
- Keep parallel work isolated by file ownership. Do not assign concurrent agents to edit the same file.

### Specialist List & Agent Matrix

| Agent Identifier | Role / Specialty | Primary Focus & Path Ownership | Bound Skills |
| :--- | :--- | :--- | :--- |
| **`orchestrator`** | Coordination & Autonomous Execution | Decomposition, dispatch, gate decisions, conflict resolution | `orchestrator-delegation`, `multi-account-agent-orchestration` |
| **`lead_ba`** (`business_analyst`) | Lead Business Analyst | Master ticket writer (`ATOMIC_TICKET.md`, `plans/plan.md`) | `bsa-doc-skill-management`, `agile-governance` |
| **`ba_intake`** | Intake & 9-Dimension Grill Specialist | Canonical intake interview, scope validation, writes exclusively to `plans/intake/<sprint>.md` | `requirement-grill-gate`, `bsa-doc-skill-management` |
| **`ba_auditor`** | Read-Only Audit & Verification Specialist | Read-only audit of DoR, DoD, test provenance, and evidence receipts | `agile-governance`, `qa-e2e-testing` |
| **`developer`** | Senior Full-Stack Developer | Implementation across assigned module lanes | `sdlc-aisdlc-workflow` |
| **`qa_tester`** | QA Tester & Verification Guard | Test baselines, contract tests, and regression verification (`tests/**`) | `qa-e2e-testing`, `hf-static-release-verification` |
| **`code_reviewer`** | Pre-Deployment Safety Auditor | Security review, secret scan, and AST verification | `qa-e2e-testing`, `hf-static-release-verification` |
| **`devops`** | DevOps & Release Agent | Release tags, packaging, deployment, and environment hygiene | `devops-deployment`, `hf-static-release-verification` |
| **`ux_ui_designer`** | UX/UI Designer & Color Architect | Design tokens, color palettes, UI components | `web-color-design` |
| **`ui_visual_tester`** | UI Visual Tester & Layout Auditor | Multi-viewport screenshot capture and DOM overlap audit | `ui-visual-auditor` |

### 6-Lane Concurrency Architecture

The ecosystem enforces a maximum 6-lane concurrency architecture divided into two operational tiers:

1. **Management Tier (up to 3 lanes)**:
   - `lead_ba`: Master ticket writer and roadmap planner. Sole writer of `ATOMIC_TICKET.md` and `plans/plan.md`.
   - `ba_intake`: Intake & 9-Dimension Grill Gate Specialist. Conducts intake and writes exclusively to `plans/intake/<sprint-or-topic>.md`. Never writes directly to `ATOMIC_TICKET.md` or `plans/plan.md`.
   - `ba_auditor`: Read-only audit and verification specialist. Audits Definition of Ready (DoR), Definition of Done (DoD), test provenance manifests, and evidence receipts. Strictly read-only; never mutates plans or source files.
2. **Parallel Execution Tier (up to 3 concurrent lanes)**:
   - `developer_api`: API Gateway and routing layer. Writable paths: `project/routers/**`, `api/index.js`, `vercel.json`.
   - `developer_core`: Computation and core logic. Writable paths: `project/core/**`, `rust_core/**`.
   - `qa_tester`: Test baselines and verification. Writable paths: `tests/**`, `plans/test_provenance/**`.
3. **Resource Isolation & Path Disjointness**:
   - Strict one-editor-per-resource ownership.
   - All concurrent lanes must have mutually disjoint writable paths.
   - Fail-closed locking: if tasks share files across lane boundaries, execution falls back to sequential execution.

## Project safeguards

- Apply the relevant `.agents/rules/` documents and skills for the task at hand.
- Kaggle synchronization, deployment, publishing, external messages, and secret operations are opt-in: perform them only when the user requests them or the current task requires them.
- Before release claims, run the relevant tests and `python3 scripts/sync_ai_agent_ecosystem.py --check`.
- Plan Completion, Archival & Release Notes Mandate (Core Rule 16 / Rule 22): Whenever all milestones or tickets in an active plan or sprint are executed and verified DONE, archive completed planning artifacts from `plans/` to `plans/archive/YYYY-MM-DD-<sprint-or-release>/`, maintain `/plans/` containing only active/upcoming specifications, and compile/publish `ReleaseNotes.md` with Executive Summary, Architectural Deliverables, Verification Matrix, Milestone Rollup (100% DONE), Live Production Endpoints, and Archived Plans list. Governed by `business_analyst` and `orchestrator`. See `.agents/rules/22-plan-completion-and-release-notes.md`.
