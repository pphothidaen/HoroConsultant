# twg CLI Commands Reference

> All commands verified with `twg v1.3.1` at `$HOME/.local/bin/twg`
> Auth: `twg login` (OAuth device flow) — token stored in `~/.config/twg/auth.conf`

---

## Authentication
```bash
# User must run this interactively in their terminal
~/.local/bin/twg login
# Opens browser for OAuth device authorization

# Verify auth status
twg doctor
# Expected: "Auth complete ✅" + "Binary v1.3.1 ✅"
```

---

## Teams (Created: 6 teams)

```bash
# List all teams
twg teams get

# Create team (requires --scope-id from `twg teams get` output)
twg teams create --name "Management" --scope-id <site-ari> -y
twg teams create --name "DevCore" --scope-id <site-ari> -y
twg teams create --name "DevAPI" --scope-id <site-ari> -y
twg teams create --name "QA" --scope-id <site-ari> -y
twg teams create --name "Security" --scope-id <site-ari> -y
twg teams create --name "BA" --scope-id <site-ari> -y

# List team members
twg teams members --team-id <team-id>

# Update team
twg teams update --team-id <team-id> --name "New Name"
```

---

## Jira Workitems (Created: 24 sub-tasks KAN-43 to KAN-66)

```bash
# Query issues
twg jira workitem query --jql "project = KAN AND status != Done"

# Create sub-task
twg jira workitem create \
  --project KAN \
  --type Sub-task \
  --summary "B5: fix fast_return path" \
  --parent KAN-40 \
  --labels "agent-codex1,effort-5"

# Bulk transition to Done
twg jira workitem bulk-transition \
  --jql "parent = KAN-40 AND status = Done" \
  --transition Done

# Update issue labels
twg jira workitem update --id KAN-43 --add-labels "sync-complete"
```

---

## Goals (Jira Plans / OKR)

```bash
# Query goals
twg goals query --query "Audit Remediation"

# Update goal status
twg goals update --goal-key KAN-38 --status "In Progress"

# Archive goal
twg goals archive --goal-key KAN-38
```

---

## Projects & Focus Areas
```bash
twg projects query --query "KAN"
twg focus-areas query --query "Audit"
```

---

## Dashboard (Created: Dashboard ID 10034)
```bash
# Create dashboard
twg jira dashboard create --name "HOROC Audit Remediation" --description "Audit remediation tracking"

# Add gadgets (4 gadgets added)
twg jira dashboard gadget add --dashboard-id 10034 --type "two-dimensional-filter-statistics" --title "Effort vs Status"
twg jira dashboard gadget add --dashboard-id 10034 --type "filter-results" --title "Active Sub-tasks"
twg jira dashboard gadget add --dashboard-id 10034 --type "sprint-health" --title "Sprint Health"
twg jira dashboard gadget add --dashboard-id 10034 --type "work-item-statistics" --title "Work Item Statistics"
```

---

## Notes
- `twg plans` — NOT AVAILABLE in v1.3.1 (use REST API or UI)
- `twg sync` — NOT AVAILABLE in v1.3.1 (use REST API or UI)
- All commands require valid OAuth token (run `twg doctor` to verify)
- `-y` flag skips confirmation prompts (for automation)