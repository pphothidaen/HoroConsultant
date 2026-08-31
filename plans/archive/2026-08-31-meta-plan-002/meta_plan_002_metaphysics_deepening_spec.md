# ☯️ Sprint META-PLAN-002: Five-Branch Metaphysics Deepening, 6-Domain Benchmark Alignment & Dynamic SVG Charting Specification

**Document ID**: `META-PLAN-002-SPEC`  
**Date**: `2026-08-31` (Asia/Bangkok)  
**Lead Authority**: Business System Analyst (`business_analyst`) & Master Orchestrator (`orchestrator`)  
**Gate Status**: `APPROVED`  
**Authorized Next Phase**: Milestone M0 (Test Baselines & Schema Contracts)  
**Assigned Editor**: `business_analyst`  
**Writable Ownership Scope**: `plans/meta_plan_002_metaphysics_deepening_spec.md`  

---

## 1. 📋 Executive Summary & Sprint Objective

Sprint **META-PLAN-002** represents the core computational and domain deepening phase of the **HoroConsultant** enterprise platform. Building upon the verified, zero-regression multi-agent architecture and hardened Agile broker infrastructure, this sprint focuses on four strategic pillars:

1. **Five-Branch Metaphysics Deepening (五術 - Wǔ Shù)**:
   - Deepening the pure-Python, deterministic algorithmic engines across all five branches:
     - **San Shi (三式)**: Tai Yi Shen Shu (太乙神數), Da Liu Ren (大六壬), Qi Men Dun Jia (奇門遁甲).
     - **Ming Xue (命學)**: BaZi (八字 - TST True Solar Time, 12-scenario midnight matrix, Shen Sha), Zi Wei Dou Shu (紫微斗數 - 12 palaces, 14 major stars, 4 Si Hua transformations), Qi Zheng Si Yu (七政四餘 - Swiss Ephemeris / PyEphem planetary coordinates).
     - **Bu Shi (卜筮)**: Zhou Yi / I Ching (周易 - 64 hexagrams, changing lines), Liu Yao (六爻 - Na Jia, 5 relatives, 6 spirits), Mei Hua Yi Shu (梅花易數 - Ti/Yong Gua interactions).
     - **Xiang Xue (相學)**: Xuan Kong Flying Stars (玄空風水 - Period 9 2024-2043, 24 mountains), San He Feng Shui (三合風水 - 12 life stages water methods), Mian Xiang (麻衣神相 - 12 facial palaces & 5 officers).
     - **Ze Ji Xue (擇吉學)**: Imperial Date Selection (協紀辨方書 - 12 duty officers 建除十二神, auspicious/inauspicious spirits, clash avoidance).
2. **6-Domain Question Benchmark Alignment**:
   - Enhancing the NLP Question Focus Router (`project/core/question_focus_router.py`), Multi-Agent Debate Engine (`project/core/multi_agent_debate.py`), and Prediction Validator (`project/validator.py`) to enforce sharp, direct answering across the 6 core consulting domains:
     - Domain 1: Career, Promotion & Business Strategy (การงานและการลงทุนธุรกิจ)
     - Domain 2: Finance, Wealth & Investment (การเงิน โชคลาภ และทรัพย์สิน)
     - Domain 3: Love, Marriage & Business Partnership (ความรัก หุ้นส่วน และความสัมพันธ์)
     - Domain 4: Health, Longevity & Accident Hazards (สุขภาพ อุบัติเหตุ และเคราะห์ยาม)
     - Domain 5: Auspicious Date & Action Timing (ฤกษ์ยามมงคลและการดำเนินการสำคัญ)
     - Domain 6: Metaphysical Remediation & Feng Shui Alignment (การปรับสมดุลชะตาชีวิตและฮวงจุ้ย)
3. **SVG Dynamic Charting & Visual Rendering Engine**:
   - Upgrading `project/core/svg_generator.py` and `project/core/bazi_display.py` with standalone, responsive, high-resolution SVG visualizers for BaZi 4-Pillars, Zi Wei 12-Palace grids, Qi Men 9-Palace squares, Xuan Kong Flying Star matrices, I Ching hexagram diagrams, and Luopan dynamic compasses.
4. **Automated Test Planes & Quality Verification**:
   - Comprehensive unit, integration, visual DOM, and regression suites enforcing 100% deterministic mathematical accuracy, zero halluncination in canonical text citations, and strict Agile governance compliance (Rules 21 & 22).

---

## 2. 🔥 9-Dimension GRILL REPORT

```
================================================================================
                    GRILL GATE EVALUATION RECORD (META-PLAN-002)
================================================================================
Gate Status    : [APPROVED]
Grilled By     : orchestrator (gpt-5.6-sol / high) 🤝 business_analyst (agy4)
Target Scope   : Metaphysics Core Deepening, 6-Domain Benchmark, SVG Charting
Evidence Base  : Rule 08 (GRILL), Rule 10 (Deterministic Math), Rule 21 (Agile),
                 Rule 22 (Release Notes), 134/134 Pytest Baseline Green
================================================================================
```

### D1 — Scope Boundary

- **IN Scope**:
  1. Deepening deterministic core calculation engines in `project/core/` (`tai_yi_engine.py`, `liu_ren_engine.py`, `qi_men_engine.py`, `bazi_engine.py`, `zi_wei_engine.py`, `qi_zheng_engine.py`, `iching_engine.py`, `liu_yao_engine.py`, `mei_hua_engine.py`, `xuan_kong_engine.py`, `san_he_engine.py`, `mian_xiang_engine.py`, `ze_ji_engine.py`, `thai_vedic_engine.py`, `western_uranian_engine.py`, `numerology_engine.py`).
  2. Question Focus Router and Multi-Agent Debate synthesis integration (`project/core/question_focus_router.py`, `project/core/multi_agent_debate.py`, `project/core/prompt_manager.py`).
  3. Dynamic SVG generator rendering enhancements (`project/core/svg_generator.py`, `project/core/bazi_display.py`).
  4. 6-Domain Question Benchmark fixtures, test suites, and validator evaluation rubric (`tests/test_question_focus_router.py`, `tests/test_five_branch_metaphysics.py`, `tests/test_svg_generator_contract.py`).
  5. Governance documentation, sprint tracking, and task board synchronization (`plans/meta_plan_002_metaphysics_deepening_spec.md`, `PROJECT_TASKS.md`, `plans/plan.md`).
- **OUT of Scope**:
  1. Live external deployment to Hugging Face Space or Vercel (reserved for release phase).
  2. Training or fine-tuning weight modification on Kaggle GPU (model weights frozen).
  3. Secret or keychain modifications (covered under completed BROKER-PLAN-001).
  4. Direct modification of generated platform mirrors (`.codex/agents/*.toml`).
- **Interface Stability**:
  - All existing FastAPI endpoints (`/api/calculate`, `/api/debate`, `/api/render-svg`) retain full backward compatibility.
  - JSON schemas for astrological calculation payloads remain strict and typed.

### D2 — Requirement Delta

- **Added**:
  - Full 18-Ju calculation in Qi Men Dun Jia (Yang 9 Ju, Yin 9 Ju) with Door/Star/Deity placement.
  - Zi Wei Dou Shu 14 Major Stars + 4 Transformations (化祿, 化權, 化科, 化忌) + Decade Palace progressions.
  - Liu Yao Na Jia 6-line stem/branch assignment with 5 Relatives (五親) and 6 Spirits (六神).
  - Xuan Kong Period 9 Flying Star chart calculation (24 mountains, mountain/facing stars).
  - 6-Domain Benchmark Evaluation Rubric with 100-point scoring.
  - Standalone SVG visual components for 6 chart types with responsive Glassmorphism styling.
- **Refined**:
  - BaZi Day Master strength scoring algorithm with seasonal coefficient weighting.
  - Question Focus Intent classifier with multi-branch relevance mapping.
- **Removed (Rule 10 Purge)**:
  - Hardcoded heuristic approximations in legacy astrological stubs.

### D3 — Acceptance Criteria & Verification

| # | Acceptance Criterion | Verification Tool / Command | Owner |
|---|---|---|---|
| 1 | All 5-branch calculations produce deterministic, canonical results matching classical treatises | `python3 -m pytest tests/test_five_branch_metaphysics.py` | `qa_tester` |
| 2 | Question Focus Router classifies 6-domain queries with >95% precision against gold standard fixtures | `python3 -m pytest tests/test_question_focus_router.py` | `qa_tester` |
| 3 | Multi-Agent Debate integrates focused answers, citing classic texts without generic filler | `python3 -m pytest tests/test_multi_agent_debate_focus.py` | `qa_tester` |
| 4 | SVG Generator produces valid XML/SVG with zero syntax errors across all 6 chart formats | `python3 -m pytest tests/test_svg_generator_contract.py` | `qa_tester` |
| 5 | Full unit and regression test suite passes 100% with zero regressions | `python3 -m pytest -v` | `qa_tester` |
| 6 | Cross-agent ecosystem remains 100% synchronized | `python3 scripts/sync_ai_agent_ecosystem.py --check` | `devops` |
| 7 | Zero secrets or raw credential material leaked | `python3 project/core/code_reviewer.py --review` | `code_reviewer` |

### D4 — Constraints & Safeguards

1. **Rule 10 Deterministic Calculation Boundary**: Pure Python math for all astronomical and astrological algorithms. LLM is strictly prohibited from doing arithmetic, solar time adjustment, or chart layout generation.
2. **Pure ASCII Logging**: All loggers, print statements, and test outputs MUST use ASCII tags (`[OK]`, `[INFO]`, `[ERROR]`, `[WARNING]`, `[START]`, `[DONE]`).
3. **One-Editor Ownership Boundary**: Concurrent tickets must have strictly disjoint writable files.
4. **Zero-Cost AI Governance**: Local-first execution using Ollama Qwen2.5:7b, with Gemini Flash fallback strictly for external validation.

### D5 — Sub-Agent Allocation & Ownership

- `orchestrator`: Overall sprint execution DAG, consensus, and final handoff seal.
- `business_analyst`: Agile task board governance, GRILL spec authoring, and ReleaseNotes compilation.
- `developer`: Core calculation engine deepening, question router, debate engine, and SVG generator implementation.
- `qa_tester`: Test fixture authoring, unit/integration test suites, and regression validation.
- `code_reviewer`: Security audit, Pure ASCII verification, and Rule 10 boundary inspection.
- `devops`: Ecosystem synchronization and platform manifest verification.
- `domain_master`: Canonical astrological rule verification and classical treatise citation audit.

### D6 — Assumption Register

| Assumption / Invariant | Status | Validation Method |
|---|---|---|
| True Solar Time calculations match NOAA Spencer 1971 formula | `[CONFIRMED]` | Verified against `tests/test_core.py` |
| Swiss Ephemeris / PyEphem bindings are available locally | `[CONFIRMED]` | Verified in `project/core/swiss_ephemeris.py` |
| All 6-domain question benchmark fixtures represent realistic user inquiries | `[CONFIRMED]` | Validated in `plans/question_forecast_alignment_spec.md` |
| SVG outputs are rendered client-side or embedded inline in Glassmorphism UI | `[CONFIRMED]` | Contract tests in `tests/test_svg_generator_contract.py` |

### D7 — Risk & Rollback Strategy

- **Risk 1: Mathematical Edge Cases in Lunar/Solar Calendar Leap Months**:
  - *Mitigation*: Comprehensive fixture testing covering leap months (閏月) and midnight transitions (早子/夜子時).
  - *Rollback*: Fallback to proven `bazi_engine.py` / `calendar_engine.py` baseline.
- **Risk 2: Visual Distortion in SVG Rendering Across Different Viewport Sizes**:
  - *Mitigation*: Use responsive `viewBox` attributes and relative coordinate grids.
  - *Rollback*: Revert SVG template changes via Git commit rollback.
- **Risk 3: Cross-Agent Memory or Token Bloat in Multi-Agent Debate**:
  - *Mitigation*: Strict token budgeting and context truncation in `prompt_manager.py`.

### D8 — Token & Capacity Efficiency Strategy

- High-tier models (`gpt-5.6-sol`, `Gemini 3.7 Pro`) reserved for architecture, GRILL review, and synthesis.
- Mid-tier / Local models (`qwen2.5:7b`) utilized for local reasoning, test generation, and code implementation.
- All test runs and command executions stream trimmed ASCII logs to preserve conversation context.

### D9 — Metaphysics Domain Alignment & Canonical References

Every calculation module is anchored in authoritative classical literature:
- **BaZi (八字)**: 《淵海子平》 (Yuan Hai Zi Ping), 《滴天髓》 (Di Tian Shui), 《子平真詮》 (Zi Ping Zhen Quan), 《三命通會》 (San Ming Tong Hui).
- **Zi Wei Dou Shu (紫微斗數)**: 《紫微斗數全書》 (Zi Wei Dou Shu Quan Shu), 《太微賦》 (Tai Wei Fu).
- **Qi Men Dun Jia (奇門遁甲)**: 《煙波釣叟歌》 (Yan Bo Diao Sou Ge), 《奇門遁甲大全》 (Qi Men Dun Jia Da Quan).
- **Da Liu Ren (大六壬)**: 《六壬大全》 (Liu Ren Da Quan), 《六壬指南》 (Liu Ren Zhi Nan).
- **Tai Yi Shen Shu (太乙神數)**: 《太乙金鏡式經》 (Tai Yi Jin Jing Shi Jing).
- **Zhou Yi / I Ching (周易)**: 《易經》 (Yi Jing), 《十翼》 (Ten Wings / Shi Yi).
- **Liu Yao (六爻)**: 《卜筮正宗》 (Bu Shi Zheng Zong), 《增刪卜易》 (Zeng Shan Bu Yi).
- **Mei Hua Yi Shu (梅花易數)**: 《梅花易數》 (Mei Hua Yi Shu - Shao Yong).
- **Xuan Kong Feng Shui (玄空風水)**: 《青囊奧語》 (Qing Nang Ao Yu), 《沈氏玄空學》 (Shen Shi Xuan Kong Xue).
- **San He Feng Shui (三合風水)**: 《地理五訣》 (Di Li Wu Jue).
- **Mian Xiang (相學)**: 《麻衣神相》 (Ma Yi Shen Xiang), 《柳莊相法》 (Liu Zhuang Xiang Fa).
- **Ze Ji (擇吉)**: 《協紀辨方書》 (Xie Ji Bian Fang Shu - Qing Imperial Court).
- **Qi Zheng Si Yu (七政四餘)**: 《果老星宗》 (Guo Lao Xing Zong).

---

## 3. 🗺️ Sprint META-PLAN-002 Milestone Breakdown (M0 - M5)

```
+-----------------------------------------------------------------------------------+
|                        SPRINT META-PLAN-002 WORKFLOW DAG                          |
+-----------------------------------------------------------------------------------+
  [M0] Agile Governance, Test Baselines & Architecture Blueprint
   │
   ├──> [M1] Five-Branch Metaphysics Computational Core Deepening
   │     │
   │     ├──> [M2] 6-Domain Question Benchmark Alignment & Focus Routing
   │     │     │
   │     └───> [M3] SVG Dynamic Charting & Visual Rendering Engine
   │           │
   └───────────┴──> [M4] Automated Test Planes, Integration & E2E Regression
                     │
                     └──> [M5] Security Audit, Release Packaging & Sprint Closure
```

---

## 4. 📝 Detailed Ticket Ledger (META2-M0-010 through META2-M5-040)

### Milestone M0: Agile Governance, Test Baselines & Architecture Blueprint

#### `META2-M0-010` — Plan & GRILL Specification Authoring
- **Role**: `business_analyst`
- **Priority / Effort**: `P0 / S`
- **Depends On**: None
- **Blocks**: `META2-M0-020`, `META2-M0-030`
- **Writable Scope**: `plans/meta_plan_002_metaphysics_deepening_spec.md`, `PROJECT_TASKS.md`, `plans/plan.md`
- **Description**: Formulate the comprehensive 9-dimension GRILL specification, decompose sprint milestones M0 through M5 into 24 atomic tickets, and establish the Agile task board in `PROJECT_TASKS.md` adhering to Rule 21 and Rule 22.
- **Definition of Ready (DoR)**:
  - [x] GRILL dimensions reviewed and confirmed.
  - [x] Agile governance rules (Rule 21, Rule 22) loaded.
- **Definition of Done (DoD)**:
  - [x] `plans/meta_plan_002_metaphysics_deepening_spec.md` created with full 9-dimension GRILL report.
  - [x] `PROJECT_TASKS.md` updated with META-PLAN-002 ticket board.
  - [x] `plans/plan.md` updated with Governance Sync header.

#### `META2-M0-020` — Baseline Test Freeze & Provenance Manifest
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META2-M0-010`
- **Blocks**: `META2-M1-010`
- **Writable Scope**: `plans/test_provenance/meta2-baseline-20260831.json`, `tests/fixtures/meta2_baselines/`
- **Description**: Execute full test suite regression, freeze test hashes into an immutable test provenance manifest, and record baseline execution proof.
- **DoR**: `META2-M0-010` DONE; test suite clean.
- **DoD**: Manifest generated and signed with Git commit hash and timestamp; 100% test pass.

#### `META2-M0-030` — Architecture Contract & Five-Branch Interface Schema Definition
- **Role**: `developer`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META2-M0-010`
- **Blocks**: `META2-M1-010`..`040`
- **Writable Scope**: `project/core/base_engine.py`, `project/core/v3_engine_adapter.py`
- **Description**: Define standardized Pydantic data schemas and abstract base classes for all five branches, ensuring uniform output interfaces for chart payloads, energies, and classical interpretations.
- **DoR**: `META2-M0-010` DONE; domain requirements specified.
- **DoD**: Typed schemas validated with pytest contract tests.

#### `META2-M0-040` — Ecosystem Sync & Pre-Implementation Gate Review
- **Role**: `code_reviewer`
- **Priority / Effort**: `P1 / XS`
- **Depends On**: `META2-M0-010`, `META2-M0-020`, `META2-M0-030`
- **Blocks**: Milestone M1 start
- **Writable Scope**: `plans/evidence/meta2/m0-pre-impl-review.json`
- **Description**: Perform independent gate review of M0 deliverables, verify zero-leak secrets, validate Rule 10 deterministic boundaries, and sign off on M1 entry.
- **DoR**: M0-010, M0-020, M0-030 DONE.
- **DoD**: Review verdict `PASS` recorded in evidence JSON.

---

### Milestone M1: Five-Branch Metaphysics Computational Core Deepening

#### `META2-M1-010` — San Shi Core Deepening (Tai Yi, Da Liu Ren, Qi Men Dun Jia)
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M0-040`
- **Blocks**: `META2-M2-020`, `META2-M3-020`, `META2-M4-010`
- **Writable Scope**: `project/core/tai_yi_engine.py`, `project/core/liu_ren_engine.py`, `project/core/qi_men_engine.py`
- **Description**: Implement full 18-Ju cycle for Qi Men Dun Jia (Yang 9 Ju, Yin 9 Ju, 9 Stars, 8 Doors, 8 Deities), complete Da Liu Ren 3-Transmissions (三傳) and 4-Lessons (四課) with 12 Heavenly Generals, and deepen Tai Yi accumulated year epoch calculations.
- **DoR**: M0 gate review PASSED; interface schemas locked.
- **DoD**: Complete pure-Python deterministic calculations verified against classical benchmark charts.

#### `META2-M1-020` — Ming Xue Core Deepening (BaZi, Zi Wei Dou Shu, Qi Zheng Si Yu)
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M0-040`
- **Blocks**: `META2-M2-020`, `META2-M3-010`, `META2-M4-010`
- **Writable Scope**: `project/core/bazi_engine.py`, `project/core/zi_wei_engine.py`, `project/core/qi_zheng_engine.py`
- **Description**: Deepen BaZi engine with 12-scenario midnight matrix, Day Master strength scoring, Hidden Stems, and Shen Sha; expand Zi Wei engine to place 14 major stars, 4 Si Hua transformations, and decade palace progressions; verify Qi Zheng planetary positions via PyEphem.
- **DoR**: M0 gate review PASSED.
- **DoD**: Unit tests verify 100% deterministic accuracy across 50 sample natal charts.

#### `META2-M1-030` — Bu Shi Core Deepening (I Ching, Liu Yao, Mei Hua Yi Shu)
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META2-M0-040`
- **Blocks**: `META2-M2-020`, `META2-M3-030`, `META2-M4-010`
- **Writable Scope**: `project/core/iching_engine.py`, `project/core/liu_yao_engine.py`, `project/core/mei_hua_engine.py`
- **Description**: Implement 64-hexagram permutations with dynamic changing lines for I Ching; full Na Jia stem/branch and 5 Relatives assignment for Liu Yao; and Ti/Yong 5-element dynamic relationship scoring for Mei Hua Yi Shu.
- **DoR**: M0 gate review PASSED.
- **DoD**: Mathematical accuracy verified against classical divination tables.

#### `META2-M1-040` — Xiang Xue & Ze Ji Core Deepening (Xuan Kong, San He, Ze Ji)
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META2-M0-040`
- **Blocks**: `META2-M2-020`, `META2-M3-020`, `META2-M4-010`
- **Writable Scope**: `project/core/xuan_kong_engine.py`, `project/core/san_he_engine.py`, `project/core/ze_ji_engine.py`, `project/core/mian_xiang_engine.py`
- **Description**: Expand Xuan Kong Flying Stars for Period 9 (2024-2043) with 24-mountain facing/mountain stars and castle gate theory; implement San He 12 Life Stages water methods; and automate Ze Ji 12 Duty Officers with auspicious/inauspicious star filters.
- **DoR**: M0 gate review PASSED.
- **DoD**: Period 9 charts and date selection rules pass 100% of unit assertions.

---

### Milestone M2: 6-Domain Question Benchmark Alignment & Focus Routing Engine

#### `META2-M2-010` — 6-Domain Question Benchmark Dataset & Canonical Fixture Suite
- **Role**: `domain_master` / `qa_tester`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META2-M1-010`..`040`
- **Blocks**: `META2-M2-020`, `META2-M4-020`
- **Writable Scope**: `tests/fixtures/benchmark_questions_6domain.json`
- **Description**: Construct gold-standard benchmark fixtures covering all 6 consulting domains with expected intent tags, relevant astrology branches, required classic citations, and 100-point rubric criteria.
- **DoR**: M1 calculation cores ready.
- **DoD**: 60 test case scenarios (10 per domain) authored and schema-validated.

#### `META2-M2-020` — Question Focus Router & NLP Intent Classification Enhancement
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M2-010`
- **Blocks**: `META2-M2-030`, `META2-M4-020`
- **Writable Scope**: `project/core/question_focus_router.py`
- **Description**: Enhance the Question Focus Router to accurately classify user queries into primary and secondary domains, extract specific focus parameters (timing, partnership, career switch), and bind appropriate astrological engine weights.
- **DoR**: `META2-M2-010` fixture dataset ready.
- **DoD**: Classification accuracy >95% across all 60 benchmark fixture cases.

#### `META2-M2-030` — Multi-Agent Debate & Master Persona Synthesis
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META2-M2-020`
- **Blocks**: `META2-M2-040`, `META2-M4-020`
- **Writable Scope**: `project/core/multi_agent_debate.py`, `project/core/prompt_manager.py`
- **Description**: Update prompt templates and synthesizer in Multi-Agent Debate to prioritize direct answers to the user's specific focus question, synthesize multi-master consensus, and eliminate generic filler.
- **DoR**: `META2-M2-020` router enhancements complete.
- **DoD**: Synthesized debate outputs contain explicit direct advice, timing recommendations, and classical treatise citations.

#### `META2-M2-040` — Prediction Validator Agent & 100-Point Evaluation Rubric Integration
- **Role**: `qa_tester`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META2-M2-030`
- **Blocks**: `META2-M4-020`
- **Writable Scope**: `project/validator.py`, `tests/test_prediction_validator.py`
- **Description**: Integrate the 100-point evaluation rubric (Direct Relevance 30%, Logic Consistency 30%, Canonical Evidence 20%, Actionable Guidance 20%) into the Gemini External Validator and automated test harness.
- **DoR**: `META2-M2-030` debate synthesizer ready.
- **DoD**: Automated validation passes with overall confidence score >= 0.85 (85/100).

---

### Milestone M3: SVG Dynamic Charting & Visual Rendering Engine

#### `META2-M3-010` — BaZi 4-Pillars & Zi Wei 12-Palace Dynamic SVG Component Generator
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M1-020`
- **Blocks**: `META2-M3-040`, `META2-M4-030`
- **Writable Scope**: `project/core/svg_generator.py`, `project/core/bazi_display.py`
- **Description**: Implement dynamic SVG generators for BaZi 4-Pillars (Stems, Branches, Hidden Stems, 10 Gods, 5-Element color themes) and Zi Wei Dou Shu 12-Palace square grid with major stars, brightness ratings, and Si Hua badges.
- **DoR**: M1 Ming Xue calculation engines complete.
- **DoD**: High-resolution, responsive SVGs render correctly with valid XML structure.

#### `META2-M3-020` — Qi Men & Xuan Kong 9-Palace Matrix SVG Visualizer
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META2-M1-010`, `META2-M1-040`
- **Blocks**: `META2-M3-040`, `META2-M4-030`
- **Writable Scope**: `project/core/svg_generator.py`
- **Description**: Develop 3x3 square matrix SVG renderers for Qi Men Dun Jia (Heaven/Earth/Door/Deity plates) and Xuan Kong Flying Stars (Base, Facing, Mountain stars with Period 9 highlights).
- **DoR**: M1 San Shi and Xiang Xue engines complete.
- **DoD**: Pure SVG output without external font dependencies, matching dark-mode Glassmorphism UI.

#### `META2-M3-030` — I Ching Hexagram & Luopan Dynamic SVG Compass Renderer
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META2-M1-030`, `META2-M1-040`
- **Blocks**: `META2-M3-040`, `META2-M4-030`
- **Writable Scope**: `project/core/svg_generator.py`, `project/core/luopan_dream_engine.py`
- **Description**: Create dynamic SVG visualizers for I Ching 64 Hexagrams (Yin/Yang lines, changing lines, trigram markers) and interactive multi-ring Luopan compass (24 mountains, Early/Later Heaven BaGua).
- **DoR**: M1 Bu Shi and Xiang Xue engines complete.
- **DoD**: Clean SVG code with crisp rendering on mobile and desktop viewports.

#### `META2-M3-040` — Glassmorphism Frontend Visual Integration & DOM Contract Tests
- **Role**: `developer` / `qa_tester`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META2-M3-010`, `META2-M3-020`, `META2-M3-030`
- **Blocks**: `META2-M4-030`
- **Writable Scope**: `project/static/`, `tests/test_svg_generator_contract.py`
- **Description**: Wire SVG rendering endpoints into the Glassmorphism frontend UI dashboard, ensuring smooth modal display, zoom/pan capability, and responsive layout.
- **DoR**: All M3 SVG renderers implemented.
- **DoD**: Frontend dashboard loads and displays SVGs seamlessly; contract tests pass.

---

### Milestone M4: Automated Test Planes, Integration & End-to-End Regression

#### `META2-M4-010` — Five-Branch Deterministic Math Unit & Invariant Test Suite
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M1-010`..`040`
- **Blocks**: `META2-M4-040`, `META2-M5-010`
- **Writable Scope**: `tests/test_five_branch_metaphysics.py`
- **Description**: Implement comprehensive unit test suite covering all 5 branches with 100+ assertions verifying edge cases, leap months, midnight boundaries, and mathematical invariants.
- **DoR**: M1 core calculation engines complete.
- **DoD**: 100% unit test pass rate with zero flaky tests.

#### `META2-M4-020` — 6-Domain Benchmark Automated Evaluation Suite & Scoring Assertion
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M2-010`..`040`
- **Blocks**: `META2-M4-040`, `META2-M5-010`
- **Writable Scope**: `tests/test_question_focus_router.py`, `tests/test_benchmark_rubric.py`
- **Description**: Build automated test runner executing the 60 benchmark queries against the Question Focus Router, Debate Engine, and Validator, asserting rubric score >= 85%.
- **DoR**: M2 benchmark router and debate synthesizer complete.
- **DoD**: Benchmark test suite completes with green assertion on all 6 domains.

#### `META2-M4-030` — SVG Visual Integrity & Dark Mode CSS Rendering Regression Suite
- **Role**: `qa_tester`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META2-M3-010`..`040`
- **Blocks**: `META2-M4-040`, `META2-M5-010`
- **Writable Scope**: `tests/test_svg_generator_contract.py`
- **Description**: Execute XML validity, bounding box, color contrast, and DOM structure contract tests across all 6 generated SVG chart types.
- **DoR**: M3 SVG visualizers and frontend integration complete.
- **DoD**: Zero XML syntax errors, valid viewBox attributes, responsive rendering verified.

#### `META2-M4-040` — Full System E2E Pipeline Integration & Multi-Agent Parity Verification
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META2-M4-010`, `META2-M4-020`, `META2-M4-030`
- **Blocks**: Milestone M5 start
- **Writable Scope**: `tests/test_e2e_metaphysics_pipeline.py`
- **Description**: Execute end-to-end integration test validating the entire flow: user query -> TST calculation -> 5-branch engines -> Question Router -> Multi-Agent Debate -> SVG Chart Generation -> Validator Scoring -> Final API Response.
- **DoR**: M4-010, M4-020, M4-030 PASS.
- **DoD**: E2E pipeline passes 100%; response latency < 2.5s locally.

---

### Milestone M5: Security Audit, Release Packaging, Documentation & Sprint Closure

#### `META2-M5-010` — Comprehensive Security Audit & Zero-Leak Secret Scanning
- **Role**: `code_reviewer`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META2-M4-040`
- **Blocks**: `META2-M5-020`
- **Writable Scope**: `plans/evidence/meta2/m5-security-audit.json`
- **Description**: Run full security scan using `project/core/code_reviewer.py`, verify zero API keys/secrets in codebase, inspect Pure ASCII logging compliance, and certify Rule 10 determinism.
- **DoR**: M4 E2E pipeline tests PASS.
- **DoD**: Security audit passes with zero critical/high findings; evidence JSON recorded.

#### `META2-M5-020` — Rule 21/22 Plan Completion, Archival & ReleaseNotes Compilation
- **Role**: `business_analyst`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META2-M5-010`
- **Blocks**: `META2-M5-030`
- **Writable Scope**: `ReleaseNotes.md`, `plans/plan.md`, `PROJECT_TASKS.md`
- **Description**: Compile full release notes into root `ReleaseNotes.md`, update task board status to 100% DONE, and maintain plans directory hygiene per Rule 22.
- **DoR**: `META2-M5-010` security audit complete.
- **DoD**: `ReleaseNotes.md` published with executive summary, deliverables, and test rollup.

#### `META2-M5-030` — AI Agent Ecosystem Sync & Multi-Platform Runtime Verification
- **Role**: `devops`
- **Priority / Effort**: `P1 / XS`
- **Depends On**: `META2-M5-020`
- **Blocks**: `META2-M5-040`
- **Writable Scope**: Generated platform configurations (`.claude/`, `.antigravity/`, `.codex/`)
- **Description**: Run `python3 scripts/sync_ai_agent_ecosystem.py --sync` and `--check` to verify multi-agent synchronization across Claude, Antigravity/Gemini, and Codex.
- **DoR**: `META2-M5-020` documentation updated.
- **DoD**: Ecosystem sync check returns exit code 0 (`[OK]`).

#### `META2-M5-040` — Sprint META-PLAN-002 Final Certification & Handoff Seal
- **Role**: `orchestrator`
- **Priority / Effort**: `P0 / XS`
- **Depends On**: `META2-M5-030`
- **Blocks**: None (Sprint Closure)
- **Writable Scope**: `plans/evidence/meta2/m5-sprint-seal.json`
- **Description**: Issue final orchestrator certification, seal the sprint evidence package, and transition task board to CLOSED.
- **DoR**: All tickets META2-M0-010 through META2-M5-030 DONE.
- **DoD**: Signed sprint seal evidence JSON generated; sprint formally closed.

---

## 5. 📊 Agile Task Board & Dependency Matrix Rollup

| Milestone | Purpose | Tickets | Assigned Roles | Critical Path |
|---|---|:---:|---|:---:|
| **M0** | Agile Governance, Test Baselines & Architecture Blueprint | 4 | `business_analyst`, `qa_tester`, `developer`, `code_reviewer` | YES |
| **M1** | Five-Branch Metaphysics Computational Core Deepening | 4 | `developer` | YES |
| **M2** | 6-Domain Question Benchmark Alignment & Focus Routing | 4 | `domain_master`, `developer`, `qa_tester` | YES |
| **M3** | SVG Dynamic Charting & Visual Rendering Engine | 4 | `developer`, `qa_tester` | NO (Parallel with M2) |
| **M4** | Automated Test Planes, Integration & E2E Regression | 4 | `qa_tester` | YES |
| **M5** | Security Audit, Release Packaging & Sprint Closure | 4 | `code_reviewer`, `business_analyst`, `devops`, `orchestrator` | YES |
| **TOTAL**| | **24**| | |

---

## 6. 🔒 Governance & Sign-Off Authority

- **Specification Status**: `APPROVED`
- **Agile Compliance**: 100% compliant with Rule 08, Rule 10, Rule 21, and Rule 22.
- **Document Authority**: Business System Analyst (`business_analyst`)
- **Master Orchestrator**: `orchestrator`
- **Sprint Seal Target**: `2026-08-31`
