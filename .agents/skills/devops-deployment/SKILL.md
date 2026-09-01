---
name: devops-deployment
description: Run fail-closed HF Docker backend and Vercel UI release workflows.
owner: devops
responsibility: production-deployment
responsible_agents:
  - devops
  - code_reviewer
  - orchestrator
  - default
  - hermes
---

# DevOps Deployment

Use this skill whenever a HoroConsultant release, publish, production health,
rollback, or release-payload dry-run is requested. The canonical pair is the HF
Docker backend `pphothidaen/horoconsultant-core-backend` and a separately
verified Vercel static UI. The legacy Static-oriented skill directory is not a
target selector.

## Scope and safety boundary

- Do not publish a Static SDK payload to the backend Space. Do not use Azure
  Container Apps or Fly.io as public release targets.
- A dry-run, scan, or review does not authorize credentials, upload, push, or
  deployment. External mutation needs its own unlocked, target-bound ticket.
- Preserve raw provider stdout/stderr: public outcomes are validated in-process
  with streams elided and are not portable/offline proof.

## Preflight and package gate

1. Confirm a source freeze, exact target, reviewed change scope, and prior HF
   Docker/Vercel revision for rollback. Stop on an unknown or conflicting target.
2. Scan for secrets:

   ```bash
   python3 project/core/code_reviewer.py --scan-secrets
   ```

3. Run the Docker-targeted payload dry-run only:

   ```bash
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk docker --dry-run
   ```

4. Run the final reviewer gate:

   ```bash
   python3 project/core/code_reviewer.py --review
   ```

Do not treat a passing local Docker compose session as deployed evidence.

## Publish, verify, and rollback

After all release gates and explicit target approval are green, publish only the
HF Docker backend. Vercel UI publication is a separately gated platform action;
never route it through `publish_space_hf.py` or the backend Space.

Verify the deployed backend with the committed release metadata:

```bash
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk docker
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk docker
```

Require QA's Vercel UI version, E2E, and visual evidence before claiming success.
If a gate fails, stop. Roll back with the exact release-commit revert and the
recorded prior HF Docker and Vercel production revisions; do not substitute Azure,
Fly, or a static backend publish.

## Evidence report

Report only sanitized fields: backend target/SDK/revision, Vercel UI target and
revision, metadata digest, `release_source_commit`, `packaging_commit`, command
statuses, rollback revisions, and `[OK]` or `[ERROR]` verdict. Use only ASCII log
tags: `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.

## Repository closeout

After the user-approved, green PR merge, verify that `main` contains the
release commit, then immediately delete both branch copies: GitHub deletes the
remote branch through `gh pr merge --merge --delete-branch`; fast-forward local
`main` and use `git branch -d <completed-branch>` for the local branch. If any
merge, CI, or update evidence is missing, keep the branch and report
`[ERROR] BLOCKED`.
