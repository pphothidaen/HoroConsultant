---
description: Enforce fail-closed HF Docker backend and Vercel UI release evidence gates.
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
# HF Docker backend and Vercel UI release verification
Apply Rule 16 to every backend/UI release, publisher, workflow, test, or release
evidence change. The legacy filename is compatibility-only: it never authorizes
a Static SDK payload to the backend Space.
- The backend is `pphothidaen/horoconsultant-core-backend` with `--sdk docker`.
  Static-to-backend publishing, Azure public deploy/routing, and Fly deployment
  are prohibited. Vercel is the separately verified static UI target.
- Use SDK-aware Docker `/health` and version checks for the backend, plus Vercel
  UI root/version, E2E, and exactly five canonical viewports with screenshots:
  `desktop-4k`, `laptop-standard`, `tablet-portrait`, `mobile-ios`, and
  `mobile-compact`. Do not replace the Vercel target with a legacy HF Static
  hostname.
- Use fail-closed exact-cardinality checks for the expected version and immutable
  `release_source_commit` across required backend/UI identity surfaces. Missing,
  duplicate, composite, stale, malformed, unreachable, or unresolved indeterminate
  evidence blocks release. A manual reviewer resolves an indeterminate only with
  viewport, finding, reviewer, decision, and timestamp.
- The committed release manifest must bind source metadata digest,
  `release_source_commit`, and evidence-only `packaging_commit`. Require atomic
  manifest/CAS preconditions and recorded prior HF Docker/Vercel revisions for
  rollback; until the publisher ticket supplies them, report `[ERROR] BLOCKED`.
- Receipt, WorkResult, and public ExecutionOutcome are validated in-process with
  stdout/stderr elided; they are not portable/offline release proof. Never restore
  or log raw provider streams.
- `devops` owns backend evidence/rollback; `qa_tester` regression/UI screenshots;
  `code_reviewer` blocks; `orchestrator` decides. Never hand-edit generated outputs.
- Claim `[OK] READY_FOR_PROD` only when every gate is green; otherwise use `[ERROR] BLOCKED`, `[WARNING]`, and `[INFO]` ASCII report tags.
