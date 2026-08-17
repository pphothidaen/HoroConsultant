# Rule 09: Lesson Learned Ingestion & Prevention Quality Gate
> **Category:** Governance & Continuous Learning  
> **Target:** All Agents (`orchestrator`, `business_analyst`, `developer`, `qa_tester`, `code_reviewer`)

---

## 🎯 Mandate

Any architectural bug, runtime failure (e.g. Kaggle kernel exit code != 0, unhandled exception, syntax error), or breaking dependency issue MUST follow the **4-Step Lesson Learned & Prevention Protocol** before the task can be marked as `DONE` or deployed to production.

---

## 🔄 The 4-Step Protocol

1. **Root Cause Analysis (5-Whys):**
   - The `business_analyst` / `orchestrator` must isolate the definitive root cause (e.g. closure variable scope ordering, API signature breaking change, unhandled race condition).
2. **Document in `.agents/LESSONS_LEARNED.md`:**
   - Must append a structured entry containing:
     - **Issue Experienced**: Exact symptoms and log traceback.
     - **Definitive Root Cause**: Low-level technical explanation.
     - **Lesson Learned**: High-level architectural rule.
     - **Prevention Protocol & Verification**: The concrete guardrails and tests put in place.
3. **Automated Test / Static AST Guard:**
   - The `qa_tester` must implement an automated regression test in `tests/` or a static AST linter in `tests/test_notebook_syntax.py` that fails if this issue recurs.
4. **Code Reviewer Quality Gate:**
   - The `code_reviewer` will NOT grant `READY_FOR_PROD` status unless the regression test passes 100% and the Lesson Learned documentation is synchronized.
