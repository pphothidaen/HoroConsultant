# Release Notes

## Completed Plan Milestones (historical)
`PROJECT_TASKS.md` now tracks only active execution and open release gates.
`docs/RELEASE_NOTES.md` is the historical archive for completed plans.

### As of 2026-08-17
- ✅ Phase 17 — Client-Side Deterministic BaZi & True Solar Time Engine
- ✅ Phase 16 — 3-Tier Notebook AST, Python Syntax & MLOps Safety Gate
- ✅ Phase 15 — Kaggle Fine-Tuning Pipeline NumPy 2.x & BNB Hotfix
- ✅ Production Gateway 404/502 Hotfix & Post-Deploy Verification
- ✅ Phase 14 — Metaphysics AI Live Consultant Chat Assistant & Multi-Turn Interactive Consultation Engine
- ✅ Phase 13 — Imperial White & Red Theme Overhaul
- ✅ Phase 12 — Life Path Multi-Scenario Simulation & What-If Analyzer
- ✅ Phase 11 — LuoPan 24-Mountain Energy Heatmap & Dream Symbolism Decoder
- ✅ Phase 10 — Astrological Calendar & Auspicious Date Selector
- ✅ Phase 9 — Multi-Profile Synastry & Partner Compatibility Matrix
- ✅ Phase 8 — Metaphysics AI Voice & Speech Synthesis (TTS / STT)
- ✅ Phase 7 — Interactive DaYun/LiuNian Timeline Scrubber & Live Sky Transit Clock
- ✅ Phase 6 — Production Delivery, PWA Offline Support & Consultation Report Exporter
- ✅ Phase 5 — Multi-Language Internationalization (i18n) & Localized Interpretation
- ✅ BaZi Fengshuix.com Complete Replication & HTML Display Component
- ✅ All 16 Metaphysics Disciplines E2E Snapshot & Visualizer Upgrade
- ✅ สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer Web Application
- ✅ Continuous MLOps, Hybrid LLM Provider & Grafana Tuning
- ✅ TICKET-META-002 — Deterministic Branch Engine Expansion (DONE)
  - Deterministic engine suite for `test_5_branch_engines.py`, Swiss Ephemeris tests, and BaZi/Ratchaburi golden vector compatibility.
  - Deterministic modules mapped for Tai Yi, Da Liu Ren, Qi Men, BaZi, I Ching/Liu Yao/Mei Hua, Xuan Kong/San He/Mian Xiang, and Ze Ji.
- ✅ TICKET-META-003 — Pipeline + Delivery Expansion (DONE)
  - OCR/RAG ingestion and ShareGPT JSONL pipeline execution with source metadata retention.
  - Dataset generation, GGUF/Ollama fusion, MCP tooling, and Glassmorphism visualizer parity for public/static app assets.
- ✅ TICKET-META-004 — Question/Forecast Benchmarking (DONE)
  - Implemented six-domain benchmark and routing evidence in prompt/debate/tests.
  - Maintained focus routing + 100-point rubric + validator confidence path with actionable guidance coverage and canonical evidence.

## Current Active Tickets (not yet closed)
- `TICKET-META-005` — **BLOCKED (External Gate Dependencies)**
  - Reconcile active/future plan work around providers, observability, CI/CD, governance, and release architecture.
- `TICKET-META-006` — **BLOCKED (External Gate Dependencies)**
  - Run full QA, security, synchronization, release evidence, and final handoff documentation.
  - **Additional local blocker:** Vercel public gateway is partially healthy (`2/3`), while canonical HF backend probes remain failing (`/health`/service and static `404`), and Azure deployment remains blocked by RBAC `AuthorizationFailed` on resource-group read/write.

## Current State Note
- All historical completion entries above were marked `DONE` during their respective handoffs.
- Ongoing release readiness remains tracked in [PROJECT_TASKS.md](PROJECT_TASKS.md), including:
  - `TICKET-META-005`
  - `TICKET-META-006`
  - Active release gates and unresolved blockers
- Local evidence package for this run is available at `project/tests/local_release_readiness_2026-08-17.md`.
- Gate closure tracking template and operator handoff plan is tracked in [docs/RELEASE_HANDOFF_CHECKLIST.md](docs/RELEASE_HANDOFF_CHECKLIST.md).
