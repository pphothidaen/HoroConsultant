# 05_AGENT_PROMPTS_AND_RUNTIMES — Horo Architecture v3.0 Specification

**Sprint Status**: ✅ COMPLETED (Sprint 4 — 2026-08-24)  
**Schema Version**: 3.0.0  
**Frozen Baseline**: Yes

---

## 🏛️ Directory Overview

This module provides the upgraded production prompt templates for all 10 specialized metaphysics tradition agent nodes (L3/L4) and the runtime adapters for L3–L7 orchestration, arbitration, adversarial auditing, and plan composition.

```
05_AGENT_PROMPTS_AND_RUNTIMES/
├── prompts/
│   ├── bazi_node_prompt.json            # @Horo_BaZi_Node (L3 Ming Xue)
│   ├── ziwei_node_prompt.json           # @Horo_ZiWei_Node (L3 Ming Xue)
│   ├── fengshui_node_prompt.json        # @Horo_FengShui_Node (L3 Xiang Xue)
│   ├── bushi_node_prompt.json           # @Horo_BuShi_Node (L3 Bu Shi)
│   ├── qimen_node_prompt.json           # @Horo_QiMen_Node (L4 San Shi)
│   ├── daliuren_node_prompt.json        # @Horo_DaLiuRen_Node (L4 San Shi)
│   ├── taiyi_node_prompt.json           # @Horo_TaiYi_Node (L4 San Shi)
│   ├── qizheng_node_prompt.json         # @Horo_QiZheng_Node (L4 Ming Xue)
│   ├── mianxiang_node_prompt.json       # @Horo_MianXiang_Node (L4 Xiang Xue)
│   └── zeji_node_prompt.json            # @Horo_ZeJi_Node (L4 Ze Ji Hard Exclusion)
└── runtimes/
    ├── __init__.py
    ├── claim_validator.py               # L3/L4 Emission Schema & Firewall Guard
    ├── consensus_engine.py              # L5 Tri-Graph & Dynamic Arbitration Engine
    ├── audit_node.py                    # L6 Adversarial Audit & Inversion Thinking
    └── plan_composer.py                 # L7 Plan Synthesis & Epistemic Disclaimer Emitter
```

---

## ⚙️ Core Architecture & Enforcements

1. **Strict Context Isolation & Domain Firewalls**:
   - Every node operates strictly within its designated tradition domain.
   - Forbidden terms from other domains are blocked at the validator level.
   - All claims must cite canonical classical texts belonging to the domain's authorized corpus list.

2. **5-Stage Epistemic Trace**:
   - `source_corpus` + `locator` + `original_text` $\rightarrow$ `interpretation_id` $\rightarrow$ `applied_rule_id` $\rightarrow$ `derived_from_calc_hash` $\rightarrow$ `statement`.

3. **5-Dimensional Confidence Vector**:
   - `calculation_integrity`, `rule_match_strength`, `source_support`, `interpretation_stability`, `cross_agent_agreement`.

4. **Tier H2 Hard Exclusion Veto Power**:
   - `@Horo_ZeJi_Node` emits `claim_type: 'hard_exclusion'`, acting as an un-overridable veto against inauspicious timing/directional vectors.

5. **Mandatory Epistemic Disclaimer**:
   - `@Horo_Composer_Node` enforces the inclusion of the official disclaimer verbatim on all output responses.
