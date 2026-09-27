# Plan: Triage & Resolve Three Blocking CI/CD Issues (Code Scanning, Render Deploy, GitBook Sync)

## Goal

Brainstorm, decompose, and assign resolution paths for three outstanding
blocking items — **Code scanning (Copilot claude-opus-5)**, **Render deploy
(update_failed)**, and **GitBook site sync** — determining which can be
resolved by automated subagents and which require direct owner action.

---

## Current Context / Assumptions

### Repository State
- **Branch**: `fix/KAN-128-docker-schemas-and-jira-sync` (clean, 2 commits ahead of main)
- **Recent commits**:
  - `a13ab0ce` — [KAN-128] Copy `schemas/` into Docker images + `--yes` to `twg login`
  - `9192914d` — [KAN-128] Tests + provenance manifest for Dockerfile schemas + sync-jira
- **TICKET-KAN-128** is marked `DONE` in `ATOMIC_TICKET.md` — it fixed one root cause of
  `update_failed` (missing `schemas/` in Docker image causing container exit code 1).
- But `update_failed` **persists**, per `TICKET-GEMINI-BRIDGE-20260921-Z-INTEGRATION`
  (line 62 of `ATOMIC_TICKET.md`): Render free-tier service creation now requires
  billing info; the service was never provisioned; the `RENDER_API_KEY` GitHub
  secret was invalid and replaced with Doppler `RENDER_TOKEN`.

### Key Files Discovered
| File | Role |
|---|---|
| `.github/workflows/deploy-render.yml` | Triggers Render deploy via API; polls for `live`/`update_failed` terminal states |
| `render.yaml` | Render Blueprint: `dockerfilePath: ./Dockerfile`, `plan: free`, `healthCheckPath: /health` |
| `Dockerfile` | Rust `horo_server` gateway + Python worker (production; used by Render) |
| `Dockerfile.render` | Python-only uvicorn (dev/local) |
| `Dockerfile.hf` | HF Spaces Dockerfile (retired per KAN-124) |
| `scripts/sync-render-secrets.sh` | Syncs Doppler `prd` secrets → Render env vars (NOT called by any workflow) |
| `scripts/sync_doppler_secrets.py` | Upserts CI GitHub secrets to Doppler project |
| `.github/workflows/ai_agent_ecosystem_sync.yml` | Validates `.agents/` ↔ `.codex/` sync (uses `DOPPLER_TOKEN`) |
| `docs/repository-guidelines.md` (line 20) | Documents GitBook sync failure: branch protection blocks GitBook pushes |
| `scripts/test_provenance_guard.py` | Fail-closed guard; `DOC_FILES` set already includes `"gitbook-docs.yaml"` (line 49) |
| `ATOMIC_TICKET.md` (line 62) | TICKET-GEMINI-BRIDGE-20260921-Z-INTEGRATION: Render blocked on billing; RENDER_API_KEY invalid |

### No Code Scanning Infrastructure in Repo
- There is **no** `.github/codeql/` directory, no `code-scanning.yml` workflow,
  no CodeQL configuration, no Dependabot config, and no GitHub-native code
  scanning workflow anywhere in `.github/`.
- The `code-review.yml` workflow uses a custom `agent-code_reviewer`, not GitHub
  native scan.
- "Code scanning (Copilot claude-opus-5)" is a **GitHub account/organization-level**
  setting configured via the GitHub web UI — it cannot be changed via repo files.

### GitBook Sync Infrastructure
- `gitbook-docs.yaml` existed at repo root (commits `30b6f8e0`, `1a9bd646`,
  `189a4a45`), then was deleted by `b653e9ec` ([KAN-84] cleanup).
- There is **no** GitBook sync workflow in `.github/workflows/`.
- GitBook's GitHub integration pushes docs directly to the repo branch.
- Branch protection requires a `test provenance` status check to pass before
  any push — but GitBook's automated sync doesn't trigger CI, so the check
  never runs and the push is blocked.
- `gitbook-docs.yaml` is still listed in the `DOC_FILES` set in
  `test_provenance_guard.py` (line 49) and in the `allowed_source_paths` of
  `plans/test_provenance/ticket-kan85-ci-fix4.json`.

### Current Branch Protection / Status Checks
- From `docs/repository-guidelines.md` (line 20): "GitHub branch protection
  requires `test provenance` status check to pass before pushes."
- The `test_provenance.yml` workflow runs `verify-pr` on PRs and pushes to main.

---

## Architecture / Proposed Approach

Three distinct issue classes, each requiring a different resolution strategy:

1. **Code scanning** — Purely a GitHub account/org UI configuration issue.
   No repository code change can fix an unsupported model selected at the
   platform level. **Owner must act via GitHub web UI.**

2. **Render deploy** — Has a code-level half (already fixed by KAN-128:
   schemas in Dockerfile) and a platform-level half (billing + invalid
   secret). The owner must add a payment method on Render. A **devops
   subagent can** harden the workflow (add secret sync step, better
   diagnostics, update monitoring to target Render) so that once the owner
   adds billing, the deploy succeeds.

3. **GitBook site sync** — A branch-protection-vs-automated-push conflict.
   A **developer_api subagent can** restore the GitBook config file, add a
   GitBook webhook-driven PR creation workflow, and document the workaround.
   The owner must add GitBook's service account to the branch protection
   bypass list (or exclude docs paths) — this is a GitHub repo setting.

---

## Step-by-Step Tasks

### Issue 1: Code scanning (Copilot claude-opus-5) — OWNER ONLY

**Root Cause**: GitHub's native code scanning uses Copilot with the
`claude-opus-5` model, which is not a supported model for code scanning.
This setting is configured at the GitHub account/organization level, not in
the repository.

**Owner Action (manual, GitHub web UI)**:
1. Navigate to GitHub → **Settings** → **Code security and analysis**.
   - Org-level: `github.com/organizations/<org>/settings/security_analysis`
   - Repo-level: `github.com/<owner>/<repo>/settings/security_analysis`
2. Under "Code scanning", find the model selection.
3. Change the model from `claude-opus-5` to a supported model. Recommended
   supported options:
   - `claude-3.7-sonnet` (Claude 3.7 Sonnet)
   - `gpt-4o` (OpenAI)
   - `gemini-2.0-flash` (Google)
4. Save the change.
5. Re-run code scanning manually via the GitHub UI ("Analyze" → "Code scanning").

**Subagent CANNOT do**: No repository file controls this setting. A subagent
cannot access the GitHub web UI or change account/org-level settings.

**Verification**: Owner should confirm in the GitHub UI that:
- Code scanning runs without the "unsupported model" error.
- The model dropdown shows a supported model selected.

**Jira ticket**: This issue should be filed as a Jira ticket (e.g.
`KAN-129`) and labeled `agent-orchestrator` for tracking.

---

### Issue 2: Render deploy (update_failed) — OWNER + DEVOPS SUBAGENT

**Root Cause (dual)**:
1. **Already fixed by KAN-128**: Missing `schemas/` in Docker image caused
   container exit code 1 → Render `update_failed`. Fixed in the current
   branch (`fix/KAN-128-docker-schemas-and-jira-sync`).
2. **Still blocking**: Render free-tier service was never provisioned because
   Render now requires billing info for free services. The `RENDER_API_KEY`
   GitHub secret was invalid; it has been replaced in Doppler as
   `RENDER_TOKEN` but the GitHub secret was not updated. The `deploy-render.yml`
   workflow uses `secrets.RENDER_API_KEY` which is stale.

**Owner Action (manual)**:
1. Navigate to [dashboard.render.com](https://dashboard.render.com).
2. Add a **billing card** (Render free tier now requires it for service
   creation).
3. Manually create the `horoconsultant-core-backend` web service using
   `render.yaml`, or allow the `deploy-render.yml` workflow's auto-discovery
   to find it after creation.
4. Verify the Render service ID matches what's in the `RENDER_SERVICE_ID`
   GitHub secret (or let auto-discovery handle it).

**DevOps Subagent Tasks (doable without Render dashboard access)**:

#### Task 2.1: Update `deploy-render.yml` to use `RENDER_TOKEN` from Doppler
- **File**: `.github/workflows/deploy-render.yml`
- **Problem**: The workflow references `${{ secrets.RENDER_API_KEY }}` but
  the valid token is now stored in Doppler as `RENDER_TOKEN`.
- **Fix**: Add a `sync-render-secrets.sh` invocation before the deploy trigger
  to ensure the `RENDER_API_KEY` GitHub secret is in sync. OR add a fallback
  to read from Doppler if `RENDER_API_KEY` is empty.
- **Patch** (insert as a new step before "Trigger Render deploy"):

```yaml
      - name: Sync Render secrets from Doppler
        env:
          DOPPLER_SERVICE_TOKEN: ${{ secrets.DOPPLER_SERVICE_TOKEN }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
        run: |
          set -euo pipefail
          if [ -z "$RENDER_API_KEY" ]; then
            echo "RENDER_API_KEY is empty — fetching from Doppler..."
            DOPPLER_TOKEN="${DOPPLER_SERVICE_TOKEN}" python3 -c "
import os, urllib.request, json
token = os.environ['DOPPLER_TOKEN']
url = 'https://api.doppler.com/v3/configs/config/secrets?project=horo-consultant&config=prd'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
secrets = json.load(urllib.request.urlopen(req))['secrets']
render_key = secrets.get('RENDER_API_KEY', {}).get('computed', '') or secrets.get('RENDER_TOKEN', {}).get('computed', '')
print(f'RENDER_API_KEY={render_key}')
' > /tmp/render_key.txt
            # Write to GITHUB_OUTPUT for downstream steps
            KEY=$(grep '^RENDER_API_KEY=' /tmp/render_key.txt | cut -d= -f2-)
            echo "render_api_key=${KEY}" >> $GITHUB_OUTPUT
          else
            echo "render_api_key=${RENDER_API_KEY}" >> $GITHUB_OUTPUT
          fi
```

- Then update the API key references to use `${{ steps.sync.outputs.render_api_key || secrets.RENDER_API_KEY }}`.

> **Note**: A cleaner approach is to fix the GitHub secret directly. But a
> subagent can add the Doppler fallback as a stopgap and document the
> recommendation. See Task 2.4 for the secret rotation recommendation.

#### Task 2.2: Add secret sync step to `deploy-render.yml`
- **File**: `.github/workflows/deploy-render.yml`
- Add a step that runs `scripts/sync-render-secrets.sh` to ensure all
  production env vars (database URLs, API keys, etc.) are pushed to the
  Render service before triggering the deploy.
- This requires `DOPPLER_SERVICE_TOKEN`, `RENDER_API_KEY`, and
  `RENDER_SERVICE_ID` as environment variables.

```yaml
      - name: Sync production env vars to Render
        env:
          DOPPLER_SERVICE_TOKEN: ${{ secrets.DOPPLER_SERVICE_TOKEN }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY || steps.sync.outputs.render_api_key }}
          RENDER_SERVICE_ID: ${{ steps.deploy.outputs.service_id || secrets.RENDER_SERVICE_ID }}
        run: |
          if [ -n "$RENDER_SERVICE_ID" ] && [ -n "$RENDER_API_KEY" ]; then
            bash scripts/sync-render-secrets.sh
          else
            echo "Skipping secret sync — RENDER_SERVICE_ID or RENDER_API_KEY not yet available"
          fi
```

#### Task 2.3: Add Render deploy log capture on failure
- **File**: `.github/workflows/deploy-render.yml`
- **Problem**: When Render reports `update_failed`, the workflow exits with
  code 1 but doesn't capture the Render deploy logs for debugging.
- **Fix**: Add a step that runs on failure (`if: failure()`) to fetch and
  print the Render deploy logs.

```yaml
      - name: Capture Render deploy logs on failure
        if: failure()
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ steps.deploy.outputs.service_id || secrets.RENDER_SERVICE_ID }}
          DEPLOY_ID: ${{ steps.deploy.outputs.deploy_id }}
        run: |
          echo "=== Render Deploy Logs ==="
          curl -sS \
            -H "Authorization: Bearer ***" \
            "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys/${DEPLOY_ID}/logs" \
            2>/dev/null | python3 -c "import sys,json; [print(l.get('line','')) for l in json.load(sys.stdin).get('logs',[])]" 2>/dev/null || \
            echo "(Could not fetch deploy logs — check Render dashboard)"
```

#### Task 2.4: Update `production_monitor.yml` to monitor Render
- **File**: `.github/workflows/production_monitor.yml`
- **Problem**: The monitor still checks the retired HF backend
  (`pphothidaen-horoconsultant-core-backend.hf.space`) instead of Render
  (`horoconsultant-core-backend.onrender.com`).
- **Fix**: Add a Render health check alongside the existing checks.

```yaml
      RENDER_BACKEND_URL: https://horoconsultant-core-backend.onrender.com
```

Then add a health check step:

```yaml
      - name: Health check Render backend
        run: |
          set -euo pipefail
          code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "${RENDER_BACKEND_URL}/health" || true)
          echo "Render /health -> ${code}"
          [ "${code}" = "200" ] || echo "⚠️ Render backend health check failed"
```

#### Task 2.5: Update README production architecture
- **File**: `README.md` (line 460-461)
- **Problem**: README still lists "Hugging Face Docker backend" as production
  target, but HF was retired (KAN-124) and Render is now primary.
- **Fix**:

```diff
-2. **Hugging Face Docker backend** — `pphothidaen/horoconsultant-core-backend`
+2. **Render Docker backend** — `https://horoconsultant-core-backend.onrender.com`
```

#### Task 2.6: Document the Render secret rotation recommendation
- **File**: `docs/architecture/deployment-rail.md` or a new doc
- Document that the `RENDER_API_KEY` GitHub secret should be rotated to
  match the Doppler `RENDER_TOKEN`, and that `RENDER_SERVICE_ID` must be
  populated once the Render service is created.

**Verification for Issue 2**:
```bash
# Verify render.yaml is syntactically valid
python3 -c "import yaml; yaml.safe_load(open('render.yaml')); print('render.yaml: VALID')"
# Verify Dockerfile builds locally (if Docker available)
docker build -f Dockerfile -t horoconsultant:test . --build-arg GIT_COMMIT_HASH=test
# Run test provenance guard
python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD --post-squash-merge
```

**Jira ticket**: Create a new Jira ticket (e.g.
`KAN-130-CI-DEPLOY-RENDER-FIX`) and assign to `agent-devops` for the
subagent tasks. Owner tasks are explicitly called out.

---

### Issue 3: GitBook site sync ⚠️ NEEDS OWNER + developer_api SUBAGENT

**Root Cause**: GitBook's GitHub integration pushes documentation changes
directly to the repo branch. GitHub branch protection requires a `test
provenance` status check to pass before any push — but GitBook's automated
sync doesn't trigger CI, so the status check never runs and the push is
rejected. Additionally, the `gitbook-docs.yaml` config file was deleted in
commit `b653e9ec`, removing GitBook's site configuration.

**Owner Action (manual, GitHub web UI)**:
1. Navigate to GitHub → **Settings** → **Branches** →
   `main` branch protection rule.
2. Under "Bypass branch protections", add GitBook's GitHub App/service account
   (`gitbook[bot]` or the GitBook integration user) so it can push without
   requiring the `test provenance` status check.
   - OR: Add an exclusion for docs paths (`docs/**`, `gitbook-docs.yaml`,
     `SUMMARY.md`) under "File and folder exclusions" in the branch
     protection rule.
3. Verify the GitBook API token is configured (if using a GitHub Action
   webhook approach — see subagent Task 3.2).

**developer_api Subagent Tasks**:

#### Task 3.1: Restore `gitbook-docs.yaml` from git history
- **File**: `gitbook-docs.yaml` (was deleted in commit `b653e9ec`)
- **Recovery**: Restore from commit `189a4a45` (the last version before
  deletion). Use `git show 189a4a45:gitbook-docs.yaml`.
- **Verification**:
```bash
git show 189a4a45c64d7e12:gitbook-docs.yaml  # Show the file content
# Then recreate it with write_file
```
- The recovered content was:
```yaml
$schema: https://api.gitbook.com/gitbook-docs.yaml
site:
  title: Pphothidaen Docs
  structure:
    - type: space
      key: space-1
      title: Untitled
      path: untitled
      default: true
      content:
        directory: ./
```
> **Note**: This file should NOT be committed without verifying it matches
> the current GitBook space configuration. The owner should confirm the
> correct GitBook space key/title before committing. The subagent should
> create the file as a draft and flag it for owner review.

#### Task 3.2: Add GitBook webhook → PR GitHub Action
- **File**: `.github/workflows/gitbook-webhook-pr.yml` (new)
- **Problem**: GitBook's automated sync pushes directly to `main`, which is
  blocked by branch protection. Instead, use a webhook-driven approach that
  creates a PR (which triggers CI, satisfies the test provenance check, and
  can be auto-approved/merged).
- **Approach**: Set up a `workflow_dispatch` or `repository_dispatch` workflow
  that GitBook webhooks can trigger. The workflow creates a branch from the
  latest GitBook export, commits the updated docs, opens a PR, and runs CI.

```yaml
name: GitBook Webhook Sync → PR

on:
  repository_dispatch:
    types: [gitbook-sync-request]
  workflow_dispatch:
    inputs:
      source:
        description: "GitBook export source (branch or commit)"
        required: false
        default: "main"

permissions:
  contents: write
  pull-requests: write

jobs:
  create-docs-pr:
    name: Create PR from GitBook webhook
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate docs from GitBook export
        run: |
          # This step would pull the latest GitBook export and update docs/
          # For now, this is a placeholder — the actual GitBook export
          # mechanism needs to be configured by the owner
          echo "GitBook webhook received — placeholder for docs sync"
          echo "TODO: Implement GitBook export fetch and docs/ directory update"

      - name: Create branch and PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRANCH="gitbook-sync-$(date +%Y%m%d-%H%M%S)"
          git checkout -b "$BRANCH"
          git add docs/
          if ! git diff --staged --quiet; then
            git commit -m "docs(gitbook): auto-sync from GitBook webhook [skip ci]"
            git push origin "$BRANCH"
            gh pr create --title "docs(gitbook): Auto-sync from GitBook" \
              --body "Auto-generated PR from GitBook webhook sync." \
              --base main --head "$BRANCH"
          else
            echo "No changes to commit"
          fi
```

> **Requirement**: The owner must configure the GitBook webhook in the
> GitBook dashboard to send a `repository_dispatch` event to this workflow.
> The GitBook → GitHub integration settings need to be configured.

#### Task 3.3: Update `docs/repository-guidelines.md` with resolution status
- **File**: `docs/repository-guidelines.md` (line 20)
- Update the "Current State" from `⚠️ Sync failing` to document the new
  webhook-driven PR approach and the branch protection bypass.

#### Task 3.4: Verify `gitbook-docs.yaml` is in DOC_FILES
- **File**: `scripts/test_provenance_guard.py`
- Confirm line 49: `"gitbook-docs.yaml"` is in the `DOC_FILES` set. (Already
  verified — it IS present.)
- No change needed, but document this in the plan.

**Verification for Issue 3**:
```bash
# Verify test_provenance_guard.py recognizes gitbook-docs.yaml
python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD --post-squash-merge
# Should pass without "PR_SOURCE_PATH_WITHOUT_BASELINE" errors for gitbook-docs.yaml
```

**Jira ticket**: Create `KAN-131-DOCS-GITBOOK-SYNC-FIX` and assign to
`agent-developer_api`.

---

## Tests / Validation

### TDD Cycle for Each Code Change

Follow the project's test-first provenance model:

1. **Write a failing test first** in `project/tests/` or `tests/`.
2. **Record RED baseline** in a `plans/test_provenance/ticket-<id>.json`
   manifest.
3. **Implement the minimal fix**.
4. **Run the test to verify GREEN**.
5. **Commit** with a Jira ticket reference in the commit message.
6. **Run the full CI guard**:

```bash
# Verify test provenance
python3 scripts/test_provenance_guard.py verify-pr --base origin/main~1 --head HEAD --post-squash-merge

# Run relevant tests
python3 -m pytest tests/ -v --tb=short -k "render or gitbook or deploy or provenance"

# Verify ecosystem sync
python3 scripts/sync_ai_agent_ecosystem.py --check
```

### No-code changes (owner actions)
For Issues 1 and 3-owner-actions, validation is manual:
- Issue 1: Confirm code scanning runs successfully in the GitHub UI.
- Issue 3: Confirm GitBook can push to a bypass branch after adding the
  service account to the branch protection bypass list.

---

## Subagent Assignment Matrix

| Issue | Component | Owner (Human) | Subagent | Skill |
|---|---|---|---|---|
| 1. Code scanning | Model selection (GitHub UI) | ✅ Must change model in GitHub Settings → Code Security | ❌ Cannot access GitHub UI | N/A |
| 1. Code scanning | N/A (no repo change needed) | — | ❌ No repo action possible | N/A |
| 2. Render deploy | Billing card on dashboard.render.com | ✅ Must add payment method | ❌ Cannot access Render dashboard | N/A |
| 2. Render deploy | Workflow hardening (`.github/workflows/deploy-render.yml`) | | ✅ `devops` | `devops-deployment`, `qa-e2e-testing` |
| 2. Render deploy | Monitoring (`production_monitor.yml`) | | ✅ `devops` | `devops-deployment`, `qa-e2e-testing` |
| 2. Render deploy | README update (`README.md`) | | ✅ `developer` | `sdlc-aisdlc-workflow` |
| 3. GitBook sync | Branch protection bypass (GitHub UI) | ✅ Must add GitBook bot to bypass list | ❌ Cannot access GitHub Settings | N/A |
| 3. GitBook sync | Restore `gitbook-docs.yaml` | (review only) | ✅ `developer_api` | `sdlc-aisdlc-workflow` |
| 3. GitBook sync | Webhook → PR workflow (`.github/workflows/gitbook-webhook-pr.yml`) | (configure webhook in GitBook UI) | ✅ `developer_api` | `sdlc-aisdlc-workflow` |
| 3. GitBook sync | Update `docs/repository-guidelines.md` | | ✅ `lead_ba` | `bsa-doc-skill-management` |

### Subagent Dispatch Plan
Each subagent-dispatched task must include:
- **Jira ticket reference** in the task goal (per KAN-105 governance).
- **Exact file paths** as writable scope.
- **Test provenance manifest** creation for any code/test changes.
- **Branch ownership**: one subagent per file, no concurrent edits to the
  same file.

**Recommended dispatch order** (to preserve single-editor ownership):
1. `devops` subagent: Tasks 2.1–2.6 (Render workflow hardening + monitoring)
2. `developer_api` subagent: Tasks 3.1–3.2 (GitBook config restore + webhook PR workflow)
3. `lead_ba` subagent: Task 3.3 (docs update)
4. `developer` subagent: (if needed) Task 2.5 (README update) — or combine with devops

---

## Risks, Tradeoffs, and Open Questions

### Risks
1. **Render free-tier billing requirement**: Render now requires billing info
   even for free-tier services. The owner MUST add a payment method. This
   is completely outside subagent control. If the owner doesn't act, the
   Render deploy will remain `update_failed`.

2. **Stale `RENDER_API_KEY` GitHub secret**: The current `deploy-render.yml`
   references `secrets.RENDER_API_KEY`, but the valid token is in Doppler as
   `RENDER_TOKEN`. If the owner doesn't update the GitHub secret, the
   workflow will fail even after billing is added. **Recommendation**: Owner
   should update the `RENDER_API_KEY` GitHub secret to the Doppler
   `RENDER_TOKEN` value, OR the subagent should implement the Doppler
   fallback (Task 2.1).

3. **GitBook webhook configuration**: The webhook → PR workflow (Task 3.2)
   requires the owner to configure the GitBook webhook endpoint in the
   GitBook dashboard. Without this, the workflow will never be triggered.

4. **Branch protection bypass for GitBook**: If the owner doesn't add GitBook's
   service account to the bypass list, GitBook's automated sync will continue
   to fail. The webhook → PR approach (Task 3.2) is an alternative but
   requires webhook setup.

5. **README staleness**: The README still references the retired HF backend
   as the production target (line 461). This is misleading but not blocking.

### Tradeoffs
1. **Doppler fallback vs. direct secret update**: Task 2.1 adds a Doppler
   fallback to the workflow, but this is a workaround. The cleaner solution
   is for the owner to directly update the `RENDER_API_KEY` GitHub secret.
   The Doppler fallback adds complexity to the workflow.

2. **Webhook → PR vs. branch protection bypass**: Two approaches for GitBook
   sync:
   - **Branch protection bypass** (owner action): Simpler, but allows GitBook
     to push directly to `main` without CI checks.
   - **Webhook → PR** (subagent): More robust (CI runs on every docs change),
     but requires webhook configuration and more code.

3. **`render.yaml` plan**: The `render.yaml` uses `plan: free`. If the owner
   adds billing, the free plan should work. But Render's free tier may have
   sleep/deactivation policies. Upgrading to a paid plan is an owner decision.

### Open Questions
1. **Code scanning**: What is the exact GitHub Settings path for the code
   scanning model? Is it at the org level or repo level? (Owner needs to
   investigate.)
2. **Render**: What is the current `RENDER_SERVICE_ID`? Does the Render
   service exist at all (it was "never provisioned" per the ticket)?
3. **GitBook**: What is the exact GitBook bot/service account name that
   needs to be added to the branch protection bypass list?
4. **GitBook token**: Is there a `GITBOOK_API_TOKEN` or `GITBOOK_TOKEN`
   GitHub secret configured? (No reference to such a secret was found in
   the repo.)
5. **Production monitoring**: Should `production_monitor.yml` monitor
   Render, HF (retired), or both? (The monitor currently checks HF, which
   is retired.)

---

## Execution Dependencies

```
Issue 1 (Code scanning):
  └── Owner: change model in GitHub Settings    [BLOCKED — Owner only]

Issue 2 (Render deploy):
  ├── Owner: add billing card at dashboard.render.com    [BLOCKED — Owner only]
  ├── Owner: update RENDER_API_KEY GitHub secret          [BLOCKED — Owner only]
  ├── devops subagent: Task 2.1 (Doppler fallback)        [READY — parallel with owner]
  ├── devops subagent: Task 2.2 (secret sync step)        [READY — parallel with owner]
  ├── devops subagent: Task 2.3 (log capture on failure)  [READY — independent]
  ├── devops subagent: Task 2.4 (monitor Render)          [READY — independent]
  ├── developer subagent: Task 2.5 (README update)        [READY — independent]
  └── devops subagent: Task 2.6 (document secret rotation) [READY — independent]

Issue 3 (GitBook site sync):
  ├── Owner: add GitBook bot to branch protection bypass  [BLOCKED — Owner only]
  ├── developer_api subagent: Task 3.1 (restore gitbook-docs.yaml) [READY — independent]
  ├── developer_api subagent: Task 3.2 (webhook → PR)     [READY — independent]
  ├── lead_ba subagent: Task 3.3 (update docs)            [READY — independent]
  └── qa_tester subagent: Task 3.4 (verify guard)         [READY — independent]
```

### Post-Resolution
After the owner actions are complete and the subagent tasks are done:
1. Merge all subagent PRs.
2. Re-run `deploy-render.yml` (workflow_dispatch) after billing is added.
3. Re-trigger code scanning via GitHub UI after model change.
4. Re-trigger GitBook sync after branch protection bypass is configured.
5. Update `ATOMIC_TICKET.md` with completion evidence.
6. Archive this plan to `plans/archive/YYYY-MM-DD-sprint-ci-cd-triage/`.
7. Compile `ReleaseNotes.md` if all three issues are resolved.
