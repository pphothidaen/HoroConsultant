---
description: Run pre-deployment code review, secret leakage scan & safety audit
command: python3 project/core/code_reviewer.py --review
---

Scans workspace for secret leakage, Kaggle CUDA compatibility, and pytest verification status before committing.
