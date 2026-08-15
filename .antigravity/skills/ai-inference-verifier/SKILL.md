---
name: ai-inference-verifier
description: Verify real LLM inference origins versus static fallback templates.
---

# 🕵️ AI Inference Origin & Anti-Template Verification Skill

This skill provides testing procedures, entropy/variance metrics, and automated inspection scripts to verify that predictions and readings on HoroConsultant are produced by **Real AI Agents (LLM Models)** and not static template fallbacks or string-substitution placeholders.

---

## 🎯 Verification Criteria Matrix

| Dimension | Real AI Model Inference (`REAL_AI_MODEL`) | Static Fallback / Template (`FALLBACK_TEMPLATE`) |
| :--- | :--- | :--- |
| **Response Metadata** | `source: "ai_agent_llm"`, `model_used: "gemini-..."` or `"qwen..."` | `source: "fallback"` or missing metadata |
| **Semantic Variance** | High ($\Delta > 0.15$ similarity difference between variant prompts) | Identical or near 1.0 ($\Delta < 0.02$) with simple keyword swapping |
| **Vocabulary & Nuance** | Rich, tailored Thai astrological prose citing classical texts dynamically | Fixed boilerplate paragraphs with hardcoded headings |
| **Linguistic Entropy** | High per-domain entropy and dynamic sentence restructuring | Rigid static phrasing |

---

## 🛠️ Verification Commands

### 1. Run Automated Inference Origin Auditor
Execute the automated auditor against any target API endpoint to classify inference authenticity:
```bash
# Audit against local or staging endpoint
python3 scripts/audit_ai_inference_origin.py --endpoint https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret

# Quick Live Audit
python3 scripts/audit_ai_inference_origin.py --live-check
```

### 2. Live Playwright Multi-Domain AI Query Verification
Run the 10-case Playwright automation suite on the live production Hugging Face Space:
```bash
python3 scripts/run_live_e2e_hf_space.py
```

---

## 🛡️ QA Audit Protocols & Zero-Tolerance Rules

1. **Anti-Template Detection Protocol**:
   - The QA Agent MUST never sign off on an endpoint that simply returns hardcoded boilerplate or substitutes the query string into a static paragraph.
   - Run query pairs with slight semantic differences (e.g. *"ลูกเป็นอย่างไร"* vs *"ในอนาคตลูกจะมีแววทำงานด้านไหน"*) and assert that the AI generates distinct sentence structures and focused answers.

2. **Network & Backend Health Protocol**:
   - Verify that the upstream cloud backend or Cloud LLM API returns `HTTP 200` without triggering client-side or gateway fallback routines.
   - Audit browser console logs for CORS errors, 404s, or 502s.

3. **Reporting Protocol**:
   - If an endpoint falls back to static templates, QA MUST log a `[FAIL: FALLBACK_DETECTED]` bug report with the offending query pair and variance score.
