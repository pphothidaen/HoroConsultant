# HoroConsultant — Master Agile Plan & Architecture Specifications

> **Repository**: `pphothidaen/HoroConsultant`  
> **Authority**: Master Orchestrator (`orchestrator`) & Business System Analyst (`business_analyst`)  
> **Governance Enforcement**: Rule 21 (Agile Governance) & Rule 22 (Plan Completion & Archival Mandate)  
> **Last Synchronized**: 2026-08-31T23:40:00+07:00 (Asia/Bangkok)  

---

<!-- AGILE-GOVERNANCE-SYNC-MRMAP:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-MRMAP-001)

**Recorded**: `2026-08-31T23:20:00+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `COMPLETED / SEALED`  
**Current Active Sprint**: Sprint SPRINT-METAPHYSICS-ROADMAP-001 (Five-Branch Metaphysics Roadmap & Computational Core across Steps 1-4)  
**Sprint Authority**: [`plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md`](plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md)  
**Active Milestones**: Sprint Sealed (All Steps 1-4 Completed)  
**Status Note**: All 16 tickets (`MRMAP-S1-010` through `MRMAP-S4-040`) are 100% DONE. Sprint SPRINT-METAPHYSICS-ROADMAP-001 is COMPLETED and sealed at 2026-08-31T23:30:00+07:00.  

### Synchronized Ticket Status Transitions (Sprint SPRINT-METAPHYSICS-ROADMAP-001 Final Seal)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `MRMAP-S1-010` | `DONE` | `DONE` | `domain_master` | `scripts/ocr_pdf_gemini.py`, `project/rag/obsidian_vault/` |
| `MRMAP-S1-020` | `DONE` | `DONE` | `developer` | `project/rag/ingest_vault.py` |
| `MRMAP-S1-030` | `DONE` | `DONE` | `developer` | `project/rag/vector_store.py` |
| `MRMAP-S1-040` | `DONE` | `DONE` | `qa_tester` | `project/tests/test_ingest_vault.py` |
| `MRMAP-S2-010` | `DONE` | `DONE` | `developer` | `project/core/tai_yi_engine.py`, `project/core/liu_ren_engine.py`, `project/core/qi_men_engine.py` |
| `MRMAP-S2-020` | `DONE` | `DONE` | `developer` | `project/core/bazi_engine.py`, `project/core/zi_wei_engine.py`, `project/core/qi_zheng_engine.py` |
| `MRMAP-S2-030` | `DONE` | `DONE` | `developer` | `project/core/iching_engine.py`, `project/core/liu_yao_engine.py`, `project/core/mei_hua_engine.py`, `project/core/xuan_kong_engine.py`, `project/core/san_he_engine.py`, `project/core/mian_xiang_engine.py` |
| `MRMAP-S2-040` | `DONE` | `DONE` | `developer` | `project/core/ze_ji_engine.py`, `project/core/thai_vedic_engine.py`, `project/core/western_uranian_engine.py`, `project/core/numerology_engine.py` |
| `MRMAP-S3-010` | `DONE` | `DONE` | `developer` | `project/rag/dataset_builder.py`, `project/rag/jsonl_exporter.py` |
| `MRMAP-S3-020` | `DONE` | `DONE` | `domain_master` | `project/data/synthetic_corpus_generator.py`, `project/data/sharegpt_dataset.jsonl` |
| `MRMAP-S3-030` | `DONE` | `DONE` | `developer` | `project/rag/external_finetune.py`, `project/data/sharegpt_dataset.jsonl` |
| `MRMAP-S3-040` | `DONE` | `DONE` | `devops` | `scripts/kaggle_notebook_manager.py`, `scripts/post_train_fuse.py` |
| `MRMAP-S4-010` | `DONE` | `DONE` | `developer` | `project/mcp_server.py`, `project/schemas/mcp_tools_v1.py` |
| `MRMAP-S4-020` | `DONE` | `DONE` | `developer` | `project/mcp_server.py`, `project/tests/test_e2e_mcp_svg.py` |
| `MRMAP-S4-030` | `DONE` | `DONE` | `developer` | `project/core/svg_generator.py`, `project/core/chart_bundler.py`, `project/static/css/glassmorphism_charts.css` |
| `MRMAP-S4-040` | `DONE` | `DONE` | `developer` | `project/static/js/chart_modal.js`, `project/tests/test_button_regression.py` |

---

<!-- AGILE-GOVERNANCE-SYNC-MRMAP:END -->

<!-- AGILE-GOVERNANCE-SYNC-META3:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-META3-003)

**Recorded**: `2026-08-31T22:17:30+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy2)  
**Gate**: `APPROVED`  
**Current Active Sprint**: Sprint META-PLAN-003 (MCP Full 16-Discipline Server Integration, Metaphysics Fine-Tuning Dataset Pipeline, and Glassmorphism Visual Endpoints across Milestones M0-M5)  
**Sprint Authority**: [`plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md`](plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md)  
**Active Milestones**: Sprint Sealed (All Milestones M0-M5 Completed)  
**Status Note**: All 24 tickets (`META3-M0-010` through `META3-M5-040`) are 100% DONE. Sprint META-PLAN-003 is COMPLETED and sealed at 2026-08-31T23:00:00+07:00.  

### Synchronized Ticket Status Transitions (Sprint META-PLAN-003 Wave 2 Admission)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `META3-M0-010` | `DONE` | `DONE` | `business_analyst` | `plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md` |
| `META3-M0-020` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m0_baseline_report.json` |
| `META3-M0-030` | `DONE` | `DONE` | `developer` | `project/schemas/mcp_tools_v1.py` |
| `META3-M0-040` | `DONE` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_003/m0_security_pre_impl.json` |
| `META3-M1-010` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M1-040` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m1_mcp_report.json` |
| `META3-M2-010` | `DONE` | `DONE` | `domain_master` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M2-040` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m2_dataset_pipeline_report.json` |
| `META3-M3-010` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-020` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-030` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M3-040` | `DONE` | `DONE` | `developer` | `plans/evidence/meta_plan_003/m3_visual_endpoints_report.json` |
| `META3-M4-010` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-020` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-030` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_test_planes_report.json` |
| `META3-M4-040` | `DONE` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_003/m4_integration_e2e_report.json` |
| `META3-M5-010` | `DONE` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-020` | `DONE` | `DONE` | `business_analyst` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-030` | `DONE` | `DONE` | `devops` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |
| `META3-M5-040` | `DONE` | `DONE` | `orchestrator` | `plans/evidence/meta_plan_003/m5_sprint_seal_report.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-META3:END -->

<!-- AGILE-GOVERNANCE-SYNC-META2:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-META2-002)

**Recorded**: `2026-08-31T22:00:00+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `COMPLETED / SEALED`  
**Current Active Sprint**: Sprint META-PLAN-002 (Milestones M0-M5 all 24 tickets 100% DONE & SEALED)  
**Sprint Authority**: [`plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md`](plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md)  
**Active Milestone**: Sprint Sealed (All Milestones M0-M5 Completed)  
**Status Note**: All 24 tickets (`META2-M0-010` through `META2-M5-040`) are `DONE`. Sprint META-PLAN-002 is 100% DONE & SEALED with comprehensive test verification (133/133 unit tests pass), 6-domain benchmark alignment (100% pass rate, 100/100 score), 18 responsive dynamic SVG visualizers, 0 secret leaks across 1,967 files, and 100% AI agent ecosystem parity.  

### Synchronized Ticket Status Transitions (Sprint META-PLAN-002 Final Seal)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `META2-M0-010` | `DONE` | `DONE` | `business_analyst` | `plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md` |
| `META2-M0-020` | `READY` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M0-030` | `READY` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M0-040` | `READY` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_002/m0_baseline_report.json` |
| `META2-M1-010` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M1-040` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m1_engines_report.json` |
| `META2-M2-010` | `BLOCKED` | `DONE` | `domain_master` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M2-040` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m2_benchmark_report.json` |
| `META2-M3-010` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-020` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-030` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M3-040` | `BLOCKED` | `DONE` | `developer` | `plans/evidence/meta_plan_002/m3_svg_visualizers_report.json` |
| `META2-M4-010` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-020` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-030` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M4-040` | `BLOCKED` | `DONE` | `qa_tester` | `plans/evidence/meta_plan_002/m4_test_planes_report.json` |
| `META2-M5-010` | `BLOCKED` | `DONE` | `code_reviewer` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-020` | `BLOCKED` | `DONE` | `business_analyst` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-030` | `BLOCKED` | `DONE` | `devops` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |
| `META2-M5-040` | `BLOCKED` | `DONE` | `orchestrator` | `plans/evidence/meta_plan_002/m5_sprint_seal_report.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-META2:END -->

<!-- AGILE-GOVERNANCE-SYNC-20260831:START -->
## Agile Governance & Task Board Status Sync (GOV-SYNC-009)

**Recorded**: `2026-08-31T21:36:08+07:00` (Asia/Bangkok)  
**Editor**: `business_analyst` (agy4)  
**Gate**: `APPROVED`  
**Current Active Sprint**: Sprint BROKER-PLAN-001 (Milestones B0-B6 all 29 tickets 100% DONE & SEALED), IDQ Operational (AUTH-02 SEALED & COMPLETED), Context Handoff v1 (CORE/ADAPTERS/POLICY/SYNC/QA/REVIEW DONE, INTEGRATION HOLD)  
**B6 Status Note**: Milestone B6 tickets (`BRK-B6-010`, `BRK-B6-020`, `BRK-B6-030`) are now `DONE`. Sprint BROKER-PLAN-001 is 100% DONE & SEALED. All 29 tickets are recorded as DONE with evidence references.  

### Synchronized Ticket Status Transitions (Wave 4C Completions: B6 Capacity Certification, Rollback, Closure)

| Ticket | Previous | New | Owner | Evidence |
|---|---|---|---|---|
| `BRK-B5-030` | `READY` | `DONE` | `agy_circuit_operator` | `b5-agy-circuit.json` |
| `BRK-B5-050` | `BLOCKED` | `DONE` | `agy1_admission_operator` | `b5-agy1-admission.json` |
| `BRK-B5-060` | `BLOCKED` | `DONE` | `agy2_admission_operator` | `b5-agy2-admission.json` |
| `BRK-B5-070` | `BLOCKED` | `DONE` | `agy3_admission_operator` | `b5-agy3-admission.json` |
| `BRK-B5-075` | `BLOCKED` | `DONE` | `agy4_admission_operator` | `b5-agy4-admission.json` |
| `BRK-B5-080A` | `BLOCKED` | `DONE` | `codex1_admission_operator` | `b5-codex1-admission.json` |
| `BRK-B5-080B` | `BLOCKED` | `DONE` | `codex2_admission_operator` | `b5-codex2-admission.json` |
| `BRK-B5-080C` | `BLOCKED` | `DONE` | `codex3_admission_operator` | `b5-codex3-admission.json` |
| `BRK-B6-010` | `READY` | `DONE` | `broker_qa_tester` | `b6-capacity-certification.json` |
| `BRK-B6-020` | `READY` | `DONE` | `broker_qa_tester` | `b6-rollback-drill.json` |
| `BRK-B6-030` | `READY` | `DONE` | `business_analyst` | `b6-sprint-closure.json` |

---

<!-- AGILE-GOVERNANCE-SYNC-20260831:END -->

## 🏛️ Master Architecture Specifications & System Topology

### 1. 🔮 Classical Metaphysics Computational Core (16 Disciplines)
The HoroConsultant engine implements deterministic mathematical modeling across 16 classical systems in pure Python with Rust PyO3 acceleration:
- **San Shi (三式)**:
  - `TaiYiEngine`: 16-path celestial star palaces, 9-palace matrix, epoch cycle boundaries (`project/core/tai_yi_engine.py`).
  - `LiuRenEngine`: 4 lessons (四課), 3 transmissions (初傳/中傳/末傳), 12 heavenly generals, noble spirit day/night rules (`project/core/liu_ren_engine.py`).
  - `QiMenEngine`: 24 solar terms, Yang/Yin Dun 1-9 Ju, 9 palaces, 8 doors, 9 stars, 8 deities (`project/core/qi_men_engine.py`).
- **Ming Xue (命學)**:
  - `BaZiEngine`: True Solar Time calculation ($TST = LMT + EoT$), midnight Zi hour early/late split, Lichun solar term boundaries, Ten Gods, Hidden Stems, Da Yun luck cycles (`project/core/bazi_engine.py`).
  - `ZiWeiEngine`: 12 Palaces, Ming/Shen Gong, 5 Element Bureaus, 14 Major Stars, 4 Si Hua transformations (`project/core/zi_wei_engine.py`).
  - `QiZhengSiYuEngine`: 7 governors, 4 shadow stars (Rahu, Ketu, Yuebei, Ziqi), 28 lunar mansions, Swiss Ephemeris (`project/core/qi_zheng_engine.py`).
- **Pu Shi (卜筮)**:
  - `IChingEngine`: Full 64 Hexagram lookup, dynamic moving lines 6/7/8/9, all-moving and all-static transitions (`project/core/iching_engine.py`).
  - `LiuYaoEngine`: Na Jia 6-line branch assignment, Shi/Ying line placement, Five Relatives (五親), Six Spirits (六神) (`project/core/liu_yao_engine.py`).
  - `MeiHuaEngine`: Ti/Yong 5-element dynamics, mutual (互卦) and transformed (變卦) hexagrams (`project/core/mei_hua_engine.py`).
- **Xiang Xue & Ze Ji (相學 / 擇吉)**:
  - `XuanKongEngine`: Period 9 (2024–2043), 24 mountains, sitting/facing star matrices, compass boundary angle wrapping (`project/core/xuan_kong_engine.py`).
  - `SanHeEngine`: 12 Life Stages Water Method (長生十二宮水法), 3 harmonies (`project/core/san_he_engine.py`).
  - `ZeJiEngine`: Imperial Calendar Date Selection, 12 Duty Officers (建除十二神), Year/Month Breaker clash detection (`project/core/ze_ji_engine.py`).
  - `MianXiangEngine`: 5-element face shapes, 12 facial palaces, 100-year age fortune flow (`project/core/mian_xiang_engine.py`).
- **Extended Astrologies & Numerology**:
  - `ThaiVedicEngine`: 12-Rashi Lagna, 8 Maha Thaksa Sri/Kalakini, 27 Nakshatras, Vimshottari Dasha (`project/core/thai_vedic_engine.py`).
  - `WesternUranianEngine`: Tropical planetary positions, 8 Uranian TNPs, midpoint formula $A+B-C$ (`project/core/western_uranian_engine.py`).
  - `NumerologyEngine`: Satta-Lek 7-Base 4-row matrix, Chaldean scoring (`project/core/numerology_engine.py`).

### 2. 🔌 Model Context Protocol (MCP) Server Architecture
The MCP Server (`project/mcp_server.py`) provides stdio JSON-RPC 2.0 transport conforming to MCP Specification 2024-11-05:
- **36-Tool Registry**:
  - 16 Calculation Engine Tools (`calculate_bazi`, `calculate_ziwei`, `calculate_qimen`, `calculate_liuren`, `calculate_taiyi`, `calculate_iching`, `calculate_liuyao`, `calculate_meihua`, `calculate_xuankong`, `calculate_sanhe`, `calculate_zeji`, `calculate_mianxiang`, `calculate_thaivedic`, `calculate_western_uranian`, `calculate_numerology`, `calculate_qizheng`).
  - 18 Dynamic SVG Visualizer Tools (`render_bazi_svg`, `render_ziwei_svg`, etc.).
  - Question Router Tool (`route_metaphysics_question`).
  - Multi-Agent Consensus Debate Tool (`debate_metaphysics_consensus`).
- **FastMCP Protocol Bridge**: Schema auto-generation, Pydantic type safety, and zero-overhead JSON-RPC dispatch.

### 3. 📚 Metaphysics Fine-Tuning Dataset & RAG Architecture
- **Obsidian Vault & FAISS Vector Store**: 11 classical Chinese treatises ingested, parsed, chunked, and indexed with semantic retrieval (`project/rag/vector_store.py`).
- **1,050-Dialogue ShareGPT Corpus**: Multi-turn consultation dialogues covering 16 disciplines × 6 domains (`Career`, `Wealth`, `Love`, `Health`, `Timing`, `Remediation`) with classical treatise citations (`project/data/sharegpt_dataset.jsonl`).
- **Format Exporters**: Automated export to ShareGPT, MLX, Unsloth, and Kaggle notebook training pipelines (`project/rag/external_finetune.py`, `scripts/kaggle_notebook_manager.py`).

### 4. 🎨 Glassmorphism Visual Rendering System
- **Dynamic SVG Generator**: 18 dynamic SVG visualizers (`project/core/svg_generator.py`) delivering high-DPI, XML-escaped responsive chart cards.
- **Glassmorphism CSS Design System**: Dark-mode Five Elements color tokens, glass cards, tooltips, responsive breakpoints (`project/static/css/glassmorphism_charts.css`).
- **Chart Bundler & Multi-Format Exporter**: Export API supporting SVG, PNG, and PDF outputs (`project/core/chart_bundler.py`).
- **Interactive Frontend Modal**: Pan/zoom viewer, tabbed 16-discipline navigation, keyboard shortcuts (`project/static/js/chart_modal.js`).

### 5. 🛡️ Agile Governance & Multi-Account Broker Architecture
- **Rule 21 (Agile Governance)**: Fail-closed capacity admission, 3 active lanes per alias ceiling, one-editor-per-file concurrency guard (`.agents/rules/21-agile-governance.md`).
- **Rule 22 (Plan Completion & Archival Mandate)**: Mandatory archival of completed plans, `/plans/` directory cleanliness, and `ReleaseNotes.md` synchronization (`.agents/rules/22-plan-completion-and-release-notes.md`).
- **macOS Keychain Account Broker**: Swift keychain bridge with Python wrapper (`scripts/ai_account_keychain_broker.swift`, `scripts/agent_broker_wrapper.py`).

---

## 🗄️ Comprehensive Archived Plans Directory Index

All completed sprint specifications, historical GRILL reports, and task boards have achieved zero-active state and are archived per Rule 22:

| Sprint / Release | Archive Directory | Archived Planning Documents |
|---|---|---|
| **Metaphysics Roadmap** | [`plans/archive/2026-08-31-metaphysics-roadmap/`](plans/archive/2026-08-31-metaphysics-roadmap/) | [`metaphysics_learning_roadmap.md`](plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md) |
| **META-PLAN-003** | [`plans/archive/2026-08-31-meta-plan-003/`](plans/archive/2026-08-31-meta-plan-003/) | [`meta_plan_003_mcp_dataset_integration_spec.md`](plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md) |
| **META-PLAN-002** | [`plans/archive/2026-08-31-meta-plan-002/`](plans/archive/2026-08-31-meta-plan-002/) | [`meta_plan_002_metaphysics_deepening_spec.md`](plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md)<br>[`question_forecast_alignment_spec.md`](plans/archive/2026-08-31-meta-plan-002/question_forecast_alignment_spec.md) |
| **BROKER-PLAN-001** | [`plans/archive/2026-08-31-broker-plan-001/`](plans/archive/2026-08-31-broker-plan-001/) | [`broker_atomic_tickets_20260831.md`](plans/archive/2026-08-31-broker-plan-001/broker_atomic_tickets_20260831.md)<br>[`account_broker_installation_runbook_20260831.md`](plans/archive/2026-08-31-broker-plan-001/account_broker_installation_runbook_20260831.md) |
| **Release v1.3.0** | [`plans/archive/2026-08-31-release-v1.3.0/`](plans/archive/2026-08-31-release-v1.3.0/) | [`release_atomic_tickets_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/release_atomic_tickets_20260831.md)<br>[`release_atomic_ticket_audit_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/release_atomic_ticket_audit_20260831.md)<br>[`agile_governance_refactor_spec_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/agile_governance_refactor_spec_20260831.md)<br>[`native_lane_capacity_loadtest_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/native_lane_capacity_loadtest_20260831.md)<br>[`RESTART_HANDOFF.md`](plans/archive/2026-08-31-release-v1.3.0/RESTART_HANDOFF.md)<br>[`todo_tasks_plan.md`](plans/archive/2026-08-31-release-v1.3.0/todo_tasks_plan.md) |
| **Historical Archive** | [`plans/archive/2026-08-31-historical-plans/`](plans/archive/2026-08-31-historical-plans/) | [`historical_plans_archive.md`](plans/archive/2026-08-31-historical-plans/historical_plans_archive.md)<br>[`historical_tasks_archive.md`](plans/archive/2026-08-31-historical-plans/historical_tasks_archive.md) |
