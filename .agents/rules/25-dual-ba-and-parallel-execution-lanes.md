# Rule 25: Dual-BA Architecture & Parallel Execution Lanes

## 1. Dual-BA Operating Model

Lifecycle governance enforces strict separation between intake, lead planning, and audit:

- `ba_intake`: Intake triage & 9-Dimension GRILL Gate. Responsible for initial requirement intake, stakeholder alignment, and draft proposals. Writable ownership strictly scoped to `plans/intake/*`.
- `lead_ba`: Lead Business Analyst (`business_analyst`). Sole authoritative writer of `ATOMIC_TICKET.md` and `plans/plan.md`. Orchestrates sprint roadmaps, decomposes atomic tickets, and approves GRILL reports.
- `ba_auditor`: Read-only verification specialist. Audits Definition of Ready (DoR) and Definition of Done (DoD) conformance without write access to plans or tickets. Publishes audit receipts to `plans/evidence/*`.

## 2. Parallel Execution Lanes (Max 3 Concurrent)

To maximize throughput while preventing race conditions, execution is divided into disjoint lanes:

- `developer_api`: API Gateway & routing layer. Writable paths: `project/routers/**`, `api/index.js`, `vercel.json`.
- `developer_core`: Computation & core logic. Writable paths: `project/core/**`, `rust_core/**`.
- `qa_tester`: Test baselines & verification. Writable paths: `tests/**`, `plans/test_provenance/**`.

## 3. One-Editor-Per-Resource & File Path Disjointness

- **Strict Resource Isolation**: Each file or directory path is owned by exactly one ticket and lane at a time.
- **Path Disjointness**: No two parallel lanes may share writable paths in their active tickets.
- **Fail-Closed Locking**: If any task requires shared files across lane boundaries, execution reverts to sequential single-lane mode until the boundary is clear.

## 4. Concurrency Capacity Ceiling

- **Total Capacity Ceiling**: Maximum 6 concurrent lanes across the ecosystem:
  - Up to 2 BA/Governance lanes (`ba_intake`, `lead_ba`/`ba_auditor`)
  - Up to 3 Parallel Execution lanes (`developer_api`, `developer_core`, `qa_tester`)
  - 1 Operations/Release lane (`devops` / `code_reviewer`)
- **Quota & Memory Protection**: Concurrency must never exceed available token budgets or breach Rule 17 Host Account Preservation.
