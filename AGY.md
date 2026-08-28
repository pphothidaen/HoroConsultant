# ☯️ HoroConsultant — AGY CLI Architecture & Operating Contract
> **Production AI SDLC & Multi-Agent Execution Blueprint for AGY CLI**  
> *Deterministic, Token-Efficient, and Secure Workspace Architecture*

---

## 🛠️ 1. Verified Local Toolchains & Commands

```bash
# Core Test Suite (134/134 Tests Passing)
python3 -m pytest -v

# FastAPI Server & Glassmorphism Web UI (Local-First: http://localhost:8000)
python3 -m uvicorn project.main:app --reload --port 8000

# AI Agent Ecosystem Validation & Multi-Platform Sync
python3 scripts/sync_ai_agent_ecosystem.py --check

# Pre-Deployment Code Review & Safety Gate
python3 project/core/code_reviewer.py --review

# Rust PyO3 Core Verification
cargo check --manifest-path rust_core/Cargo.toml 2>/dev/null || true
```

---

## 🏗️ 2. Core Subsystems Architecture

```text
+-------------------------------------------------------------------------+
|                  HoroConsultant Production System                       |
+-------------------------------------------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-----------------------------+             +-----------------------------+
|    FastAPI Gateway & UI     |             |    AGY Agentic Sandbox      |
|  - Glassmorphism Dark UI    |             |  - Pre/Post-Tool Hooks      |
|  - REST / WebSocket Routes  |             |  - 14-Param Sub-agents      |
|  - Admin & Telemetry Engine |             |  - Progressive Rules Engine |
+-----------------------------+             +-----------------------------+
          |                                                   |
          v                                                   v
+-----------------------------+             +-----------------------------+
|   Astro-Calculation Core    |             |   Hybrid AI & Vector RAG    |
|  - NOAA Spencer 1971 Solar  |             |  - FAISS Index (dim=768)    |
|  - Swiss Ephemeris & BaZi   |             |  - Local Ollama / Qwen2.5   |
|  - Rust PyO3 High-Perf Math |             |  - Gemini Dual-Key Failover |
+-----------------------------+             +-----------------------------+
```

---

## 📜 3. Git Hygiene & Semantic Commit Protocol

- **Atomic Commits**: Group modifications by semantic intent (`feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`).
- **Targeted Staging**: Stage specific files only (`git add <file1> <file2>`). Never execute `git add .` or `git add -A`.
- **Draft Pull Requests**: Push to feature branch and open draft PR: `gh pr create --draft --title "feat: <title>" --body "<details>"`.
- **Branch Protection**: Direct edits to `main` / `master` are blocked by `.agy/hooks/pre-tool-use.sh`.

---

## ⚡ 4. Operating Directives & Context Preservation

1. **Anti-Cognitive Decay (45% Rule)**: When context usage crosses 45%, trigger memory compaction, generate `HANDOFF.md`, and execute `/clear`.
2. **Deterministic Precedence**: Tool-grounded calculation overrides LLM hallucination in all astrological computations.
3. **Log Sanitization**: Keep main terminal output under 30 lines. Use `.agy/scripts/tmux-runner.sh` for heavy outputs.
4. **Pure ASCII Logging**: Logger tags must use ASCII `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` to avoid UTF-8 surrogate crashes.

---

## 🔍 5. Active Hooks Configuration

### Active AGY Hooks
!`find .agy/hooks -name "*.sh" -type f 2>/dev/null || true`
