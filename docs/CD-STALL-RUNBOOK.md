# CD Stall Runbook — KAN-173 Watchdog

## Purpose
This runbook documents the **ops-watchdog** (KAN-173) that monitors for silent CD pipeline stalls on the `gemini-web-bridge` worker deployment. The watchdog detects when a deploy is stuck at a gate (previously a 51-minute 503 alert gap with no alert) and creates a loud, trackable incident.

---

## Architecture

### Components
| Component | Location | Role |
|-----------|----------|------|
| `cd-watchdog.yml` | `.github/workflows/cd-watchdog.yml` | Scheduled workflow (every 10 min) that checks for stalled deployments |
| `ops-watchdog` skill | `.agents/skills/ops-watchdog/SKILL.md` | Reusable runbook + implementation pattern |
| Watchdog tracker issue | GitHub Issues (auto-created) | Single idempotent issue per stall incident |
| Jira alert | KAN project | Human-visible escalation |
| Auto-close | On resolution | Closes tracker issue + Jira when deploy completes |

### Detection Logic
1. **Trigger**: Workflow runs every 10 minutes (`*/10 * * * *`)
2. **Query**: Checks `gemini-web-bridge` worker deployments via Cloudflare API
3. **Stall condition**: Deployment in `pending` or `queued` state > 15 minutes with no progress
4. **Gate-awareness**: Respects `environment: production` + `cd-concurrency-audit` gate

---

## Runbook: CD Stall Detected

### When Watchdog Fires
**Alert channels**: GitHub Issue (tracker), Jira (KAN ticket), optional Slack/Discord/Telegram

**Tracker issue template** (auto-populated):
```
Title: [WATCHDOG] gemini-web-bridge deploy stalled — <deployment-id>
Labels: watchdog, cd-stall, gemini-web-bridge
Body:
- Deployment ID: <id>
- Environment: production
- Stalled since: <timestamp> (UTC)
- Current status: <pending|queued>
- Minutes stalled: <N>
- Gate status: <cd-concurrency-audit / environment:production>
- Cloudflare dashboard: https://dash.cloudflare.com/...
- Runbook: docs/CD-STALL-RUNBOOK.md
```

### Immediate Triage (≤ 5 min)
1. **Open tracker issue** — verify it's not a duplicate (idempotent by deployment ID)
2. **Check Cloudflare dashboard** → Workers → `gemini-web-bridge` → Deployments
3. **Identify the gate**:
   - `environment: production` — requires manual approval in GitHub Actions
   - `cd-concurrency-audit` — concurrency limit (1 at a time) blocked by prior run
4. **Check logs** — `gh run view <run-id> --log` for the stalled workflow

### Resolution Paths

#### A. Stuck at `environment: production` gate (most common)
- **Cause**: Deploy waiting for human approval in GitHub Actions
- **Action**: 
  - If intentional: approve in GitHub Actions → deploy resumes
  - If accidental: cancel workflow, investigate why approval wasn't triggered
- **Watchdog**: Auto-closes tracker when deployment reaches `success`

#### B. Stuck at `cd-concurrency-audit` gate
- **Cause**: Previous deployment still running (or zombie)
- **Action**:
  - Check for running deployments: `gh run list --workflow=cd.yml --status=in_progress`
  - Cancel zombie run if stuck > 30 min: `gh run cancel <run-id>`
  - Re-trigger: `gh workflow run cd.yml`
- **Watchdog**: Auto-closes tracker when new deployment succeeds

#### C. Cloudflare API / infrastructure issue
- **Cause**: Cloudflare Workers API returning errors, rate limits, or partial outage
- **Action**:
  - Check Cloudflare status page
  - Retry deployment: `gh workflow run cd.yml`
  - If persistent: escalate to Cloudflare support
- **Watchdog**: Continues firing every 10 min until resolved

#### D. Build failure not surfacing correctly
- **Cause**: Build passes but deploy step hangs silently
- **Action**:
  - Check `gh run view <run-id> --log-failed` for hidden errors
  - Verify `wrangler deploy` exit codes
- **Watchdog**: Alerts on stall, not failure — build failures already surface via CI

---

## Escalation

| Severity | Condition | Action |
|----------|-----------|--------|
| **P1** | Production deploy stalled > 30 min, no human gate | Page on-call, cancel + retrigger |
| **P2** | Stalled at human gate > 2 hours | Ping approver, escalate to lead |
| **P3** | Recurrent stalls (> 2/week) | Root cause analysis, fix pipeline |

---

## Verification Checklist (Post-Resolution)
- [ ] Deployment shows `success` in Cloudflare dashboard
- [ ] `gemini-web-bridge` health endpoint returns 200: `https://prod.gemini-web-bridge.workers.dev/health`
- [ ] Tracker issue auto-closed (or manually closed with resolution note)
- [ ] Jira ticket updated with resolution evidence
- [ ] No regression in next scheduled watchdog run

---

## Configuration

### Watchdog Schedule
```yaml
# .github/workflows/cd-watchdog.yml
on:
  schedule:
    - cron: "*/10 * * * *"  # Every 10 minutes
  workflow_dispatch: {}
```

### Stall Threshold
```python
# In watchdog script
STALL_THRESHOLD_MINUTES = 15  # Deployment stuck this long = stall
```

### Tracker Issue Idempotency
- Key: `watchdog-cd-stall-<deployment-id>`
- Only one issue per deployment ID
- Auto-closes when deployment status = `success`

---

## Related Tickets

| Ticket | Description | Status |
|--------|-------------|--------|
| **KAN-173** | Ops watchdog for 51-min 503 alert gap | ✅ Done (watchdog deployed) |
| **KAN-274** | Option A: Stay on Render + Cloudflare D1 outbox | ✅ Approved |
| **KAN-275/276** | HF Static retired (.hf.space removed) | ✅ Done |

---

## Historical Context

**Before KAN-173**: A deployment stalled at the `environment: production` gate for 51 minutes. No alert fired because the workflow was "running" (not failed). The gap was only discovered when a human checked.

**After KAN-173**: 
- Watchdog runs every 10 minutes
- Detects any deployment in `pending`/`queued` > 15 minutes
- Creates loud GitHub Issue + Jira alert
- Auto-closes on resolution
- Zero silent stalls since deployment

---

## Maintenance

### Updating the Watchdog
1. Modify `.github/workflows/cd-watchdog.yml` or the watchdog script
2. Test via `workflow_dispatch`
3. Verify tracker issue creation + auto-close in a staging deploy
4. Update this runbook if detection logic changes

### Adding New Workers
To monitor additional Cloudflare Workers:
1. Add worker name to watchdog config
2. Verify gate structure matches (environment + concurrency)
3. Test detection with a manual stall simulation
4. Add to this runbook's "Components" table