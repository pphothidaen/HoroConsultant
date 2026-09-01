# Rule 23: Automated Pull Request and Deployment Orchestration

## Purpose

Govern automated PR creation, CI monitoring, merge, and deployment workflows
where Hermes (the orchestrator) acts as human proxy for routine operations.

## Credential Sources

Credentials MUST be read from approved sources in this priority order:

1. **Environment variables** (`.env` file loaded by shell):
   - `GH_TOKEN` — GitHub Personal Access Token for `gh` CLI
   - `DOPPLER_PROJECT`, `DOPPLER_ENVIRONMENT`, `DOPPLER_CONFIG` — Doppler config

2. **Doppler secret manager** (when available):
   ```bash
   doppler secrets get GH_TOKEN --plain
   doppler secrets get VERCEL_TOKEN --plain
   doppler secrets get HF_TOKEN --plain
   ```

3. **Never hardcode** — credentials in files, logs, or commits are forbidden.

## Automated PR Workflow

When CI passes on a feature branch and the user approves merge:

1. **Create PR** (if not exists):
   ```bash
   gh pr create --title "..." --body "..."
   ```

2. **Monitor CI**:
   ```bash
   gh pr checks --watch
   ```

3. **Merge** (when green and approved):
   ```bash
   gh pr merge --squash --delete-branch
   ```

4. **Deploy** (post-merge on main):
   - Vercel: auto-deploys on push to main
   - HF: `python3 scripts/publish_space_hf.py --sdk docker`

## Permitted Automated Actions

| Action | Condition |
|--------|-----------|
| `git push origin <branch>` | Any feature branch |
| `gh pr create` | When branch is ready |
| `gh pr merge --squash` | CI green + user approval |
| `gh pr checks --watch` | After PR creation |
| `vercel --prod` | Post-merge with approval |
| `publish_space_hf.py` | Post-merge with approval |

## Forbidden Actions

| Action | Reason |
|--------|--------|
| `git push origin main` | Blocked by GitHub ruleset |
| `git push --force` | Force push forbidden |
| `gh pr merge` without CI green | Quality gate |
| Deploy without user approval | Production safeguard |
| Expose credentials in logs | Security policy |

## Human Override

The user may at any time:
- Take over PR creation manually
- Request specific PR title/body
- Hold merge for additional review
- Rollback any deployment

When human override occurs, Hermes stops automation and reports status.
