# 🌐 Sprint META-PLAN-003: Model Context Protocol (MCP) Full 16-Discipline Server Integration, Metaphysics Fine-Tuning Dataset Pipeline & Glassmorphism Visual Endpoints Specification

**Document ID**: `META-PLAN-003-SPEC`  
**Date**: `2026-08-31T22:05:03+07:00` (Asia/Bangkok)  
**Lead Authority**: Business System Analyst (`business_analyst`) & Master Orchestrator (`orchestrator`)  
**Gate Status**: `APPROVED`  
**Authorized Next Phase**: Milestone M0 (Test Baselines & Schema Contracts)  
**Assigned Editor**: `business_analyst`  
**Writable Ownership Scope**: `plans/meta_plan_003_mcp_dataset_integration_spec.md`, `PROJECT_TASKS.md`, `plans/plan.md`  

---

## 1. 📋 Executive Summary & Sprint Objective

Sprint **META-PLAN-003** marks the integration, dataset curation, and protocol standardization phase of the **HoroConsultant** enterprise platform. Building upon the mathematically deepened 16 classical metaphysics computational engines and dynamic SVG visualizers finalized in META-PLAN-002, this sprint unites the computational core with external client ecosystems, fine-tuning infrastructure, and high-performance frontend interfaces across four strategic pillars:

1. **Model Context Protocol (MCP) Full 16-Discipline Server Integration**:
   - Upgrading `project/mcp_server.py` to expose all 16 computational engines via standard Model Context Protocol (MCP) JSON-RPC / stdio transport.
   - Comprehensive tool schema manifest exposing all 16 engines:
     - **San Shi (三式)**: Tai Yi Shen Shu (`tai_yi_calculate`), Da Liu Ren (`liuren_calculate`), Qi Men Dun Jia (`qimen_calculate`).
     - **Ming Xue (命學)**: BaZi (`bazi_calculate`), Zi Wei Dou Shu (`ziwei_calculate`), Qi Zheng Si Yu (`qi_zheng_calculate`).
     - **Bu Shi (卜筮)**: I Ching (`iching_calculate`), Liu Yao (`liu_yao_calculate`), Mei Hua Yi Shu (`mei_hua_calculate`).
     - **Xiang Xue (相學)**: Xuan Kong Flying Stars (`xuankong_calculate`), San He Feng Shui (`san_he_calculate`), Mian Xiang Face Reading (`mian_xiang_analyze`).
     - **Ze Ji & Extended Systems (擇吉 & 術數)**: Ze Ji Imperial Date Selection (`zeji_calculate`), Thai Suriyayart Vedic (`thaivedic_calculate`), Western Tropical & Uranian (`western_calculate`), Satta-Lek 7-Base Numerology (`numerology_calculate`).
   - Seamless interoperability bridge for `thClaws` (Rust agent harness), AGY subagents, and Claude Desktop.

2. **Metaphysics Fine-Tuning Dataset Pipeline & Corpus Distillation**:
   - Building a production-grade synthetic dataset pipeline (`scripts/extract_dataset_mlx.py`, `scripts/harvest_hf_liked_datasets.py`, `project/data/sharegpt_dataset.jsonl`) extracting canonical multi-turn consultations.
   - Standardized formatting for ShareGPT, MLX (Apple Silicon), and Unsloth / HuggingFace fine-tuning frameworks.
   - 6-Domain multi-turn consultation dialogues anchored in classical treatise citations with strict automated quality scoring, deduplication, and hallucination filtering.

3. **Glassmorphism Visual Endpoints & Dynamic SVG Interactive Rendering**:
   - Dedicated visual rendering endpoints in FastAPI (`/api/v1/visuals/{discipline}`) serving dark-mode Glassmorphism SVG chart cards for all 16 disciplines.
   - Enhanced SVG CSS theming, interactive DOM tooltips, vector scaling, and multi-format visual export capabilities (SVG/PNG/PDF).
   - Responsive UI dashboard integration verified across mobile, tablet, and desktop viewports.

4. **Automated Test Planes & Quality Verification**:
   - End-to-end regression suites ensuring 100% deterministic mathematical accuracy across all 16 MCP tool invocations, dataset schema validity, and SVG rendering integrity per Rule 21 and Rule 22.

---

## 2. 🔥 9-Dimension GRILL REPORT

```text
================================================================================
                    GRILL GATE EVALUATION RECORD (META-PLAN-003)
================================================================================
Gate Status    : [APPROVED]
Grilled By     : orchestrator (gpt-5.6-sol / high) 🤝 business_analyst (agy4)
Target Scope   : MCP 16-Discipline Server, Dataset Pipeline, Visual Endpoints
Evidence Base  : Rule 08 (GRILL), Rule 10 (Deterministic Math), Rule 21 (Agile),
                 Rule 22 (Release Notes), 133/133 Unit Test Green Baseline
================================================================================
```

### D1 — Scope Boundary

- **IN Scope**:
  1. Complete MCP tool definitions and JSON-RPC / stdio server in `project/mcp_server.py` supporting all 16 metaphysics disciplines with full parameter schemas and tool manifests.
  2. Dataset generation, transformation, and distillation pipeline (`scripts/extract_dataset_mlx.py`, `scripts/harvest_hf_liked_datasets.py`, `scripts/kaggle_dataset_sync_automation.py`, `project/data/sharegpt_dataset.jsonl`).
  3. FastAPI visual rendering routes in `project/routers/visual_router.py` (or `project/routers/astrology_router.py`) and dynamic SVG enhancements in `project/core/svg_generator.py`.
  4. Contract and regression test suites (`tests/test_mcp_server_contract.py`, `tests/test_dataset_pipeline.py`, `tests/test_visual_endpoints.py`, `tests/test_e2e_mcp_svg.py`).
  5. Governance documentation, sprint tracking, and task board synchronization (`plans/meta_plan_003_mcp_dataset_integration_spec.md`, `PROJECT_TASKS.md`, `plans/plan.md`).
- **OUT of Scope**:
  1. Live external deployment to Hugging Face Space or Vercel (reserved for subsequent release sprint).
  2. Executing live training jobs on Kaggle GPU (model weights stay frozen; pipeline prepares and validates training artifacts only).
  3. Modifying underlying 16 deterministic calculation engines (`project/core/*_engine.py`) unless required for MCP interface compliance.
  4. Direct modification of generated platform mirrors (`.codex/agents/*.toml`).
- **Interface Stability**:
  - All existing FastAPI endpoints (`/api/calculate`, `/api/debate`, `/api/render-svg`) retain 100% backward compatibility.
  - MCP JSON-RPC protocol conforms to Model Context Protocol Specification 2024-11-05.
  - Output JSON structures for all 16 discipline calculations match typed Pydantic contracts.

### D2 — Requirement Delta

- **Added**:
  - Full 16-discipline tool registry in `project/mcp_server.py` returning structured JSON and inline SVG snippets.
  - FastMCP / thClaws stdio bridge compatibility mode.
  - Multi-discipline synthetic consultation dataset generator formatting 1,000+ high-quality ShareGPT conversation turns.
  - Glassmorphic visual rendering endpoints for all 16 metaphysics disciplines with responsive CSS and tooltips.
  - Comprehensive automated test harness for MCP tool calls, dataset integrity, and visual rendering DOM contracts.
- **Refined**:
  - Vector store RAG search integration inside MCP server with top-k text relevance filtering.
  - ShareGPT export pipeline with token-budget validation and automated deduplication.
- **Removed (Rule 10 Purge)**:
  - Partial 4-tool MCP manifest superseded by full 16-tool registry.
  - Legacy unvalidated dataset generation stubs.

### D3 — Acceptance Criteria & Verification Matrix

| # | Acceptance Criterion | Verification Tool / Command | Owner |
|---|---|---|---|
| 1 | `project/mcp_server.py --manifest` outputs valid JSON containing all 16 registered metaphysics tools | `python3 project/mcp_server.py --manifest` | `developer` |
| 2 | All 16 MCP tool functions execute deterministically and return valid JSON payloads | `python3 -m pytest tests/test_mcp_server_contract.py` | `qa_tester` |
| 3 | Dataset generation pipeline exports valid ShareGPT JSONL with zero syntax or tokenization errors | `python3 -m pytest tests/test_dataset_pipeline.py` | `qa_tester` |
| 4 | Visual endpoints return valid SVG XML with dark-mode Glassmorphism styling across all 16 disciplines | `python3 -m pytest tests/test_visual_endpoints.py` | `qa_tester` |
| 5 | Full system E2E pipeline passes (MCP invocation -> Engine compute -> Dataset generation -> SVG rendering) | `python3 -m pytest tests/test_e2e_mcp_svg.py` | `qa_tester` |
| 6 | Zero security vulnerabilities and zero secret leaks detected across codebase | `python3 project/core/code_reviewer.py --review` | `code_reviewer` |
| 7 | Cross-agent ecosystem remains 100% synchronized across Claude, Antigravity, and Codex | `python3 scripts/sync_ai_agent_ecosystem.py --check` | `devops` |

### D4 — Constraints & Safeguards

1. **Rule 10 Deterministic Calculation Boundary**: Pure Python math for all astronomical, astrological, and numerical algorithms. MCP server routes data to deterministic engines; LLMs are strictly prohibited from performing arithmetic or chart layout geometry.
2. **Pure ASCII Logging**: All loggers, print statements, and test outputs MUST use ASCII tags (`[OK]`, `[INFO]`, `[ERROR]`, `[WARNING]`, `[START]`, `[DONE]`).
3. **One-Editor Ownership Boundary**: Concurrent tickets must have strictly disjoint writable files per Rule 21.
4. **Zero-Cost AI Governance**: Local-first execution using Ollama Qwen2.5:7b, with Gemini Flash fallback strictly for external validation.
5. **Kaggle GPU Accelerator Constraint**: Dataset export pipeline must generate artifacts compatible with offline Kaggle/MLX fine-tuning without requiring active remote GPU execution.

### D5 — Sub-Agent Allocation & Ownership

- `orchestrator`: Overall sprint execution DAG, consensus, and final handoff seal.
- `business_analyst`: Agile task board governance, GRILL spec authoring, and ReleaseNotes compilation per Rules 21 & 22.
- `developer`: MCP server implementation, dataset exporters, visual endpoints, and SVG styling.
- `qa_tester`: Test fixture authoring, MCP contract tests, dataset validation suite, and E2E regression.
- `code_reviewer`: Security audit, Pure ASCII verification, and Rule 10 boundary inspection.
- `devops`: Ecosystem synchronization and platform manifest verification.
- `domain_master`: Multi-branch synthetic dialogue fixtures and classical treatise citation verification.

### D6 — Assumption Register

| Assumption / Invariant | Status | Validation Method |
|---|---|---|
| MCP tool schemas conform to Model Context Protocol specification | `[CONFIRMED]` | Verified against `project/mcp_server.py --manifest` |
| 16 deterministic engines produce valid structured dictionaries | `[CONFIRMED]` | Verified in `tests/test_five_branch_metaphysics.py` |
| ShareGPT JSONL format matches HuggingFace / MLX dataset loader contracts | `[CONFIRMED]` | Validated via `scripts/extract_dataset_mlx.py` |
| SVG outputs are valid standalone XML with dark-mode Glassmorphism styles | `[CONFIRMED]` | Contract tests in `tests/test_svg_generator_contract.py` |

### D7 — Risk & Rollback Strategy

- **Risk 1: MCP Tool Parameter Type Mismatch in Client Runtimes (thClaws / Claude Desktop)**:
  - *Mitigation*: Strict Pydantic typing and default parameter fallbacks for all 16 MCP tool handlers.
  - *Rollback*: Revert to core `HoroMCPTools` baseline adapter.
- **Risk 2: Dataset Token Bloat or Formatting Corruption in Multi-Turn Dialogues**:
  - *Mitigation*: Automated JSONL line-by-line schema validation, token length truncation, and deduplication filter.
  - *Rollback*: Revert dataset generation scripts to previous tagged release.
- **Risk 3: SVG Rendering Performance Degradation on Mobile Viewports**:
  - *Mitigation*: Clean vector paths, inline CSS scoping, and responsive `viewBox` geometry without external fonts.
  - *Rollback*: Revert SVG template changes via Git commit rollback.

### D8 — Token & Capacity Efficiency Strategy

- High-tier models (`gpt-5.6-sol`, `Gemini 3.7 Pro`) reserved for architecture governance, GRILL review, and synthesis.
- Mid-tier / Local models (`qwen2.5:7b`) utilized for local reasoning, dataset generation, and code implementation.
- All test runs and command executions stream trimmed ASCII logs to preserve conversation context.

### D9 — Metaphysics Domain Alignment & Canonical References

Every MCP tool and dataset dialogue turn is anchored in authoritative classical literature across all 16 disciplines:
1. **Tai Yi Shen Shu (太乙神數)**: 《太乙金鏡式經》, 《太乙統宗寶鑒》.
2. **Da Liu Ren (大六壬)**: 《六壬大全》, 《六壬指南》, 《大六壬心印賦》.
3. **Qi Men Dun Jia (奇門遁甲)**: 《煙波釣叟歌》, 《奇門遁甲大全》.
4. **BaZi (八字命理)**: 《淵海子平》, 《滴天髓》, 《子平真詮》, 《三命通會》.
5. **Zi Wei Dou Shu (紫微斗數)**: 《紫微斗數全書》, 《太微賦》, 《骨髓賦》.
6. **Qi Zheng Si Yu (七政四餘)**: 《果老星宗》, 《星度指南》.
7. **Zhou Yi / I Ching (周易)**: 《易經》, 《十翼》, 《周易折中》.
8. **Liu Yao (六爻預測)**: 《卜筮正宗》, 《增刪卜易》, 《易隱》.
9. **Mei Hua Yi Shu (梅花易數)**: 《梅花易數》 (Shao Yong / 邵雍).
10. **Xuan Kong Feng Shui (玄空風水)**: 《青囊奧語》, 《沈氏玄空學》, Period 9 《九運風水寶典》.
11. **San He Feng Shui (三合風水)**: 《地理五訣》, 《催官篇》.
12. **Ze Ji Imperial Selection (擇吉學)**: 《協紀辨方書》 (Qing Imperial Court / 四庫全書).
13. **Mian Xiang Physiognomy (相學)**: 《麻衣神相》, 《柳莊相法》, 《神相鐵關刀》.
14. **Thai Suriyayart & Vedic Astrology**: ตำราคัมภีร์สุริยยาตร์, มหาทักษาพยากรณ์, วิมโศตตริทศา (Vimshottari Dasha).
15. **Western Tropical & Uranian Astrology**: Ptolemy's *Tetrabiblos*, Alfred Witte's *Rules for Planetary Pictures* (Hamburg School).
16. **Satta-Lek 7-Base Numerology**: ตำราสัตเลข ๗ ฐาน ๔ ชั้น, ศาสตร์ตัวเลขคาลเดียน (Chaldean Numerology).

---

## 3. 🗺️ Sprint META-PLAN-003 Milestone Breakdown & Workflow DAG (M0 - M5)

```text
+-----------------------------------------------------------------------------------+
|                        SPRINT META-PLAN-003 WORKFLOW DAG                          |
+-----------------------------------------------------------------------------------+
  [M0] Agile Governance, Test Baselines & Architecture Blueprint
   │
   ├──> [M1] MCP Full 16-Discipline Server Integration (Tools, JSON-RPC, thClaws)
   │     │
   │     ├──> [M2] Metaphysics Fine-Tuning Dataset Pipeline & Corpus Exporters
   │     │     │
   │     └───> [M3] Glassmorphism Visual Endpoints & Dynamic SVG Rendering
   │           │
   └───────────┴──> [M4] Automated Test Planes, Integration & E2E Regression
                     │
                     └──> [M5] Security Audit, Release Packaging & Sprint Closure
```

---

## 4. 📝 Detailed Ticket Ledger (META3-M0-010 through META3-M5-040)

### Milestone M0: Agile Governance, Test Baselines & Architecture Blueprint

#### `META3-M0-010` — Plan & GRILL Specification Authoring
- **Role**: `business_analyst`
- **Priority / Effort**: `P0 / S`
- **Depends On**: None
- **Blocks**: `META3-M0-020`, `META3-M0-030`
- **Writable Scope**: `plans/meta_plan_003_mcp_dataset_integration_spec.md`, `PROJECT_TASKS.md`, `plans/plan.md`
- **Description**: Formulate the comprehensive 9-dimension GRILL specification, decompose sprint milestones M0 through M5 into 24 atomic tickets, and establish the Agile task board in `PROJECT_TASKS.md` adhering to Rule 21 and Rule 22.
- **Definition of Ready (DoR)**:
  - [x] GRILL dimensions reviewed and confirmed.
  - [x] Agile governance rules (Rule 21, Rule 22) loaded.
- **Definition of Done (DoD)**:
  - [x] `plans/meta_plan_003_mcp_dataset_integration_spec.md` created with full 9-dimension GRILL report.
  - [x] `PROJECT_TASKS.md` updated with META-PLAN-003 ticket board.
  - [x] `plans/plan.md` updated with Governance Sync header.

#### `META3-M0-020` — Baseline Test Freeze & Provenance Manifest
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META3-M0-010`
- **Blocks**: `META3-M1-010`, `META3-M2-010`, `META3-M3-010`
- **Writable Scope**: `plans/test_provenance/meta3-baseline-20260831.json`, `plans/evidence/meta_plan_003/m0_baseline_report.json`
- **Description**: Execute the full baseline test suite (133+ unit tests), verify zero regressions, freeze test hashes into an immutable test provenance manifest, and record baseline execution proof.
- **DoR**: `META3-M0-010` DONE; test suite clean.
- **DoD**: Manifest generated and signed with Git commit hash and timestamp; 100% test pass.

#### `META3-M0-030` — MCP 16-Discipline Protocol Schema & Tool Registry Architecture
- **Role**: `developer`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M0-010`
- **Blocks**: `META3-M1-010`..`040`
- **Writable Scope**: `project/schemas/mcp_schemas.py`, `project/schemas/__init__.py`
- **Description**: Define standardized Pydantic data schemas and JSON-RPC parameter models for all 16 metaphysics disciplines, ensuring typed input/output validation across MCP tool boundaries.
- **DoR**: `META3-M0-010` DONE; domain requirements specified.
- **DoD**: Typed schemas validated with pytest contract tests.

#### `META3-M0-040` — Ecosystem Sync & Pre-Implementation Gate Review
- **Role**: `code_reviewer`
- **Priority / Effort**: `P1 / XS`
- **Depends On**: `META3-M0-010`, `META3-M0-020`, `META3-M0-030`
- **Blocks**: Milestone M1, M2, M3 start
- **Writable Scope**: `plans/evidence/meta_plan_003/m0_pre_impl_review.json`
- **Description**: Perform independent gate review of M0 deliverables, verify zero-leak secrets, validate Rule 10 deterministic boundaries, and sign off on entry into M1/M2/M3.
- **DoR**: M0-010, M0-020, M0-030 DONE.
- **DoD**: Review verdict `PASS` recorded in evidence JSON.

---

### Milestone M1: Model Context Protocol (MCP) Full 16-Discipline Server Integration

#### `META3-M1-010` — San Shi & Ming Xue MCP Tool Implementation
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M0-040`
- **Blocks**: `META3-M1-040`, `META3-M4-010`
- **Writable Scope**: `project/mcp_server.py`
- **Description**: Register and expose full MCP tools for San Shi (`tai_yi_calculate`, `liuren_calculate`, `qimen_calculate`) and Ming Xue (`bazi_calculate`, `ziwei_calculate`, `qi_zheng_calculate`) with complete docstrings, parameter schemas, and error handling.
- **DoR**: M0 gate review PASSED; schemas locked.
- **DoD**: All 6 tools execute and return deterministic JSON responses matching classical algorithms.

#### `META3-M1-020` — Bu Shi & Xiang Xue MCP Tool Implementation
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M0-040`
- **Blocks**: `META3-M1-040`, `META3-M4-010`
- **Writable Scope**: `project/mcp_server.py`
- **Description**: Register and expose full MCP tools for Bu Shi (`iching_calculate`, `liu_yao_calculate`, `mei_hua_calculate`) and Xiang Xue (`xuankong_calculate`, `san_he_calculate`, `mian_xiang_analyze`) in `HoroMCPTools`.
- **DoR**: M0 gate review PASSED.
- **DoD**: All 6 divination and feng shui/physiognomy tools pass contract assertions.

#### `META3-M1-030` — Ze Ji, Thai-Vedic, Uranian & Numerology MCP Tool Implementation
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META3-M0-040`
- **Blocks**: `META3-M1-040`, `META3-M4-010`
- **Writable Scope**: `project/mcp_server.py`
- **Description**: Register and expose MCP tools for Imperial Date Selection (`zeji_calculate`), Thai-Vedic Suriyayart (`thaivedic_calculate`), Western Tropical/Uranian (`western_calculate`), and Satta-Lek Numerology (`numerology_calculate`).
- **DoR**: M0 gate review PASSED.
- **DoD**: All 4 remaining tools fully exposed with verified calculation output.

#### `META3-M1-040` — MCP Server Stdio & JSON-RPC Protocol Transport with FastMCP / thClaws Bridge
- **Role**: `developer`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META3-M1-010`, `META3-M1-020`, `META3-M1-030`
- **Blocks**: `META3-M4-010`
- **Writable Scope**: `project/mcp_server.py`
- **Description**: Implement standard JSON-RPC 2.0 stdio transport loop in `project/mcp_server.py`, complete `get_mcp_manifest()` tool catalog exposing all 16 disciplines, and verify thClaws / Claude Desktop compatibility.
- **DoR**: All 16 MCP tool implementations complete.
- **DoD**: `python3 project/mcp_server.py --manifest` emits valid JSON with 16 tools; stdio loop responds correctly to `tools/list` and `tools/call`.

---

### Milestone M2: Metaphysics Fine-Tuning Dataset Pipeline & ShareGPT / HuggingFace Exporters

#### `META3-M2-010` — Multi-Branch Synthetic Consultation Corpus Generator
- **Role**: `domain_master`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M0-040`
- **Blocks**: `META3-M2-020`, `META3-M4-020`
- **Writable Scope**: `project/data/synthetic_corpus_generator.py`, `tests/fixtures/synthetic_prompts.json`
- **Description**: Build multi-branch dialogue generator producing realistic user queries across all 6 consultation domains (Career, Wealth, Love, Health, Auspicious Timing, Remediation) paired with multi-discipline chart interpretations.
- **DoR**: M0 gate review PASSED.
- **DoD**: 200+ distinct scenario prompts authored and categorized across 16 disciplines.

#### `META3-M2-020` — Classical Treatise RAG Ingestion & QA Pair Distillation Pipeline
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M2-010`
- **Blocks**: `META3-M2-030`, `META3-M4-020`
- **Writable Scope**: `scripts/extract_dataset_mlx.py`, `scripts/harvest_hf_liked_datasets.py`
- **Description**: Implement pipeline extracting high-quality question-answer consultation pairs distilled from FAISS vector store classical treatises and deterministic engine chart outputs.
- **DoR**: `META3-M2-010` scenario prompts ready.
- **DoD**: Pipeline extracts structured consultation records with canonical citations.

#### `META3-M2-030` — ShareGPT / MLX / Unsloth Training Format Export & Tokenizer Validation
- **Role**: `developer`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M2-020`
- **Blocks**: `META3-M2-040`, `META3-M4-020`
- **Writable Scope**: `project/data/sharegpt_dataset.jsonl`, `scripts/kaggle_dataset_sync_automation.py`
- **Description**: Format distilled consultation dialogues into standard ShareGPT JSONL format (`conversations`: `from`: `human`/`gpt`, `value`), validate token lengths with Qwen tokenizer, and ensure compatibility with MLX / Unsloth fine-tuning.
- **DoR**: `META3-M2-020` distillation complete.
- **DoD**: Valid `project/data/sharegpt_dataset.jsonl` produced with 1,000+ validated multi-turn examples.

#### `META3-M2-040` — Dataset Quality Scoring, Deduplication & Hallucination Guard Filter
- **Role**: `qa_tester`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M2-030`
- **Blocks**: `META3-M4-020`
- **Writable Scope**: `tests/test_dataset_pipeline.py`, `project/validator.py`
- **Description**: Run automated quality scoring against generated dataset, filter near-duplicates via MinHash/cosine similarity, and assert 100% adherence to deterministic chart facts (zero arithmetic hallucination).
- **DoR**: `META3-M2-030` ShareGPT dataset generated.
- **DoD**: Dataset passes 100% of quality, deduplication, and fact-checking assertions.

---

### Milestone M3: Glassmorphism Visual Endpoints & Dynamic SVG Interactive Rendering

#### `META3-M3-010` — 16-Discipline SVG Visualizer Endpoints & FastAPI Route Binding
- **Role**: `developer`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M0-040`
- **Blocks**: `META3-M3-020`, `META3-M4-030`
- **Writable Scope**: `project/routers/visual_router.py`, `project/main.py`
- **Description**: Create dedicated FastAPI router `visual_router` providing HTTP GET/POST endpoints (`/api/v1/visuals/{discipline}`) returning SVG charts for all 16 disciplines.
- **DoR**: M0 gate review PASSED.
- **DoD**: Endpoints mounted in `project/main.py` and responding with valid `image/svg+xml` content.

#### `META3-M3-020` — Dark-Mode Glassmorphism SVG CSS Theme Styling & Interactive Tooltips
- **Role**: `developer`
- **Priority / Effort**: `P1 / M`
- **Depends On**: `META3-M3-010`
- **Blocks**: `META3-M3-030`, `META3-M4-030`
- **Writable Scope**: `project/core/svg_generator.py`, `project/static/css/glassmorphism_charts.css`
- **Description**: Refine SVG generator styling with cohesive dark-mode Glassmorphism aesthetics (gradient overlays, backdrop blurs, luminous stroke accents) and embed interactive CSS tooltips for stars, stems, and palaces.
- **DoR**: `META3-M3-010` visual routes active.
- **DoD**: High-DPI, aesthetic SVGs render cleanly with embedded CSS styling and tooltip triggers.

#### `META3-M3-030` — Comprehensive Visual Export API (SVG/PNG/PDF) & Chart Bundler
- **Role**: `developer`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M3-020`
- **Blocks**: `META3-M3-040`, `META3-M4-030`
- **Writable Scope**: `project/routers/visual_router.py`, `project/core/chart_bundler.py`
- **Description**: Add visual export capabilities allowing users to download single charts or bundled multi-discipline consultation reports in SVG, PNG, and PDF formats.
- **DoR**: `META3-M3-020` SVG visualizers styled.
- **DoD**: Export endpoints verified with integration tests.

#### `META3-M3-040` — Responsive Frontend UI Modal & Canvas Integration with DOM Validation
- **Role**: `developer`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M3-030`
- **Blocks**: `META3-M4-030`
- **Writable Scope**: `project/static/index.html`, `project/static/js/chart_modal.js`
- **Description**: Embed interactive SVG chart viewer modal in web frontend with zoom/pan capabilities, responsive viewport resizing, and tabbed 16-discipline navigation.
- **DoR**: `META3-M3-030` export API complete.
- **DoD**: Frontend modal displays charts seamlessly across all tested viewports.

---

### Milestone M4: Automated Test Planes, Integration & End-to-End Regression

#### `META3-M4-010` — MCP Protocol & 16-Discipline Tool Harness Unit Test Suite
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M1-040`
- **Blocks**: `META3-M4-040`, `META3-M5-010`
- **Writable Scope**: `tests/test_mcp_server_contract.py`
- **Description**: Comprehensive unit test suite executing all 16 MCP tool functions via stdio / JSON-RPC mock harness, verifying parameter validation, output schema adherence, and error recovery.
- **DoR**: Milestone M1 complete.
- **DoD**: 100% pass rate across all 16 MCP tool contract tests.

#### `META3-M4-020` — Dataset Pipeline Integrity & Schema Validation Test Suite
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META3-M2-040`
- **Blocks**: `META3-M4-040`, `META3-M5-010`
- **Writable Scope**: `tests/test_dataset_pipeline.py`
- **Description**: Build automated test runner validating the ShareGPT dataset JSONL syntax, conversation turn structure, token distributions, and zero-arithmetic-drift invariants.
- **DoR**: Milestone M2 complete.
- **DoD**: Dataset validation test suite passes with zero errors.

#### `META3-M4-030` — Visual SVG Rendering & DOM Viewport Responsiveness Test Suite
- **Role**: `qa_tester`
- **Priority / Effort**: `P1 / S`
- **Depends On**: `META3-M3-040`
- **Blocks**: `META3-M4-040`, `META3-M5-010`
- **Writable Scope**: `tests/test_visual_endpoints.py`
- **Description**: Execute XML syntax verification, viewBox scaling, color contrast, and HTTP route response tests across all 16 visual endpoints.
- **DoR**: Milestone M3 complete.
- **DoD**: All visual endpoints return 200 OK and valid XML/SVG.

#### `META3-M4-040` — Full System E2E Pipeline Integration Verification
- **Role**: `qa_tester`
- **Priority / Effort**: `P0 / M`
- **Depends On**: `META3-M4-010`, `META3-M4-020`, `META3-M4-030`
- **Blocks**: Milestone M5 start
- **Writable Scope**: `tests/test_e2e_mcp_svg.py`, `plans/evidence/meta_plan_003/m4_integration_e2e_report.json`
- **Description**: Execute end-to-end integration test validating the entire connected flow: MCP tool request -> Engine computation -> Dataset distillation -> SVG visual rendering -> API response.
- **DoR**: M4-010, M4-020, M4-030 PASS.
- **DoD**: E2E integration pipeline passes 100%; evidence report recorded.

---

### Milestone M5: Security Audit, Release Packaging & Sprint Closure

#### `META3-M5-010` — Comprehensive Security Audit & Zero-Leak Secret Scanning
- **Role**: `code_reviewer`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META3-M4-040`
- **Blocks**: `META3-M5-020`
- **Writable Scope**: `plans/evidence/meta_plan_003/m5_security_audit_report.json`
- **Description**: Run full security scan using `project/core/code_reviewer.py`, verify zero API keys/secrets in codebase, inspect Pure ASCII logging compliance, and certify Rule 10 determinism.
- **DoR**: M4 E2E pipeline tests PASS.
- **DoD**: Security audit passes with zero critical/high findings; evidence JSON recorded.

#### `META3-M5-020` — Rule 21/22 Plan Completion & ReleaseNotes Synchronization
- **Role**: `business_analyst`
- **Priority / Effort**: `P0 / S`
- **Depends On**: `META3-M5-010`
- **Blocks**: `META3-M5-030`
- **Writable Scope**: `ReleaseNotes.md`, `plans/plan.md`, `PROJECT_TASKS.md`
- **Description**: Compile full release notes into root `ReleaseNotes.md`, update task board status to 100% DONE, and maintain plans directory hygiene per Rule 22.
- **DoR**: `META3-M5-010` security audit complete.
- **DoD**: `ReleaseNotes.md` published with executive summary, deliverables, and test rollup.

#### `META3-M5-030` — AI Agent Ecosystem Sync & Multi-Platform Runtime Verification
- **Role**: `devops`
- **Priority / Effort**: `P1 / XS`
- **Depends On**: `META3-M5-020`
- **Blocks**: `META3-M5-040`
- **Writable Scope**: Generated platform configurations (`.claude/`, `.antigravity/`, `.codex/`)
- **Description**: Run `python3 scripts/sync_ai_agent_ecosystem.py --sync` and `--check` to verify multi-agent synchronization across Claude, Antigravity/Gemini, and Codex.
- **DoR**: `META3-M5-020` documentation updated.
- **DoD**: Ecosystem sync check returns exit code 0 (`[OK]`).

#### `META3-M5-040` — Sprint META-PLAN-003 Final Certification & Handoff Seal
- **Role**: `orchestrator`
- **Priority / Effort**: `P0 / XS`
- **Depends On**: `META3-M5-030`
- **Blocks**: None (Sprint Closure)
- **Writable Scope**: `plans/evidence/meta_plan_003/m5_sprint_seal_report.json`
- **Description**: Issue final orchestrator certification, seal the sprint evidence package, and transition task board to CLOSED.
- **DoR**: All tickets META3-M0-010 through META3-M5-030 DONE.
- **DoD**: Signed sprint seal evidence JSON generated; sprint formally closed.

---

## 5. 📊 Agile Task Board & Dependency Matrix Rollup

| Milestone | Purpose | Tickets | Assigned Roles | Critical Path |
|---|---|:---:|---|:---:|
| **M0** | Agile Governance, Test Baselines & Architecture Blueprint | 4 | `business_analyst`, `qa_tester`, `developer`, `code_reviewer` | YES |
| **M1** | Model Context Protocol (MCP) Full 16-Discipline Server Integration | 4 | `developer` | YES |
| **M2** | Metaphysics Fine-Tuning Dataset Pipeline & Corpus Exporters | 4 | `domain_master`, `developer`, `qa_tester` | NO (Parallel with M1/M3) |
| **M3** | Glassmorphism Visual Endpoints & Dynamic SVG Interactive Rendering | 4 | `developer` | NO (Parallel with M1/M2) |
| **M4** | Automated Test Planes, Integration & E2E Regression | 4 | `qa_tester` | YES |
| **M5** | Security Audit, Release Packaging & Sprint Closure | 4 | `code_reviewer`, `business_analyst`, `devops`, `orchestrator` | YES |
| **TOTAL**| | **24**| | |

---

## 6. 🔒 Governance & Sign-Off Authority

- **Specification Status**: `APPROVED`
- **Agile Compliance**: 100% compliant with Rule 08, Rule 10, Rule 21, and Rule 22.
- **Document Authority**: Business System Analyst (`business_analyst`)
- **Master Orchestrator**: `orchestrator`
- **Sprint Target Date**: `2026-08-31`
