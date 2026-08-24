# 03_STORAGE_AND_EVENT_SOURCING — Horo Architecture v3.0 Specification

**Sprint Status**: ✅ COMPLETED (Sprint 3 — 2026-08-24)  
**Schema Version**: 3.0.0  
**Frozen Baseline**: Yes

---

## 🏛️ Directory Overview

This module provides the database schemas, graph constraints, Merkle DAG specifications, and append-only event streaming protocols that underpin the Tri-Graph architecture ($\mathcal{G}_{\text{deriv}}, \mathcal{G}_{\text{sem}}, \mathcal{L}_{\text{event}}$).

```
03_STORAGE_AND_EVENT_SOURCING/
├── cypher/
│   └── semantic_graph_schema.cql        # Neo4j Constraints, Indexes, Ontology & Traversal Queries
└── specs/
    ├── derivation_dag_immutability.md   # Merkle DAG Hashes, Acyclicity & Provenance Chain Spec
    └── event_ledger_stream.md           # Append-Only Event Store (Kafka/Redis Stream Hash Chaining)
```

---

## ⚙️ Core Components

### 1. Semantic Property Graph Schema (`cypher/semantic_graph_schema.cql`)
- **Neo4j Constraints**: Uniqueness enforced for `Session.session_id`, `Claim.claim_id`, `DerivationNode.node_uid`, `Rule.rule_id`, `CorpusPassage.passage_id`, and `EventNode.node_uid`.
- **Search Indexes**: Domain, Materiality, and Session lookup indexes.
- **Ontology & Edge Types**: `:CONTRADICTS` (symmetric), `:SUPERCEDES` (transitive/monotonic), `:SUPPORTS`, `:QUALIFIES`, `:DERIVES_FROM` (DAG acyclic), `:APPLIED_RULE`, `:GROUNDED_IN`.
- **Stored Queries**: Cycle detection in $\mathcal{G}_{\text{deriv}}$, conflict cluster extraction, real-time $LCI_w / RNI_w$ evaluation, and full epistemic traceback from claim to canon text.

### 2. Derivation DAG Immutability (`specs/derivation_dag_immutability.md`)
- **Mathematical Model**: $\mathcal{G}_{\text{deriv}} = (V_D, E_D)$ content-addressed DAG.
- **Merkle Hash Formula**: $H(v) = \text{SHA256}(\text{JCS}(v.\text{payload}) \parallel \bigoplus H(parents))$.
- **Acyclicity Invariant**: Mandatory reachability check $\text{Reachable}(v, u)$ prior to edge insertion; cycles trigger fatal $H_0$ abort.
- **Reproducibility Tiers**: Governs verification across $R_0$ (bit-identical) through $R_3$ (semantic embedding).

### 3. Append-Only Event Ledger (`specs/event_ledger_stream.md`)
- **Event Envelope**: Standardized envelope supporting 17 canonical FSM event types.
- **Hash-Chaining Formula**: $h_n = \text{SHA256}(h_{n-1} \parallel n \parallel \text{session\_id} \parallel \text{event\_type} \parallel \text{JCS}(\text{payload}_n))$.
- **Stream Binding**: Redis Streams / Kafka topic `horo.events.v3` partitioned by `session_id` to guarantee linear execution ordering and deterministic crash recovery.
