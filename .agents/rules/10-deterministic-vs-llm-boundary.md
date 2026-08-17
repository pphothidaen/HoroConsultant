# Rule 10: Deterministic vs. AI Agent Allocation Boundary
> **Category:** Architectural Governance & System Hygiene  
> **Target:** All Agents (`orchestrator`, `business_analyst`, `developer`, `qa_tester`, `code_reviewer`, `domain_masters`)

---

## 🎯 The Core Philosophy: "Deterministic for Truth, AI for Synthesis"

Every system component must strictly adhere to the functional boundary between **Deterministic Code Logic** (Rust/Python) and **AI Agents / LLM Inference**. Violating this boundary is strictly forbidden and constitutes an architectural defect.

---

## 🚫 1. Prohibited for LLMs (Must Use 100% Deterministic Code)

The following operations MUST NEVER be performed by LLM prompts, agent hallucinations, or probabilistic inference:

1. **Metaphysical & Calendar Math:**
   - Lunar-Solar calendar conversions, True Solar Time (longitude adjustments), BaZi 4-Pillars generation, Ten Deities (Shi Shen), 12 Life Stages (Chang Sheng), 5 Elements weighting.
   - *Implementation:* Native Rust PyO3 engine (`rust_core/`) or deterministic Python algorithms (`project/bazi/engine.py`).
2. **Static Code & Syntax Verification:**
   - Python/Notebook AST compilation (`ast.parse`, `compile()`), variable closure scope inspection, import checking.
   - *Implementation:* Python AST visitors in `tests/test_notebook_syntax.py`.
3. **Security & Secrets Scanning:**
   - Regex pattern matching for API keys, tokens, and credentials.
   - *Implementation:* `CodeReviewer.scan_secrets()` and `.agents/hooks/pre_tool_check.py`.
4. **CI/CD, Git & CLI Automation:**
   - Git working tree status, hash retrieval, command interception, Kaggle file downloads.
   - *Implementation:* `scripts/smart_quality_gate.py` and `scripts/kaggle_notebook_manager.py`.

---

## 🤖 2. Mandated for AI Agents (LLM Inference & Synthesis)

The following operations MUST leverage AI Agents and fine-tuned models (e.g. `Qwen 2.5-7B LoRA`, `Gemini 3.6/3.7 Flash`, `DeepSeek-V3`):

1. **Context Understanding & Metaphysical Synthesis:**
   - Reading calculated astrological values + RAG classical treatises to weave personalized, empathetic, and multi-domain consultations for users.
2. **Root Cause Analysis (5-Whys Post-Mortem):**
   - Synthesizing incident logs, understanding error contexts, documenting lessons learned in `.agents/LESSONS_LEARNED.md`.
3. **Requirement Grilling & Architectural Planning:**
   - Dissecting ambiguous user intent, interactive edge-case interview, and multi-agent task breakdown.
4. **Natural Language Counseling & Empathy:**
   - Formulating respectful, compassionate, and actionable life guidance in Thai/English without robotic boilerplate.
