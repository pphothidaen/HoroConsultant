# 📐 Derivation DAG Immutability & Merkle Provenance Specification
**Horo Architecture v3.0 — Frozen Baseline**  
**Module**: `03_STORAGE_AND_EVENT_SOURCING`  
**Schema Version**: 3.0.0  
**Status**: NORMATIVE SPECIFICATION

---

## 1. Executive Summary & Mathematical Model

The **Derivation DAG** ($\mathcal{G}_{\text{deriv}} = (V_D, E_D)$) is the immutable, content-addressed backbone of Horo Architecture v3.0. Every computational artifact—from raw planetary coordinates produced by L1 to atomic claims emitted by L3/L4—is preserved as a node in $\mathcal{G}_{\text{deriv}}$.

```
[L1 Astro State] (H_1)
       │
       ▼
[L2 Tradition Matrix] (H_2) ──────┐
       │                          │
       ▼                          ▼
[L3 Claim Emission A] (H_3)  [L3 Claim Emission B] (H_4)
       │                          │
       └──────────────┬───────────┘
                      ▼
            [L5 Consensus Tri-Graph] (H_5)
                      │
                      ▼
            [L6 Audit Verification] (H_6)
                      │
                      ▼
            [L7 Composed Plan] (H_7)
```

---

## 2. Merkle Hash Formulation

Every node $v \in V_D$ receives a deterministic content hash $H(v) \in \{0, 1\}^{256}$ computed as:

$$H(v) = \text{SHA256}\Big(\text{JCS}(v.\text{payload}) \;\big\|\; \bigoplus_{(u, v) \in E_D} H(u)\Big)$$

Where:
- $\text{JCS}(\cdot)$ is the RFC 8785 JSON Canonicalization Scheme (deterministic key sorting, standardized float representation, UTF-8 encoding).
- $(u, v) \in E_D$ represents a directed edge indicating that node $v$ was computed directly from parent node $u$.
- $\bigoplus$ denotes the lexicographically sorted concatenation of parent content hashes.

### Base Case (Root Nodes)
For root nodes with indegree $0$ (e.g. initial user parameters, Swiss Ephemeris ephemeris metadata):

$$H(\text{root}) = \text{SHA256}\Big(\text{JCS}(\text{root}.\text{payload}) \;\big\|\; \text{"ROOT\_NODE"}\Big)$$

---

## 3. Strict Acyclicity Invariant Enforcement

$\mathcal{G}_{\text{deriv}}$ is **strictly acyclic**. Cycles represent logical paradoxes (a computation depending on its own descendant) and are strictly prohibited.

### Insertion Guard Algorithm
Before committing any new edge $(u, v)$ to $\mathcal{G}_{\text{deriv}}$:

1. Perform a directed reachability query: $\text{Reachable}(v, u)$.
2. If $\text{Reachable}(v, u) == \text{True}$:
   - **REJECT** the insertion immediately.
   - Emit an `FSM_H0_TRIGGERED` event.
   - Abort pipeline with error `DERIVATION_CYCLE_DETECTED`.
3. If $\text{Reachable}(v, u) == \text{False}$:
   - Compute updated content hash $H(v)$.
   - Persist node $v$ and edge $(u, v)$ with immutable flag set to `True`.

---

## 4. Reproducibility Tiers & Verification

$\mathcal{G}_{\text{deriv}}$ guarantees reproducibility across five formal tiers:

| Tier | Name | Guarantee | Verification Method |
|---|---|---|---|
| **$R_0$** | Bit-Identical | Exact bit-for-bit match of all L1/L2 calculation outputs | SHA-256 hash match |
| **$R_1$** | Float-Epsilon | Numerical convergence within physical tolerance | $\|x_{\text{calc}} - x_{\text{ref}}\| \le 10^{-7}$ (or $1.0''$ arcsec) |
| **$R_2$** | Rule-Identical | Exact match of executed rule IDs and triggers | Set equality of `applied_rule_id` |
| **$R_3$** | Semantic | Semantic consistency across LLM variations | Embedding Cosine Similarity $\ge 0.95$ |
| **$R_4$** | Observational | External real-world correlation (Isolated by Plane D) | Statistical aggregate analysis |

---

## 5. Storage Engine Binding & Content-Addressability

### Primary Keying
- Node Primary Key: `content_hash` (SHA-256 hex string).
- Key-Value / Object Store Location: `s3://horo-deriv-cas/v3/{hash[0:2]}/{hash[2:4]}/{hash}.json`

### Immutability (WORM Semantics)
- Once written, no update (`UPDATE` / `PUT`) is permitted on existing hashes.
- Nodes are strictly append-only.
- Historical graphs can be reconstructed by traversing backwards from any terminal L7 node hash to the root inputs.
