# Rule 16: Hugging Face Static Release Verification

## Purpose

Prevent a Hugging Face Static Space release from being approved when health,
version identity, visual layout, or release evidence is incomplete or stale.

## Mandatory release gate

Every production publish or production-release claim for the HF Static Space
must satisfy all of these checks:

1. Run SDK-aware health verification. A Static Space is checked through its
   root document and `version.json`; it must not be judged by a Docker-only
   `/health` endpoint.
2. Run fail-closed live version verification. The expected version and commit
   must each occur exactly once in every required identity location. Missing,
   duplicate, composite, stale, malformed, or unreachable identity evidence is
   a failure.
3. Run the publisher regression suite and the production visual layout audit.
4. Capture all five canonical viewport screenshots and store the machine-readable
   report and post-deploy evidence artifact.
5. Treat network errors, missing files, unresolved indeterminate checks, stale
   reports, and non-zero commands as release blockers. A visual gradient marked
   indeterminate may pass only with a documented manual reviewer sign-off that
   identifies the viewport, finding, reviewer, decision, and timestamp. Never make
   a release claim on failure.

## Required commands

```bash
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk static
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk static
python3 -m pytest -q tests/test_publish_space_hf.py
python3 scripts/run_visual_layout_audit.py --url https://pphothidaen-horoconsultant-core-backend.static.hf.space --scenario v3-consensus --no-server
python3 -m pytest -q tests/test_hf_release_governance.py
```

## Evidence contract

The release evidence must identify the target Space, SDK, deployed revision,
expected version and commit, command outcomes, per-asset cardinality checks,
visual report path, five screenshot paths, timestamp, and responsible agents.
Document every manual gradient review with its viewport, finding, reviewer,
decision, and timestamp.
Use only ASCII status tags: `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.

## Ownership

- `devops`: runs SDK-aware health and fail-closed live version gates and assembles
  the release evidence.
- `qa_tester`: runs publisher tests and the live five-viewport visual audit,
  captures screenshots, and reports failures without weakening assertions.
- `code_reviewer`: blocks `READY_FOR_PROD` when any check fails or evidence is
  absent, stale, unresolved indeterminate, or inconsistent.
- `orchestrator`: owns the final release decision after reviewing green evidence
  from DevOps, QA, and Code Reviewer.

## Generated-source boundary

Edit authoritative role responsibilities in `.antigravity/agents/*.agent`.
`.agents/agents/*` and `.codex/agents/*.toml` are synchronized compatibility
outputs; never hand-edit them. After an intentional source change, run
`python3 scripts/sync_ai_agent_ecosystem.py --sync`, then require
`python3 scripts/sync_ai_agent_ecosystem.py --check` to pass.

## Completion gate

A production release may be claimed only when every mandatory command exits zero,
the exact-cardinality checks all pass, the five screenshots and reports exist,
every indeterminate gradient has documented manual sign-off, and the Code Reviewer
records `READY_FOR_PROD`. Otherwise report `[ERROR] BLOCKED`.
