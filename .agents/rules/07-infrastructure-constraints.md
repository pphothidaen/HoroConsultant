# Rule 07 — Production Infrastructure Constraints

> **Effective Date:** 2026-08-15
> **Last Updated:** 2026-08-26
> **Scope:** All agents and every release-affecting change

## Purpose

Keep production routing on one auditable architecture: the Hugging Face Docker
backend `pphothidaen/horoconsultant-core-backend` serves the backend API, and
Vercel owns the public static UI. A legacy filename, historical workflow, or
CLI default is never authority to select another target.

## Prohibited release paths

- **Fly.io is retired.** Do not create, restore, suggest, or deploy Fly
  configuration; do not use Fly secrets. Preserve legacy files only when an
  owned migration ticket neutralizes them without deleting history.
- **Azure Container Apps is not a public production route.** Do not enable
  ingress, proxy Vercel traffic to it, or run an Azure public auto-deploy.
  Azure variables may remain as inactive historical configuration only.
- **The backend Space is Docker-only.** Never publish a Static SDK payload to
  `pphothidaen/horoconsultant-core-backend`; never use its old Static hostname
  as the public UI target.

## Approved architecture

| Target | Production role | Release status |
|---|---|---|
| HF Space `pphothidaen/horoconsultant-core-backend` | Docker backend API | approved when gated |
| Vercel | Static UI and browser-facing visual checks | approved when gated |
| Docker local | Build, package, and dry-run verification | approved |
| Azure Container Apps | Historical/inactive | prohibited for public release |
| Fly.io | Retired | prohibited |

```text
Browser -> Vercel static UI -> HF Docker backend API
```

## Release and evidence gate

1. Select the HF target with `--sdk docker`; verify backend health and version
   against committed provenance before any release claim.
2. Verify the separately recorded Vercel UI target for version identity, E2E,
   and all required visual evidence. Do not substitute an HF Static URL.
3. Require a bounded owner, source freeze, QA, package dry-run, secret scan,
   reviewer verdict, and target-scoped approval before any external mutation.
4. Record only sanitized evidence. Provider results and public outcomes are
   validated in-process with elided stdout/stderr; they are not independently
   portable or offline proof.

## Rollback and completion

Rollback uses the exact release-commit revert, the recorded prior HF Docker
revision, and the recorded prior Vercel production revision. Stop on a missing,
stale, mismatched, or unapproved target; do not fall back to Azure, Fly, or a
Static backend publish. Rule 16 supplies the fail-closed release-verification
contract.
