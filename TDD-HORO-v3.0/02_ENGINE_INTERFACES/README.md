# 02_ENGINE_INTERFACES — Horo Architecture v3.0 Specification

**Sprint Status**: ✅ COMPLETED (Sprint 2 — 2026-08-24)  
**Schema Version**: 3.0.0  
**Frozen Baseline**: Yes

---

## 🏛️ Directory Overview

This module provides the formal deterministic specifications for execution flow control, error recovery, multi-domain arbitration, and quality audit verification in the Horo v3.0 pipeline.

```
02_ENGINE_INTERFACES/
├── fsm/
│   └── constraint_state_machine.json    # 4-Tier Constraint FSM (H0, H1, H2, H3)
├── policies/
│   └── dynamic_arbitration.json         # Intent-to-Domain Priority Matrix & Tiebreakers
└── matrices/
    └── audit_policy_truth_table.csv     # Deterministic L6 Audit Verdict Lookup Table
```

---

## ⚙️ Core Specifications

### 1. 4-Tier Constraint FSM (`fsm/constraint_state_machine.json`)
Governs pipeline progression through 13 states with 18 deterministic transitions:
- **Tier H0 (Fatal / Physical Invariance)**: Immediate pipeline abort (`PIPELINE_ABORTED`) on astronomical kernel errors or coordinate anomalies.
- **Tier H1 (Single-Domain Integrity)**: Automatic bounded recomputation loop (max 3 retries) for domain firewall breaches or ungrounded claims; falls back to claim quarantine.
- **Tier H2 (Hard Domain Exclusion / Veto)**: Non-negotiable pruning of candidate datetimes/locations triggered by ZeJi (e.g. Sui Po 岁破, San Sha 三煞) or Feng Shui sha factors.
- **Tier H3 (Cross-Domain Arbitration)**: Dynamic resolution of multi-domain contradictions via user intent priority rankings; escalates to HITL queue if severity $\ge 0.70$ and rank is tied.

### 2. Dynamic Arbitration Policy (`policies/dynamic_arbitration.json`)
Defines the authoritative domain precedence order mapped across core user intents:
- `STRATEGIC_TIMING_ACTION`: QiMen (1) > ZeJi (2) > BaZi (3) > ZiWei (4) > DaLiuRen (5)
- `NATAL_CHARACTER_PATH`: BaZi (1) > ZiWei (2) > QiZheng (3) > MianXiang (4)
- `SPATIAL_LOCATION_OFFICE`: FengShui (1) > QiMen (2) > BaZi (3)
- `TACTICAL_DIVINATION_EVENT`: LiuYao (1) > DaLiuRen (2) > QiMen (3)
- `HEALTH_VITALITY`: BaZi (1) > ZiWei (2) > MianXiang (3)
- `RELATIONSHIP_SYNASTRY`: BaZi (1) > ZiWei (2) > LiuYao (3)

Also includes rules for:
- `ARB-01-PRIORITY-DOMINANCE`: Creation of `supersedes` edges.
- `ARB-02-EQUAL-RANK-TIEBREAKER`: Composite scoring using materiality and confidence vectors.
- `ARB-03-HARD-VETO-ABSOLUTE`: Absolute override by Hard Exclusion claims.
- `ARB-04-CONFIRMATION-BIAS-AUDIT`: Guard against echo chambers ($RNI_w$ warning when consensus lacks corpus grounding).

### 3. Audit Policy Truth Table (`matrices/audit_policy_truth_table.csv`)
Provides a deterministic lookup table for the L6 Audit Node to assign one of four verdicts:
1. `AUDIT_PASS`: $LCI_w \ge 0.85$, $RNI_w \le 0.15$, clean flags $\rightarrow$ Release to Composer.
2. `AUDIT_PASS_WITH_WARNINGS`: $LCI_w \in [0.70, 0.85)$, $RNI_w \le 0.20$ or Echo Chamber $\rightarrow$ Release with domain divergence disclosure.
3. `AUDIT_FAIL_RECOMPUTE`: $RNI_w > 0.20$ or ungrounded claims $\rightarrow$ Trigger H1 recompute.
4. `AUDIT_FAIL_ESCALATE`: $LCI_w < 0.70$ or False Provenance $\rightarrow$ Escalate to Human Review Queue (`HITL_ESCALATION_QUEUE`).
