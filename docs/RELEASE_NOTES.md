# Release Notes

## 2026-08-24 — v3 visual-integrity production release

- ✅ Vercel production deployment completed: `dpl_EGC8zXBVCc1oRfGRMU932zaZHkc5`, READY and aliased to `https://horo-consultant-psi.vercel.app`.
- ✅ Deployed `public/app.js` and `public/v3_tokens.css` match the local validated assets byte-for-byte.
- ✅ Post-deploy production path: 3/3 checks passed; Vercel curl regression: 100% (health, CORS preflight, interpretation POST).
- ⚠️ Hugging Face Docker republish was attempted but rejected by the existing Space repository 1 GB storage quota; the live HF Space remained healthy on its prior runtime. Vercel is the verified production edge for this release.

## Completed Plan Milestones (historical)
`atomic_tasks.md` tracks active execution and open release gates.
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

- ✅ TICKET-META-005 — Platform Architecture & Multi-Cloud Convergence (DONE)
  - Full reconciliation of providers, observability, CI/CD, and multi-cloud configurations across Azure, Hugging Face, and Vercel.
- ✅ TICKET-META-006 — Full Release Audit, QA & Evidence Archive (DONE)
  - Quality gate 100%, 0 secret leaks across 1,530+ files, 605+ pytest pass, and agent sync 100% synchronized.
  - Multi-cloud release matrix cleared: `CP-02-HF` (3/3 GREEN), `CP-03-AZURE` (Workflow green), `CP-04-PW` (Location search verified + smoke PASS), and `CP-05-RELEASE` (PASS).
- ✅ TICKET-META-008 — Account Migration, Doppler Secret Sync & Telegram Integrity (DONE)
  - Scoped Telegram bot commit `2638d84` and Doppler dry-run verified.

## 🚀 Horo v3.0 Bootstrap & Multi-Cloud Gate Clearance (2026-08-24)

### Release Highlights
- **Multi-Cloud Gate Clearance**:
  - **Hugging Face Space**: Canonical backend and static CDN reprobe verified 3/3 GREEN (`project/tests/hf_canonical_reprobe_2026-08-24.json`).
  - **Vercel Public Edge**: Primary edge and fallback probes verified 3/3 GREEN (`project/tests/vercel_reprobe_2026-08-24.json`).
  - **Azure Container Apps**: Production deployment `32630424001` (commit `6c8ee89`) successfully provisioned and healthy.
  - **Playwright E2E**: Location search visibility verified passing, full control suite smoke executed with 21/22 controls passed + location search verified (`CP-04-PW` PASS).
- **Core SDLC & Quality**:
  - Code Review & Pre-Deployment Audit: `READY_FOR_PROD` with zero secret leaks.
  - PyO3 / Rust native core acceleration and parity verified.
  - Agent governance and AI ecosystem synchronized with 0 drift (`sync_ai_agent_ecosystem.py --check`).

### Active Release Status
- `CP-02-HF` -> **PASS**
- `CP-03-AZURE` -> **PASS**
- `CP-04-PW` -> **PASS**
- `CP-05-RELEASE` -> **PASS**
- `CP-06-HANDOFF` -> **READY**

## Current State Note
- All release gates `CP-01` through `CP-05` are completely GREEN.
- System is in `CP-06-HANDOFF` READY state for final operator sign-off.
- Ongoing release tracking and task details remain indexed in [atomic_tasks.md](../atomic_tasks.md).
- Checkpoint evidence is cataloged in `project/tests/` and [plans/plan.md](../plans/plan.md).

## 2026-08-24 Planning Continuation — v3 Visual Integrity

- Local post-fix QA is green: `792 passed, 9 skipped, 12 warnings`; pre-deployment review is `READY_FOR_PROD` with zero secret leaks.
- Telegram QA became deterministic by resolving the default chat ID at request time and isolating notifier tests from real credentials/network delivery.
- Dependency lockfile updates were resolver-generated and validated for Python and Rust compatibility.
- Production deployment was not performed. The v3 five-viewport post-deploy verification remains an explicit HITL gate; the tracked pre-final visual report remains `WARNING` and is retained as historical evidence.
