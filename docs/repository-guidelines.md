# Repository Guidelines & Documentation Rules

## Documentation Architecture
- **Root Directory (`/README.md`)**: Reserved strictly for the project overview, high-level architecture summary, repository quick-start, and link redirects to the documentation. Do not place detailed guides or technical documentation pages at the root.
- **Detailed Documentation (`./docs/`)**: All technical documentation, API specifications, guides, and subsystem details MUST be placed inside the `./docs/` directory.
- **Structure File (`./docs/SUMMARY.md` or `/SUMMARY.md`)**: When adding new pages inside `./docs/`, always update the corresponding navigation/summary file so GitBook can properly index the sidebar.

## Action Rules for AI Agents
1. When asked to write, document, or expand features:
   - Create and edit Markdown files exclusively under `./docs/<category>/<page-name>.md`.
   - Use `kebab-case` for all directory and file names.
2. Never dump miscellaneous `.md` files in the repository root directory.
3. Keep `./README.md` clean, updated, and pointing to `./docs/`.

## GitBook Integration

### Git Sync Status
|- **Repository**: `pphothidaen/HoroConsultant` (branch: `main`)
|- **GitBook Space**: Pphothidaen Docs
|- **Current State**: ⚠️ Sync failing — GitHub branch protection requires `test provenance` status check to pass before pushes. GitBook's automated sync does not trigger CI.
|- **Resolution Applied**: (1) Restored `gitbook-docs.yaml` at repository root (was deleted in `b653e9ec`); (2) Added `.github/workflows/gitbook-webhook-pr.yml` that listens for GitBook webhook events via `workflow_dispatch` and creates formal PRs so CI provenance gates run automatically; (3) The `gitbook-docs.yaml` config is registered in `DOC_FILES` at `scripts/test_provenance_guard.py:49`.
|- **Owner Action Still Required**: Add GitBook's service account/bot to the GitHub branch protection bypass list (Settings → Branches → Branch protection rules), OR exclude `docs/**` paths from the `test-provenance` required status check. Configure GitBook's webhook to fire `repository_dispatch` events that trigger `gitbook-webhook-pr.yml`.
|- **Resolution Options** (from original docs):
| 1. Add GitBook's bot/service account to the branch protection bypass list (recommended).
| 2. Exclude docs paths from branch protection rules.
| 3. Use GitBook's native editor instead of Git Sync (no automation).
| 4. ✅ **IMPLEMENTED**: Set up a GitHub Action (`gitbook-webhook-pr.yml`) that listens for GitBook webhook events and creates PRs instead of direct pushes.

### Webhooks
- GitBook Webhook integration: `https://app.gitbook.com/integrations/webhook`
- Events: content updates, site views, user feedback
- Payload: JSON with HMAC signature verification
- Retry: 3 retries with exponential backoff
