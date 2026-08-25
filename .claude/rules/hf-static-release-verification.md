---
description: Enforce fail-closed HF Static health, version, visual, and evidence gates.
paths:
  - "scripts/publish_space_hf.py"
  - "scripts/run_visual_layout_audit.py"
  - "tests/test_publish_space_hf.py"
  - "tests/test_hf_release_governance.py"
  - "project/static/**"
  - "public/**"
  - "project/tests/artifacts/**"
  - "project/tests/screenshots/visual_audit/**"
  - ".github/workflows/**"
  - ".agents/rules/16-hf-static-release-verification.md"
  - ".agents/skills/hf-static-release-verification/**"
---

# HF Static release verification

Apply Rule 16 whenever an HF Static production asset, publisher, workflow, test,
or release evidence file changes.

- Use SDK-aware health checks: validate the Static root and `version.json`, not a
  Docker-only `/health` endpoint.
- Use fail-closed exact-cardinality version checks. Missing, duplicate, composite,
  stale, malformed, unreachable, or unresolved indeterminate evidence blocks release.
- A visual gradient marked indeterminate is resolved only by documented manual
  reviewer sign-off with viewport, finding, reviewer, decision, and timestamp.
- Run publisher regressions and the live `v3-consensus` visual audit across all
  five canonical viewports.
- Preserve the machine-readable report, post-deploy evidence, and five screenshots.
- `devops` runs the gate, `qa_tester` owns regressions and screenshots,
  `code_reviewer` blocks incomplete releases, and `orchestrator` makes the final
  evidence-based decision.
- Do not claim production success unless every gate is green. Report failures with
  ASCII tags such as `[ERROR] BLOCKED`.
- Edit authoritative role sources under `.antigravity/agents/`; never hand-edit
  synchronized `.agents/agents/*` or generated `.codex/agents/*.toml`.
