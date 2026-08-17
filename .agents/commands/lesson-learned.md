---
description: Trigger post-mortem lesson learned analysis, sync lessons learned database, and run static regression gates
command: python3 -m pytest tests/test_notebook_syntax.py -v && python3 project/core/code_reviewer.py --review
---

Executes post-mortem regression checks, audits `.agents/LESSONS_LEARNED.md` synchronization, and verifies static AST quality gates.
