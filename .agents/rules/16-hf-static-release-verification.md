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
2. Run fail-closed live version verification using the immutable
   `release_source_commit`, not the later packaging/evidence commit. The
   expected version and `release_source_commit` must each occur exactly once in
   every required deployed identity location. Missing, duplicate, composite,
   stale, malformed, or unreachable identity evidence is a failure.
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
expected version, immutable `release_source_commit`, source-metadata path and
SHA-256 digest, source revision, later `packaging_commit`, command outcomes,
per-asset cardinality checks, report/screenshots, timestamp, and responsible
agents. `packaging_commit` is evidence-only. Record every manual review's
viewport, finding, reviewer, decision, and timestamp. Use `[OK]`, `[ERROR]`,
`[WARNING]`, `[INFO]`.

## Release identity model

The owner authorized this model for `TICKET-V3UI-007`:
`release_source_commit` is the immutable deployed-payload identity;
`packaging_commit` is the later metadata/evidence commit. They are distinct:
record both values, but never put `packaging_commit` on a version surface.

Committed release metadata is the provenance authority. It records the metadata
path and SHA-256 digest, version, `release_source_commit`, and source revision;
the verifier derives deployed values only from it, proves
`release_source_commit` is an ancestor of `packaging_commit`, and checks
version/source exact cardinality on every surface. There is no legacy commit,
version, or metadata fallback. No environment variable, CLI default, runtime
`HEAD`, or external override may substitute either identity. An absent,
conflicting, mutable, overridden, or unproven value blocks release; do not weaken
checks because packaging follows source.

## Ownership

- `devops`: health/version gates and release evidence.
- `qa_tester`: publisher tests, five-viewport audit, screenshots, strict failures.
- `code_reviewer`: blocks failed, absent, stale, indeterminate, inconsistent evidence.
- `orchestrator`: final decision after green DevOps, QA, and reviewer evidence.

## Generated-source boundary

Edit authoritative role responsibilities in `.antigravity/agents/*.agent`.
`.agents/agents/*` and `.codex/agents/*.toml` are synchronized compatibility
outputs; never hand-edit them. After an intentional source change, run
`python3 scripts/sync_ai_agent_ecosystem.py --sync`, then require
`python3 scripts/sync_ai_agent_ecosystem.py --check` to pass.

## Completion gate

A production release may be claimed only when commands, exact-cardinality,
screenshots/reports, manual indeterminate sign-off, and Code Reviewer
`READY_FOR_PROD` are all green. Otherwise report `[ERROR] BLOCKED`.
