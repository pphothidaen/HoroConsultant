# ☯️ HoroConsultant — Computational Metaphysics & AI Fine-Tuning Pipeline
> **Cross-Platform AI Agent Instruction & Context Blueprint**  
> *Supports Claude Code, Antigravity, Cursor, Windsurf, thClaws, GitHub Copilot, and Custom Agents.*

---

## Claude Code governance priority

Claude Code should use the three-layer governance model in this order:

1. `.claude/settings.json` hooks for hard safety constraints before tool execution.
2. `.claude/rules/*.md` for path-scoped, context-aware rules.
3. `.claude/CLAUDE.md` and this file for short global context only.

Do not read secret files or print token values. Do not edit generated `.codex/agents/*.toml` directly. Do not claim release completion without CI, deployment, and live endpoint evidence.

For cross-platform agent sync, use the umbrella gate:

```bash
python3 scripts/sync_ai_agent_ecosystem.py --check
python3 scripts/sync_ai_agent_ecosystem.py --sync
```

---

## 📌 1. Session Initialization & Project Overview

**HoroConsultant** is an enterprise-grade Computational Metaphysics Engine & Fine-Tuning Pipeline. It combines deterministic astronomical algorithms (True Solar Time, NOAA Spencer 1971, Swiss Ephemeris) with a Local-First Hybrid Multi-Agent AI System (Ollama Qwen2.5:7b + FAISS RAG + Gemini Cloud Validator).

### 🛠️ Core Technology Stack
- **Core Engine**: Python 3.12 (Pure Python math, Rust PyO3 core bindings)
- **Web & API Framework**: FastAPI, Uvicorn, HTML5/CSS3 (Glassmorphism Dark UI)
- **Vector DB & RAG**: FAISS Index (dim=768) + `nomic-embed-text:latest` (3,132 vectors ingested)
- **Local LLM**: Ollama (`qwen2.5:7b`, `qwen2.5-coder:7b`) / MLX QLoRA 4-bit (`mlx-community/Qwen2.5-7B-Instruct-4bit`)
- **Cloud LLM**: Gemini 2.0 Flash (Dual Key rotation fallback & Prediction Validator Auditor)
- **Cloud Fine-Tuning**: Kaggle GPU Automation (`pphothidaen/horoconsultant-finetune-pipeline`), Hugging Face Hub (`pphothidaen/qwen2.5-7b-bazi-instruct-4bit`)

---

## ⚡ 2. Primary Project Commands

```bash
# 1. Run Full Unit, Integration & Web Regression Test Suite (134/134 PASS)
python3 -m pytest -v

# 2. Start FastAPI Server & Web UI (Local-First: Qwen2.5:7b + FAISS + Glassmorphism UI)
python3 -m uvicorn project.main:app --reload --port 8000
# Web UI Dashboard: http://localhost:8000
# Admin Panel:       http://localhost:8000/admin
# API Docs:          http://localhost:8000/docs

# 3. Synchronize AI Agents across Claude, OpenAI/Codex, Gemini/AGY, Hermes, and thClaws
python3 scripts/sync_ai_agent_ecosystem.py --sync

# 4. Run Universal Production Metaphysics Engine (thClaws + AGY Subagent Hybrid Mode)
python3 scripts/run_universal_bridge.py --mode hybrid

# 5. Pre-Deployment Code Review & Safety Audit
python3 project/core/code_reviewer.py --review

# 6. Ingest Obsidian Vault Books & Export ShareGPT Fine-Tuning Dataset
python3 project/rag/ingest_vault.py --export-finetune

# 7. Kaggle Fine-Tuning Automation (Status, Push, Pull)
python3 scripts/kaggle_notebook_manager.py --status
python3 scripts/kaggle_notebook_manager.py --push
python3 scripts/kaggle_notebook_manager.py --pull

# 8. Post-Training Model Fusion & GGUF Conversion
python3 scripts/post_train_fuse.py --dry-run
```

---

## 🏗️ 3. Architecture & Coding Standards

1. **Pure ASCII Logging Guard**:
   - All `logger` outputs and stdout must use Pure ASCII tags (`[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`, `[START]`, `[MODEL]`, `[CUDA]`, `[AUDIT]`).
   - Avoid emojis inside subprocess/ipykernel logs to prevent `UnicodeEncodeError` surrogate crashes.

2. **Locked MLOps Dependency Stack**:
   - `transformers == 4.44.2`
   - `peft == 0.12.0`
   - `trl == 0.11.0`
   - `accelerate >= 0.34.0, < 1.0.0`
   - `bitsandbytes == 0.43.3`
   - `datasets >= 2.21.0`
   - `huggingface_hub == 0.25.1`

3. **Pip Options Standard**:
   - Forbidden: `--no-progress-bar` (causes exit code 2 error).
   - Required: Use `--progress-bar off` with `-q --prefer-binary`.

4. **Kaggle GPU & CUDA Compatibility Guard**:
   - Never reinstall PyTorch (`pip install torch==...`) in Kaggle environment.
   - If Kaggle allocates unsupported GPU hardware (`sm_60` / Tesla P100), `cloud_train_orchestrator.py` gracefully falls back to CPU Mode to guarantee Exit Code 0.

5. **Local Override Configuration**:
   - Developers and Agents may create `CLAUDE.local.md` or `.env` for local environment variable overrides without committing secrets to Git.

6. **Claude Code Command Governance (3 Levels)**:
   - Level 1 hard constraints live in `.claude/settings.json` hooks and block critical risks before tool execution.
   - Level 2 context-aware rules live in `.claude/rules/*.md` and `.agents/rules/*.md`; load only rules relevant to touched paths.
   - Level 3 global context stays here in `CLAUDE.md`; keep it short and do not use it as the only safety boundary.
   - Delegation rules are governed by `.agents/skills/orchestrator-delegation/SKILL.md`, `.agents/rules/11-orchestrator-subagent-delegation.md`, and `.agents/rules/12-claude-code-three-level-governance.md`.

---

## 📁 4. Project Directory Structure

```
HoroConsultant/
├── CLAUDE.md                    # Main Project Blueprint & Agent Guide
├── .antigravity/agents/         # Primary Google Antigravity Agent Specifications (.agent YAML)
├── .claude/                     # Claude Code hooks, path-aware rules, and prompt patterns
│   ├── settings.json            # PreToolUse/PostToolUse hook wiring
│   └── rules/                   # Context-aware Claude Code rules
├── .mcp.json                    # Model Context Protocol (MCP) Shared Config
├── settings.json                # Tools & Agent Permissions Settings
├── .agent_rules.md              # Mandatory Operational Commandments
├── .agents/                     # Multi-Agent Architecture Directory & Skill Governance
│   ├── AGENTS.md                # Agent Role Strategy & Flow Protocol
│   ├── rules/                   # Modular Rules (01-coding, 02-testing, etc.)
│   ├── commands/                # Custom Slash Commands (/test, /review, etc.)
│   ├── skills/                  # Context-aware Modular Skills
│   ├── agents/                  # Downstream Markdown Agent Definitions
│   └── hooks/                   # Pre/Post-tool Audit Scripts
├── project/                     # Core Application Source Code
│   ├── core/                    # Solar Time, BaZi Engine, SVG, Reviewer
│   ├── rag/                     # Vector DB (FAISS), Ingestion, Exporter
│   ├── static/                  # Glassmorphism Web UI Frontend
│   └── main.py                  # FastAPI Application Entrypoint
├── scripts/                     # Automation & Cloud Fine-Tuning Scripts
└── tests/                       # Automated Pytest Test Suite
```
