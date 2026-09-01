---
name: github-pr-automation
description: Automated PR creation, CI monitoring, merge, and deployment via gh CLI.
---

# GitHub PR Automation

## Purpose

Automate the workflow from branch push through PR creation, CI monitoring,
merge, and deployment. Hermes acts as human proxy for routine operations.

## Credential Resolution

Resolve GitHub token from approved sources (in priority order):

1. **Environment variable**: `GH_TOKEN` (from `.env`)
2. **Doppler**: `doppler secrets get GH_TOKEN --plain`
3. **gh CLI auth**: `gh auth status` (if already logged in)

```bash
# Load from .env
source ~/.zshrc && export GH_TOKEN=$(grep GH_TOKEN .env | cut -d'"' -f2)

# Or from Doppler
export GH_TOKEN=$(doppler secrets get GH_TOKEN --plain)
```

## Workflow

### 1. Create PR

```bash
gh pr create \
  --title "feat: descriptive title" \
  --body "## Summary\n- Change 1\n- Change 2\n\n## Test plan\n- [ ] CI passes\n- [ ] Deploy to production" \
  --base main \
  --head feature-branch
```

### 2. Monitor CI

```bash
# Watch CI status
gh pr checks --watch

# Check specific PR
gh pr checks 14
```

### 3. Merge (when CI green)

```bash
# Squash merge (recommended)
gh pr merge 14 --squash --delete-branch

# Or regular merge
gh pr merge 14 --merge --delete-branch
```

### 4. Deploy (post-merge)

```bash
# Vercel auto-deploys on push to main
# For HF backend:
python3 scripts/publish_space_hf.py --sdk docker --check-health
```

## Safety Rules

| Rule | Enforcement |
|------|-------------|
| Never push to main | GitHub ruleset blocks this |
| Never force push | `pre_tool_check.py` blocks this |
| Never merge without CI green | Check `gh pr checks` first |
| Never deploy without approval | User must approve production deploy |
| Never expose tokens | Don't log or echo credentials |

## Error Handling

| Error | Action |
|-------|--------|
| `gh auth` fails | Ask user to run `gh auth login` |
| CI fails | Report failures, wait for fix |
| Merge conflicts | Ask user to resolve |
| Deploy fails | Rollback, report error |

## Integration with Rules

- **Rule 11**: Orchestrator delegates PR automation to Hermes
- **Rule 17**: Multi-account dispatch doesn't apply to PR automation
- **Rule 23**: This skill implements Rule 23
- **pre_tool_check.py**: Allows `gh pr` and `gh run` commands
