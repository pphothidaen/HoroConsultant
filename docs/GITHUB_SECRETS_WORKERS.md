# GitHub Secrets Required for Workers Deployments

These three Cloudflare API tokens must be added manually in **GitHub Repository Settings → Secrets and variables → Actions**:

## Required Secrets

| Secret Name | Account | Account ID | Worker(s) |
|-------------|---------|------------|-----------|
| `CF_API_TOKEN_HERMES` | horo-hermes | `bda49e4e77e00609cb1ef68561b0d9eb` | horoconsultant, hermes-harness-hooks, hermes-harness-hooks-staging |
| `CF_API_TOKEN_GEMINI` | horo-gemini-bridge | `d91b1a43a188b73be61833adee445111` | prod (gemini-web-bridge) |
| `CF_API_TOKEN_AIPASS` | horo-aipass-bridge | `db2b77716a826311bbf9d104e125f540` | aipass-web-bridge |

## How to Create Each Token

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token** → **Custom token**
3. Permissions:
   - Account → Cloudflare Workers Scripts → Edit
   - Account → Cloudflare Workers KV Storage → Edit
   - Account → Cloudflare Workers R2 Storage → Edit
   - Zone → Zone Settings → Read (if using custom domains)

Note: Durable Objects have no standalone token permission — `Workers Scripts: Edit` already covers deploying workers that bind Durable Objects (e.g. the `EXT_HUB` DO in `wrangler.aipass.toml`).

4. Account Resources: **Include → Specific account → [select the account from table above]**
5. Name the token clearly (e.g., `GH Actions - Hermes Workers`)
6. Copy the token and add it as the corresponding GitHub secret

## Workflow Mapping

| Workflow File | Config File | Secret Used |
|---------------|-------------|-------------|
| `.github/workflows/workers-hermes.yml` | `wrangler.hermes.toml` | `CF_API_TOKEN_HERMES` |
| `.github/workflows/workers-gemini.yml` | `wrangler.gemini.toml` | `CF_API_TOKEN_GEMINI` |
| `.github/workflows/workers-aipass.yml` | `wrangler.aipass.toml` | `CF_API_TOKEN_AIPASS` |

## Archived Workflow

- Old `workers-builds.yml` → `workers-builds.yml.legacy` (no longer used)

---
*Generated during Phase 4 GitHub Actions setup*