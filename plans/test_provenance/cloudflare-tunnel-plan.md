# Plan: Cloudflare Tunnel Migration (Local → Cloudflare) with .env Secrets

Plan ID: cloudflare-migrate-20260903
Workspace: /Users/kimlenglim/Project/HoroConsultant
Plan saved: /Users/kimlenglim/Project/codexPivot/.hermes/plans/2026-09-03_000000-cloudflare-tunnel-migrate.md

---

## Goal
Move the existing local `cloudflared tunnel --url http://127.0.0.1:48765` (current work from `codexPivot`) to a managed Cloudflare Tunnel using `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_AI_TOKEN` read from `.env`, without breaking existing Vercel/HF backend paths.

## Current context / assumptions
- `codexPivot/` workspace at `/Users/kimlenglim/Project/codexPivot`
- Existing `.env` at repo root (`/Users/kimlenglim/Project/HoroConsultant/.env`) — contains `HF_TOKEN`, `VERCEL_STATIC_URL`, etc. Must also contain `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AI_TOKEN` (or add them).
- Existing tunnel process: PID 51746 (`cloudflared tunnel --url http://127.0.0.1:48765 --no-autoupdate`) — runs locally only.
- Existing build: `~/codex-with-chatgpt` built (`dist/cli/index.js`), skill at `~/.codex/skills/codex-with-chatgpt/`, ChatGPT Connector `Codex Native2` configured.
- No `cloudflared` config file (`~/.cloudflared/config.yml`) exists yet.
- Target: named tunnel under Cloudflare account (not Quick Tunnel) so URL is stable for ChatGPT Connector.

## Architecture / proposed approach
Instead of `cloudflared tunnel --url` (Quick Tunnel, ephemeral URL), create a named tunnel via `cloudflared tunnel --name codex-pivot --url http://localhost:48765` using credentials from `.env`. Update `.env` with `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AI_TOKEN`; add `CLOUDFLARE_TUNNEL_NAME=codex-pivot`; update ChatGPT Connector URL to the new stable tunnel URL; commit only the `.env.example` changes (never real tokens) and the tunnel config.

---

## Step-by-step tasks (bite-sized)

### Task 1: Verify `.env` secrets exist (2 min)
File: `/Users/kimlenglim/Project/HoroConsultant/.env`
Command:
```bash
grep -E "CLOUDFLARE_ACCOUNT_ID|CLOUDFLARE_AI_TOKEN" /Users/kimlenglim/Project/HoroConsultant/.env
```
Expected output: lines with the values. If missing, add to `.env` (not `.env.example`):
```bash
echo 'CLOUDFLARE_ACCOUNT_ID=your-account-id' >> /Users/kimlenglim/Project/HoroConsultant/.env
echo 'CLOUDFLARE_AI_TOKEN=your-token' >> /Users/kimlenglim/Project/HoroConsultant/.env
echo 'CLOUDFLARE_TUNNEL_NAME=codex-pivot' >> /Users/kimlenglim/Project/HoroConsultant/.env
```
Verification: `grep CLOUDFLARE /Users/kimlenglim/Project/HoroConsultant/.env` → 3 lines.

### Task 2: Stop existing local tunnel (2 min)
Command:
```bash
kill $(pgrep -f "cloudflared tunnel --url http://127.0.0.1:48765") 2>/dev/null || echo "already stopped"
```
Expected: process stops; verify `pgrep -f cloudflared` → nothing.

### Task 3: Login / configure cloudflared with account token (5 min)
File to create: `/Users/kimlenglim/.cloudflared/config.yml` (local only, do not commit)
Commands:
```bash
export CLOUDFLARE_ACCOUNT_ID=$(grep CLOUDFLARE_ACCOUNT_ID /Users/kimlenglim/Project/HoroConsultant/.env | cut -d= -f2)
export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_AI_TOKEN /Users/kimlenglim/Project/HoroConsultant/.env | cut -d= -f2)
cloudflared tunnel --name codex-pivot --url http://localhost:48765 --token "$CLOUDFLARE_API_TOKEN"
```
Note: `CLOUDFLARE_AI_TOKEN` is used as the tunnel auth token; if `cloudflared` requires `CLOUDFLARE_API_TOKEN` format, use that name instead.
Expected: tunnel created; output includes `https://codex-pivot.<acc>.trycloudflare.com` or similar.
Verification: `cloudflared tunnel info codex-pivot` → shows active tunnel.

### Task 4: Start named tunnel (2 min)
Command:
```bash
nohup cloudflared tunnel run codex-pivot > /tmp/cloudflare-tunnel.log 2>&1 &
sleep 2
cat /tmp/cloudflare-tunnel.log | tail -3
```
Expected: log shows `INF` / tunnel running / URL assigned.
Verification: `pgrep -f "cloudflared tunnel run codex-pivot"` → PID exists; `curl -I https://codex-pivot.<acc>.trycloudflare.com` → 200/404 (endpoint exists).

### Task 5: Update ChatGPT Connector (2 min — manual step, documented)
Location: https://chatgpt.com → Settings → Developer Mode → Custom Connector `Codex Native2`
Update URL from old Quick Tunnel to new named tunnel URL (from `cloudflared tunnel info`).
No file edit needed; document in `.hermes/plans/` or `IDEA.md` update.
Verification: Connector shows `Connected`; test prompt via ChatGPT Web.

### Task 6: Update `.env.example` (2 min — commit-safe)
File: `/Users/kimlenglim/Project/HoroConsultant/.env.example`
Add:
```bash
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_AI_TOKEN=your_cloudflare_token_here
CLOUDFLARE_TUNNEL_NAME=codex-pivot
```
Verification: `grep -E "CLOUDFLARE" /Users/kimlenglim/Project/HoroConsultant/.env.example` → 3 lines.

### Task 7: Commit changes (2 min)
Only commit:
- `.env.example` updates
- `.hermes/plans/2026-09-03_000000-cloudflare-tunnel-migrate.md`
- Any new `cloudflared/config.yml` only if it contains no secrets (use `CLOUDFLARE_ACCOUNT_ID` as reference, never token)
Never commit `.env`, `~/.cloudflared/config.yml`, or `HF_TOKEN`.
Commands:
```bash
git add .env.example .hermes/plans/2026-09-03_000000-cloudflare-tunnel-migrate.md
git commit -m "docs: add Cloudflare tunnel migration plan and .env.example"
```
Verification: `git diff --cached --name-only` → excludes `.env`, `config.yml`.

---

## Tests / validation (TDD per task)

Task 1 (verify): Write failing check before edit:
```bash
grep CLOUDFLARE_ACCOUNT_ID /Users/kimlenglim/Project/HoroConsultant/.env || echo "FAIL: missing"
```
Run → expect FAIL → add to `.env` → run → expect PASS.

Task 3 (create tunnel): Write test before run:
```bash
cloudflared tunnel info codex-pivot 2>/dev/null || echo "FAIL: tunnel not created"
```
Run → expect FAIL → run create → expect PASS.

Task 4 (start): Before start, test tunnel down:
```bash
pgrep -f "cloudflared tunnel run" || echo "FAIL: not running"
```
Run start → test → PASS.

---

## Risks, tradeoffs, open questions

- **Risk: `CLOUDFLARE_AI_TOKEN` format** — `cloudflared` may expect `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_TUNNEL_TOKEN`; verify with `cloudflared --help` before task 3. Open question: which env var name does the installed `cloudflared` (v2024+) accept?
- **Risk: Quick Tunnel vs Named Tunnel URL** — Existing ChatGPT Connector points to Quick Tunnel; named tunnel URL will differ. Must update Connector (manual step 5) or Connector breaks.
- **Tradeoff: Named tunnel is stable** but requires Cloudflare account; Quick Tunnel is ephemeral but needs no auth. User explicitly wants named tunnel via `.env`.
- **Risk: `.env` secrets in repo** — Pre-commit rules (`test_provenance`) block test-file commits; `.env` is already `.gitignored` (verify: `grep ".env" .gitignore`). If `.env` not ignored, add `echo ".env" >> .gitignore` first.
- **Open Q: Is `CLOUDFLARE_ACCOUNT_ID` the same format as `CLOUDFLARE_API_TOKEN`?** Need user to confirm token type (API token vs Tunnel token) before task 3.

---

## Deliverable
Plan file saved: `/Users/kimlenglim/Project/codexPivot/.hermes/plans/2026-09-03_000000-cloudflare-tunnel-migrate.md`
Ready to execute via subagent if user confirms.
