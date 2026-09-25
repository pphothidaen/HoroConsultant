# Grill Intake Report: Jira + Hermes + Herdr/Tmux Autonomous Execution System

**Date:** 2026-09-25  
**Owner:** @kimlenglim  
**Intake Lead:** `ba_intake` / `orchestrator`  
**Gate Status:** `APPROVED` (Contract-Locked)  

---

## 1. Executive Summary & Objective

Build a production-grade, fail-closed **Autonomous Agent Execution Platform** combining:
1. **Jira Cloud**: External Single Source of Truth (SSOT) & workflow audit projection.
2. **Hermes Agent**: Central Control Plane, State Machine authority, and Durable Session State Manager.
3. **WorkerRuntime (Hybrid `herdr` on macOS / `tmux` on Linux/CI)**: Ephemeral Execution Process & decoupled execution fabric.
4. **Lease + Monotonic Fencing Token**: Concurrency, replay, and zombie process protection.
5. **Deterministic Evidence Gate**: Schema-validated v1.0 contract bound directly to Jira acceptance criteria.
6. **Security & Prompt Injection Boundary**: Treating all Jira content as untrusted input.

---

## 2. Core Execution Invariants [FROZEN]

- **`INVARIANT-01`**: One Jira ticket may have only one active execution lease.
- **`INVARIANT-02`**: Only the current fencing token may mutate execution state.
- **`INVARIANT-03`**: `DONE` requires validated deterministic evidence.
- **`INVARIANT-04`**: Worker LLM output/prose alone can never authorize `DONE`.
- **`INVARIANT-05`**: An expired lease does not automatically imply successful completion.
- **`INVARIANT-06`**: Runtime backend is selected before spawn and is immutable for that execution.
- **`INVARIANT-07`**: All Jira content (title, description, comments, attachments) is untrusted input.
- **`INVARIANT-08`**: Every execution is recoverable, renewable, or explicitly `BLOCKED`.

---

## 3. Five-Point Architecture Refinements

1. **Worker vs. Control Plane Definition**:
   * `Worker` = Ephemeral / disposable execution process.
   * `Hermes Session / Control Plane` = Durable state, session database, lineage, and authority.
2. **Composite Execution Identity**:
   * Every mutation requires validation against composite key:
     `{execution_id, ticket_id, attempt, lease_id, fencing_token, session_id, worker_id}`
3. **Lease Expiry & Reconciliation State Machine**:
   * `IN_PROGRESS` $\rightarrow$ `LEASE_EXPIRED` $\rightarrow$ `RECONCILING`:
     * Worker alive $\rightarrow$ `RENEW / RECOVER`
     * Worker dead $\rightarrow$ `FENCE`
     * State unclear $\rightarrow$ `RECOVERY_PENDING` $\rightarrow$ `BLOCKED` (with Telegram / Jira alert)
4. **Direct Acceptance Criteria Binding in Evidence Contract**:
   * Evidence requires: `acceptance_test_ids[]`, `acceptance_results[]`, `environment`, `command_receipts[]`, `evidence_timestamp`, `fencing_token`, `attempt`.
5. **D7 Security & Untrusted Input Boundary**:
   * Ingest webhook $\rightarrow$ HMAC authenticate $\rightarrow$ Sanitize & validate $\rightarrow$ Trust boundary $\rightarrow$ DoR Gate $\rightarrow$ Worker.

---

## 4. Nine-Dimension Assessment Matrix

| Dimension | Classification | Decision & Grounded Specification | Evidence State |
| :--- | :--- | :--- | :--- |
| **D1: Scope Boundary** | **CRITICAL** | In-scope: `WorkerRuntime` abstraction, Jira Event-Driven State Machine, Lease & Fencing Token manager, Reconciler loop, Security boundary, Evidence schema validator. Out-of-scope: Direct metaphysical computation engine, unverified auto-deploy to prod. | `[CONFIRMED]` |
| **D2: Requirement Delta** | **HIGH** | Transition from polling script (`sync_jira_hermes.py`) to an Event-Driven Control Plane with webhook support, atomic leases, and idempotent reconciliation. | `[CONFIRMED]` |
| **D3: Acceptance & Stop Conditions** | **CRITICAL** | Deterministic Evidence JSON required for `DONE`. Zero transition on LLM self-prose. Transitions: `TODO` $\rightarrow$ `DOR_CHECK` $\rightarrow$ `CLAIMED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `VERIFYING` $\rightarrow$ `DONE` / `BLOCKED`. | `[CONFIRMED]` |
| **D4: Inputs, Constraints & Dependencies** | **HIGH** | Hybrid Runtime Policy: macOS prefers `herdr` (agent-aware), fallback to `tmux`. Linux/CI uses `tmux`. Pre-spawn immutable selection. Bounded output reads ($\le 30$ lines). | `[CONFIRMED]` |
| **D5: Architecture & Ownership** | **HIGH** | Clear tiering: Jira = Workflow Record; Hermes = Control Plane; Worker = Ephemeral Execution Process; Evidence Gate = DoD Validator. | `[CONFIRMED]` |
| **D6: Assumption Register** | **CRITICAL** | All assumptions around network retries, crash recovery, and multi-tenant leases are bound to fencing tokens. | `[CONFIRMED]` |
| **D7: Risk, Recovery & Security** | **HIGH** | Renewable Lease (15m initial + 1-5m heartbeat). Fencing tokens invalidate zombie workers. Reconciler auto-fences orphans. Untrusted Jira content sanitization boundary. | `[CONFIRMED]` |
| **D8: Budget & Evidence Strategy** | **HIGH** | Context hard cap 256K tokens, `tail_mode: lean`, auxiliary model `gemini-3.1-flash-lite`, Handoff capsules $\le 16\text{ KiB}$ upon quota $< 10\%$. | `[CONFIRMED]` |
| **D9: Domain & HITL Check** | **HIGH** | Risk-Tiered Gate: LOW (Auto-DONE) $\rightarrow$ MEDIUM (Extra tests) $\rightarrow$ HIGH/PROD (Human Approval via Telegram / Jira). | `[CONFIRMED]` |

---

## 5. Schema Contract: Evidence V1.0

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "HermesWorkerEvidenceV1",
  "type": "object",
  "required": [
    "schema_version",
    "execution_id",
    "ticket_id",
    "attempt",
    "lease_id",
    "fencing_token",
    "session_id",
    "worker_id",
    "git_sha",
    "environment",
    "tests",
    "acceptance_checks",
    "command_receipts",
    "timestamp",
    "evidence_hash"
  ],
  "properties": {
    "schema_version": {"type": "string", "enum": ["1.0"]},
    "execution_id": {"type": "string"},
    "ticket_id": {"type": "string"},
    "attempt": {"type": "integer", "minimum": 1},
    "lease_id": {"type": "string"},
    "fencing_token": {"type": "string"},
    "session_id": {"type": "string"},
    "worker_id": {"type": "string"},
    "git_sha": {"type": "string"},
    "environment": {"type": "string"},
    "tests": {
      "type": "object",
      "required": ["total", "passed", "failed", "skipped"],
      "properties": {
        "total": {"type": "integer"},
        "passed": {"type": "integer"},
        "failed": {"type": "integer"},
        "skipped": {"type": "integer"}
      }
    },
    "acceptance_checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["check_id", "status", "detail"],
        "properties": {
          "check_id": {"type": "string"},
          "status": {"type": "string", "enum": ["passed", "failed", "waived"]},
          "detail": {"type": "string"}
        }
      }
    },
    "command_receipts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["command", "exit_code", "stdout_hash"],
        "properties": {
          "command": {"type": "string"},
          "exit_code": {"type": "integer"},
          "stdout_hash": {"type": "string"}
        }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "sha256"],
        "properties": {
          "path": {"type": "string"},
          "sha256": {"type": "string"}
        }
      }
    },
    "timestamp": {"type": "string", "format": "date-time"},
    "evidence_hash": {"type": "string"}
  }
}
```

---

## 6. Atomic Ticket Roadmap (AT-01 to AT-14)

### Phase 1: Core WorkerRuntime & Deterministic Evidence Gate
- **`AT-01`**: `WorkerRuntime` Unified Interface & `ExecutionIdentity` Contract (`RuntimeBackend` ABC: `detect`, `health`, `spawn`, `attach`, `send`, `read`, `status`, `terminate`, `collect_metadata`).
- **`AT-02`**: `herdr` Adapter Implementation (`HerdrRuntimeAdapter` on macOS with agent-aware state tracking).
- **`AT-03`**: `tmux` Adapter & Fallback Implementation (`TmuxRuntimeAdapter` with bounded capture $\le 30$ lines).
- **`AT-04`**: Platform-Aware Pre-Spawn Selection & Immutable Execution Locking (`RuntimeSelector`).
- **`AT-05`**: Evidence Schema v1.0 Definition & JSON Schema Manifest.
- **`AT-06`**: Deterministic Evidence Validator & Test Provenance Guard.

### Phase 2: Lease Management, Fencing & Jira State Machine
- **`AT-07`**: Composite Execution Identity & Renewable Lease Manager (15m initial TTL + 1-5m heartbeat).
- **`AT-08`**: Monotonic Fencing Token Enforcement & Mutation Guard.
- **`AT-09`**: Jira Event-Driven State Machine (`TODO` $\rightarrow$ `DOR` $\rightarrow$ `CLAIMED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `VERIFYING` $\rightarrow$ `DONE`/`BLOCKED`).
- **`AT-10`**: Background Reconciler & Orphan Worker Reaper (`RECONCILING` $\rightarrow$ `RENEW`/`FENCE`/`BLOCKED`).

### Phase 3: Security Boundary & Resilience
- **`AT-11`**: Webhook Idempotency & Delivery Coalescing / Deduplication.
- **`AT-12`**: Risk-Tiered Approval Gate (`LOW` $\rightarrow$ auto; `MEDIUM` $\rightarrow$ tests; `HIGH/PROD` $\rightarrow$ human).
- **`AT-13`**: Jira Untrusted Content Sanitizer & Prompt Injection Security Boundary.
- **`AT-14`**: End-to-End Failure Matrix & Chaos/Crash Recovery Verification.
