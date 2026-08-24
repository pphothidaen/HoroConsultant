# 📜 Append-Only Execution Event Ledger ($\mathcal{L}_{\text{event}}$) Specification
**Horo Architecture v3.0 — Frozen Baseline**  
**Module**: `03_STORAGE_AND_EVENT_SOURCING`  
**Schema Version**: 3.0.0  
**Status**: NORMATIVE SPECIFICATION

---

## 1. Executive Summary & Purpose

The **Execution Event Ledger** ($\mathcal{L}_{\text{event}}$) is an append-only, cryptographically hash-chained event stream recording every state transition, computation milestone, exclusion veto, arbitration decision, and audit gate evaluation during a pipeline run.

### Core Objectives
1. **Total Auditability**: Every decision made by LLM agents or deterministic engines can be reconstructed post-facto.
2. **Crash Recovery & Resumption**: A crashed or timed-out pipeline run can be resumed from the exact state indicated by the latest valid event.
3. **Tamper Evidence**: Any alteration of past events invalidates the cryptographic hash chain.

---

## 2. Event Envelope Specification

Every event emitted to $\mathcal{L}_{\text{event}}$ MUST conform to the following schema:

```json
{
  "event_id": "UUIDv4",
  "session_id": "UUIDv4",
  "sequence_number": 1,
  "event_type": "FSM_H3_ARBITRATION",
  "actor_node_id": "@Horo_Consensus_Engine",
  "timestamp_utc": "2026-08-24T18:30:00.000Z",
  "previous_event_hash": "a1b2c3...64hex",
  "event_hash": "d4e5f6...64hex",
  "payload": {
    "intent": "STRATEGIC_TIMING_ACTION",
    "conflict_id": "CONF-001",
    "winning_domain": "san_shi_qi_men",
    "superseded_claim_id": "c12345",
    "arbitration_rule": "ARB-01-PRIORITY-DOMINANCE"
  }
}
```

### Required Fields & Invariants

| Field | Type | Description | Invariant |
|---|---|---|---|
| `event_id` | UUIDv4 | Unique event message identifier | Globally unique |
| `session_id` | UUIDv4 | Execution session ID | Consistent across whole run |
| `sequence_number` | Integer | 1-based sequential counter | Strictly monotonic: $seq_n = seq_{n-1} + 1$ |
| `event_type` | String Enum | 17 canonical FSM event types | Must match FSM specification |
| `actor_node_id` | String | Emitting agent or engine ID | Valid node identifier |
| `timestamp_utc` | ISO 8601 | Server timestamp | Monotonically non-decreasing |
| `previous_event_hash` | Hex (64) | SHA-256 of previous event | Genesis event uses $64 \times \text{'0'}$ |
| `event_hash` | Hex (64) | SHA-256 of current event | Verified by Hash-Chaining Formula |
| `payload` | Object | Event-specific data | Valid JSON object |

---

## 3. Cryptographic Hash-Chaining Algorithm

### Genesis Hash (Sequence Number 1)
$$h_0 = \text{"0000000000000000000000000000000000000000000000000000000000000000"}$$

### Recurrence Relation
For event $n \ge 1$:

$$h_n = \text{SHA256}\Big(h_{n-1} \;\big\|\; \text{str}(n) \;\big\|\; \text{session\_id} \;\big\|\; \text{event\_type} \;\big\|\; \text{JCS}(\text{payload}_n)\Big)$$

Where:
- $\text{JCS}(\cdot)$ is the RFC 8785 JSON Canonicalization Scheme.
- $\big\|$ denotes byte-level concatenation with null-byte (`\x00`) separators.

---

## 4. Canonical Event Type Catalog

The ledger supports exactly 17 canonical FSM event types:

```
PIPELINE_STARTED
L2_CALCULATION_COMPLETED
CLAIM_EMITTED
FSM_H0_TRIGGERED
FSM_H1_TRIGGERED
FSM_H1_RECOMPUTE
FSM_H1_QUARANTINE
FSM_H2_EXCLUSION
FSM_H3_ARBITRATION
FSM_H3_HITL_ESCALATION
AUDIT_PASS
AUDIT_PASS_WITH_WARNINGS
AUDIT_FAIL_RECOMPUTE
AUDIT_FAIL_ESCALATE
COMPOSER_OUTPUT_EMITTED
PIPELINE_COMPLETED
PIPELINE_ABORTED
```

---

## 5. Stream Transport & Partitioning Architecture

### Transport Engine Binding
- **Primary Message Bus**: Redis Streams (`XADD / XREADGROUP`) or Apache Kafka / Redpanda.
- **Topic / Stream Name**: `horo.events.v3`
- **Partition Key**: `session_id`

### Partitioning Invariant
All events belonging to the same `session_id` are routed to the **same stream partition**. This guarantees strict FIFO linear delivery without requiring distributed locking.

---

## 6. Replay & FSM Recovery Protocol

In the event of worker crash or unexpected disconnect:

1. Read all events for `session_id` from `horo.events.v3` ordered by `sequence_number ASC`.
2. Verify cryptographic hash chain from $h_0$ to $h_{\text{last}}$.
   - If chain validation fails: **ABORT** with `CORRUPTED_EVENT_LEDGER`.
3. Feed valid events sequentially into the FSM state reducer.
4. The FSM reaches the exact state corresponding to $h_{\text{last}}$, allowing seamless continuation.
