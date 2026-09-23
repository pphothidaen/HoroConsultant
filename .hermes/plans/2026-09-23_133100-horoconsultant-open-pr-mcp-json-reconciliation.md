# HoroConsultant Open-PR Reconciliation & .mcp.json Secret Guard — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Close superseded PRs #68 and #60 with evidence-backed comments, and move the aipass-web-bridge MCP Bearer token out of the tracked (PUBLIC repo) `.mcp.json` into Claude user-scope config, protected by a new fail-closed pytest contract test.

**Architecture:** The two open PRs are stale leftovers whose real fixes already landed on `main` via other paths (PR #65, PR #64, commit `22b362bb`), so they are closed-with-comment rather than merged. The `.mcp.json` worktree change carries a live secret in a file that is git-tracked in a public repository; the server is re-registered in Claude **user scope** (`~/.claude.json`, never committed), the worktree file is restored to HEAD, and a pytest guard freezes the "no literal credentials in tracked .mcp.json" contract following the repo's test-provenance governance (baseline manifest + separate commits).

**Tech Stack:** git, `gh` CLI, pytest, Claude Code MCP config (`claude mcp add-json`), `scripts/test_provenance_guard.py`, `scripts/sync_ai_agent_ecosystem.py`.

---

## Current context / verified facts (evidence gathered 2026-09-23, all read-only)

| # | Fact | Evidence |
|---|------|----------|
| 1 | Repo is `pphothidaen/HoroConsultant`, **PUBLIC**, local branch `pr64-fix`, one modified file: `.mcp.json` | `gh repo view --json visibility`; `git status --porcelain` → ` M .mcp.json` |
| 2 | `.mcp.json` is **git-tracked** (not gitignored) and parsed by the ecosystem sync gate | `git ls-files --error-unmatch .mcp.json` → TRACKED; `scripts/sync_ai_agent_ecosystem.py:488` → `check_json_file(".mcp.json", ...)` |
| 3 | The uncommitted diff adds an `aipass-web-bridge` MCP server with an inline `Authorization: Bearer <46-char token>` — **this is the aipass-web-bridge token, NOT a Vercel token** (corrects the working assumption) | `git diff -- .mcp.json` (token masked during audit) |
| 4 | The token was **never committed to any remote ref or candidate commit** (hash-based scan across all `refs/remotes/*` plus `fab949f9`, `fc4a15af`, `73b39947`, `fcee8d95`, `77c3be52`) → **no rotation required**; the only risk is accidentally committing the current worktree file | `git grep -I -l -F <token> <ref> -- .` returned nothing for every ref |
| 5 | HEAD/`origin/main` `.mcp.json` contains only the `filesystem` server (no secrets) and is byte-identical between `pr64-fix` HEAD and `origin/main` | `git show HEAD:.mcp.json`; `diff` → IDENTICAL |
| 6 | **PR #68** ([KAN-68] flaky COMMAND_LOG race): head commit `fcee8d95` is **EMPTY** (0 files, 0+/0−); the real fix already landed on `main` via **PR #65** (merge `7c1ea9da`, atomic-mock fix `a5449acc`); PR is 45 commits behind main | `gh api .../commits/fcee8d95` → `{"additions":0,"deletions":0,"total":0}`; `gh pr view 68` |
| 7 | **PR #60** ([KAN-69] render.yaml Dockerfile path): `mergeStateStatus: DIRTY` (CONFLICTING), 69 behind / 4 ahead. Its stated fix landed via **PR #64 (MERGED)**; `RENDER_BACKEND_URL` docs landed on main via commit `22b362bb`. Remaining unique content vs main: (a) `tests/env_template_render_origin_contract.test.mjs` — **no CI workflow executes `.mjs` tests**, (b) sync-jira non-interactive consent fix — still absent from main, (c) stale `HANDOFF.md`/`plans/plan.md` edits | `gh pr view 60 --json mergeable,mergeStateStatus`; `gh api .../compare/main...77c3be52`; `git diff origin/main 77c3be52 -- .github/workflows/sync-jira.yml` |
| 8 | Our Vercel work (KAN-84: vercel.json rewrites, outputDirectory, payload reduction) is **already on `main`** via direct pushes — PRs #68/#60 do not need to "receive" it | `git log origin/main --oneline` → `8b684584`, `c3848585`, `0e67b5e5`, `440710e9`, `f24ddb7b`, … |
| 9 | `main` CI is currently RED for a pre-existing, unrelated reason: `project/tests/test_prod_version_regression.py` (5 failures) — the production Vercel deployment now returns a **Vercel SSO login page** instead of the app HTML. There is **no required-check branch protection** (PRs with failing checks show `MERGEABLE`), so this does not block merging, but every new PR will show this red | `gh run view 35813457728 --log-failed` (tail); `gh pr view 68 --json mergeable` |
| 10 | Test-provenance governance (fail-closed): any commit staging a file under `tests/` must also stage a NEW manifest in `plans/test_provenance/` whose `baseline_parent` == current HEAD and whose `test_files[].sha256` matches the staged blob; test and source files must never mix in one commit; PRs with "material" (non-test, non-doc) paths need manifest coverage | `scripts/test_provenance_guard.py` (`verify_staged`, `verify_pr`); `.githooks/pre-commit` |
| 11 | PR titles must start with `[KAN-\d+]` (workflow `jira-governance.yml`, regex-only check — does not verify the ticket exists) | `git show origin/main:.github/workflows/jira-governance.yml` |
| 12 | `pr64-fix` is pushed (`origin/pr64-fix`) and its net diff vs main is only an `ATOMIC_TICKET.md` Sprint-E table addition containing a typo (`|| Sprint |` double pipe that breaks the table header) | `git diff origin/main HEAD -- ATOMIC_TICKET.md` |
| 13 | Claude user-scope `mcpServers` in `~/.claude.json` is currently empty — safe to add there | `python3 -c '...~/.claude.json...'` → `user-scope: []` |

**Hard safety rules for the implementer:**
- **NEVER print, log, or paste the Bearer token value** anywhere (chat, terminal output, commit messages, PR bodies). All verification uses hashes, lengths, or key names only. The guard test is written so pytest's failure output contains field/server names, never the value.
- **NEVER stage or commit the current worktree `.mcp.json`.**
- Pushing branches, opening/closing PRs, and posting PR comments are **external actions requiring explicit user authorization** before execution (per standing delegation policy). Tasks below are marked accordingly.
- Do not run `git commit --amend`/rebase after the baseline commit exists (provenance guard counts manifest add-commits).

---

## Phase 0 — Re-verify evidence at execution time (read-only, ~2 min)

### Task 0.1: Confirm the state has not drifted since 2026-09-23 audit

**Objective:** Guard against stale data before acting.

**Steps:**

```bash
cd /Users/kimlenglim/Project/HoroConsultant
git branch --show-current            # expect: pr64-fix
git status --porcelain               # expect: only " M .mcp.json"
gh pr list --state open --limit 30   # expect: 68 and 60 still OPEN
gh pr view 68 --json state,mergeStateStatus   # expect: OPEN / BEHIND
gh pr view 60 --json state,mergeStateStatus   # expect: OPEN / DIRTY
python3 - <<'PY'
import json, hashlib
tok = json.load(open('.mcp.json'))['mcpServers'].get('aipass-web-bridge',{}).get('headers',{}).get('Authorization','')
print('aipass header present:', bool(tok), '| len:', len(tok), '| sha256[:12]:', hashlib.sha256(tok.encode()).hexdigest()[:12])
PY
# expect: aipass header present: True | len: 53 | sha256[:12]: feff1af8b83a
```

**Expected output:** all values match. If anything differs materially (PRs already closed, token changed, extra dirty files), **STOP and re-confirm with the user** before proceeding.

---

## Phase 1 — .mcp.json secret hygiene (local machine only; no authorization needed)

**CRITICAL ORDERING:** the RED test run in Task 1.3 *requires* the dirty `.mcp.json` still holding the token. Do **not** restore `.mcp.json` (Task 1.4) until the RED evidence is captured.

### Task 1.1: Register aipass-web-bridge in Claude user scope (before touching the repo file)

**Objective:** Preserve the working MCP config outside the tracked file so restoring `.mcp.json` loses nothing.

**Steps:**

```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 - <<'PY'
import json, subprocess
cfg = json.load(open('.mcp.json'))['mcpServers']['aipass-web-bridge']
payload = json.dumps({"type": "http", "url": cfg['url'], "headers": cfg['headers']})
r = subprocess.run(['claude', 'mcp', 'add-json', 'aipass-web-bridge', payload, '-s', 'user'],
                   capture_output=True, text=True)
print((r.stdout or r.stderr).strip())
print('exit:', r.returncode)
PY
```

**Expected output:** a success line from `claude mcp add-json` and `exit: 0` (token stays inside the captured subprocess — never on screen).

**Fallback** (if `add-json` rejects the payload shape): edit `~/.claude.json` directly with a backup:

```bash
python3 - <<'PY'
import json, shutil, pathlib
src = json.load(open('.mcp.json'))['mcpServers']['aipass-web-bridge']
p = pathlib.Path.home() / '.claude.json'
bak = p.with_name('.claude.json.bak-mcp-guard')
if not bak.exists():
    shutil.copy2(p, bak)
data = json.loads(p.read_text())
data.setdefault('mcpServers', {})['aipass-web-bridge'] = {
    "type": "http", "url": src['url'], "headers": src['headers']}
p.write_text(json.dumps(data, indent=2))
print('registered; backup at', bak)
PY
```

**Verify:**

```bash
claude mcp list    # expect: aipass-web-bridge listed (user scope)
python3 -c 'import json,pathlib; d=json.loads((pathlib.Path.home()/".claude.json").read_text()); print("aipass-web-bridge" in d.get("mcpServers",{}))'
# expect: True
```

### Task 1.2: Create a clean branch off origin/main (dirty .mcp.json carries over)

**Objective:** Isolate the guard-test work from `pr64-fix` (whose unique ATOMIC_TICKET.md content stays safely on `origin/pr64-fix`).

**Steps:**

```bash
cd /Users/kimlenglim/Project/HoroConsultant
git fetch origin
git checkout -b test/mcp-json-secret-guard origin/main
git status --porcelain   # expect: still " M .mcp.json" (file identical between branches, so it carries over)
git rev-parse HEAD       # note this SHA — it is <BASELINE_PARENT_SHA>; expect 8b684584... (current origin/main)
```

**Expected output:** branch created, `.mcp.json` still modified. (If git refuses because of the dirty file, that means `.mcp.json` differs between branches — STOP, re-audit.)

### Task 1.3: Write the guard test — RED

**Objective:** Freeze the contract "tracked `.mcp.json` must not contain literal credentials" with a failing run against the current dirty state.

**Files:**
- Create: `tests/test_mcp_json_secret_contract.py`

**Step 1 — create the test file with exactly this content:**

```python
"""Fail-closed secret guard for the tracked .mcp.json MCP config.

.mcp.json is committed to a PUBLIC repository, so it must never contain
literal credentials. MCP authentication belongs in user-scope config
(~/.claude.json) or ${VAR} environment references.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = ROOT / ".mcp.json"

ENV_REFERENCE = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")
CREDENTIAL_PATTERNS = (
    ("bearer-token", re.compile(r"^Bearer\s+\S{20,}$", re.IGNORECASE)),
    (
        "known-key-prefix",
        re.compile(
            r"\b(?:ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
            r"|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}"
            r"|xox[bp]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}"
            r"|hf_[A-Za-z0-9]{20,})"
        ),
    ),
    ("long-base64-blob", re.compile(r"^[A-Za-z0-9+/_=-]{40,}$")),
    ("long-hex-blob", re.compile(r"^[a-f0-9]{32,}$")),
)


def _mcp_servers() -> dict:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    servers = data.get("mcpServers")
    assert isinstance(servers, dict), "mcpServers must be a JSON object"
    return servers


def test_mcp_json_parses_with_mcp_servers_object() -> None:
    servers = _mcp_servers()
    assert isinstance(servers, dict)


def test_tracked_mcp_json_has_no_literal_credentials() -> None:
    violations: list[str] = []
    for server_name, config in _mcp_servers().items():
        credential_fields: dict[str, str] = {}
        credential_fields.update(config.get("headers") or {})
        env = config.get("env") or {}
        if isinstance(env, dict):
            credential_fields.update(env)
        for field_name, value in credential_fields.items():
            if not isinstance(value, str):
                continue
            if ENV_REFERENCE.match(value):
                continue
            for label, pattern in CREDENTIAL_PATTERNS:
                if pattern.search(value):
                    violations.append(
                        f"server {server_name!r} field {field_name!r} matches {label}"
                    )
                    break
    assert not violations, (
        "literal credential suspected in tracked .mcp.json "
        f"({'; '.join(violations)}); use ${{VAR}} env references or "
        "user-scope MCP config instead of committing secrets"
    )
```

Note: the assertion is built from a `violations` list containing only server/field names — pytest's failure output can never leak the token value.

**Step 2 — run RED:**

```bash
python3 -m pytest tests/test_mcp_json_secret_contract.py -v
```

**Expected output:** `1 failed, 1 passed` — `test_tracked_mcp_json_has_no_literal_credentials` FAILS with a message like:

```
AssertionError: literal credential suspected in tracked .mcp.json
(server 'aipass-web-bridge' field 'Authorization' matches bearer-token);
use ${VAR} env references or user-scope MCP config instead of committing secrets
```

**Step 3 — capture the RED evidence** (needed for the provenance manifest):

```bash
python3 -m pytest tests/test_mcp_json_secret_contract.py -v > /tmp/mcp-guard-red.log 2>&1; echo "exit=$?"
# expect: exit=1
grep -m1 "AssertionError" /tmp/mcp-guard-red.log
# copy this exact line — it becomes red_tests[0].failure_fingerprint
```

### Task 1.4: Restore .mcp.json to HEAD (GREEN part A)

**Objective:** Remove the secret from the worktree now that it lives in user scope.

```bash
cd /Users/kimlenglim/Project/HoroConsultant
git restore .mcp.json
git status --porcelain    # expect: only "?? tests/test_mcp_json_secret_contract.py" (untracked new test)
git diff -- .mcp.json     # expect: empty output
```

### Task 1.5: GREEN verify

```bash
python3 -m pytest tests/test_mcp_json_secret_contract.py -v
# expect: 2 passed
python3 scripts/sync_ai_agent_ecosystem.py --check 2>&1 | grep -F '.mcp.json'
# expect line: "[OK] .mcp.json: .mcp.json parses"
```

Note: the full `--check` may exit non-zero from workstation-local gates (e.g. Codex multi-account policy) — that is pre-existing and out of scope; only the `.mcp.json` line must be `[OK]`. CI marks that gate not-applicable.

### Task 1.6: Write the test-provenance manifest

**Objective:** Satisfy the fail-closed provenance guard for the new test file.

**Files:**
- Create: `plans/test_provenance/ticket-mcp-json-secret-guard-001.json`

**Step 1 — collect the two values to embed:**

```bash
shasum -a 256 tests/test_mcp_json_secret_contract.py | awk '{print $1}'   # <TEST_SHA256>
git rev-parse HEAD                                                        # <BASELINE_PARENT_SHA> (= origin/main SHA, from Task 1.2)
```

**Step 2 — create the manifest** (substitute the two values and the RED fingerprint line from Task 1.3):

```json
{
  "schema_version": "test-provenance-v1",
  "ticket_id": "TICKET-MCP-JSON-SECRET-GUARD-001",
  "sequence": 1,
  "provenance_status": "VERIFIED",
  "baseline_parent": "<BASELINE_PARENT_SHA>",
  "test_files": [
    {
      "path": "tests/test_mcp_json_secret_contract.py",
      "sha256": "<TEST_SHA256>"
    }
  ],
  "red_tests": [
    {
      "command": ["python3", "-m", "pytest", "tests/test_mcp_json_secret_contract.py", "-v"],
      "expected_exit": 1,
      "failure_fingerprint": "<paste the exact AssertionError line from /tmp/mcp-guard-red.log>"
    }
  ],
  "allowed_source_paths": [".mcp.json"],
  "test_owner_role": "qa_tester",
  "reviewer_role": "ba_auditor",
  "supersedes": null,
  "correction_reason": null,
  "rationale": "Contract test freezes the tracked public .mcp.json so literal credentials (Bearer tokens, API keys) can never be committed; MCP auth belongs in user-scope config or ${VAR} env references."
}
```

**Important:** the test file is now FROZEN — if you edit it after this point, the sha256 breaks and the guard fails. Finalize the test before writing the manifest.

### Task 1.7: Baseline commit (test + manifest together, nothing else)

```bash
cd /Users/kimlenglim/Project/HoroConsultant
git add tests/test_mcp_json_secret_contract.py plans/test_provenance/ticket-mcp-json-secret-guard-001.json
git commit -m "test: freeze .mcp.json secret guard contract (TICKET-MCP-JSON-SECRET-GUARD-001)

RED: pytest tests/test_mcp_json_secret_contract.py -v failed against the
local worktree .mcp.json containing a literal aipass-web-bridge Bearer
token (verified never committed to any remote ref; registered in Claude
user scope instead).
GREEN: after git restore .mcp.json, 2 passed."
```

The pre-commit hook (`.githooks/pre-commit`) runs `scripts/test_provenance_guard.py staged` — expect it to pass (manifest present, `baseline_parent` == HEAD, hashes match), plus the notebook-syntax pytest gate.

**Expected output:** commit succeeds; `git log --oneline -1` shows the new commit; `git status --porcelain` is empty.

### Task 1.8: Local provenance verification (simulates the CI check)

```bash
python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD
```

**Expected output:** JSON with `"status": "PASSED"`, `"test_files_verified": 1`, `"issues": []`.

---

## Phase 2 — Close PR #68 (EXTERNAL ACTION — requires user authorization)

### Task 2.1: Close as superseded with an evidence comment

```bash
cd /Users/kimlenglim/Project/HoroConsultant
gh pr close 68 --comment "Closing as superseded: the COMMAND_LOG race fix already landed on main via #65 (merge 7c1ea9da; atomic mock fix a5449acc, docs 24d3e64a). This PR's head commit fcee8d95 is empty (0 files changed) and the branch is 45 commits behind main. KAN-68 is DONE per the Sprint E registry."
gh pr view 68 --json state   # expect: "state": "CLOSED"
```

**Optional (ask user):** delete the remote branch — `git push origin --delete feat/KAN-68-fix-command-log-race` (safe: its only commit is empty).

---

## Phase 3 — Close PR #60 (EXTERNAL ACTION — requires user authorization)

### Task 3.1: Close as superseded with an evidence comment

```bash
cd /Users/kimlenglim/Project/HoroConsultant
gh pr close 60 --comment "Closing as superseded: the render.yaml Dockerfile path fix landed via #64 (merged), and RENDER_BACKEND_URL documentation landed on main via commit 22b362bb. The branch is CONFLICTING (69 commits behind main). Remaining unique content is intentionally NOT salvaged here: the .env.example origins contract test is a .mjs file that no CI workflow executes, and the sync-jira non-interactive consent fix will be re-landed as a separate clean PR. KAN-69 is DONE per the Sprint E registry."
gh pr view 60 --json state   # expect: "state": "CLOSED"
```

**Optional (ask user):** delete the remote branch — `git push origin --delete chore/sync-main-retrigger-deploy`.

---

## Phase 4 — Land the guard test via PR (EXTERNAL ACTIONS — require user authorization)

### Task 4.1: Push the branch

```bash
git push -u origin test/mcp-json-secret-guard
# expect: branch created on origin
```

### Task 4.2: Open the PR

**Before creating:** confirm the next free KAN number with the user (Sprint E registry ends at KAN-72; suggest KAN-73).

```bash
gh pr create \
  --title "[KAN-73] test: freeze .mcp.json secret guard contract" \
  --body "## Summary
- Adds \`tests/test_mcp_json_secret_contract.py\`: fail-closed guard asserting the tracked, public \`.mcp.json\` never contains literal credentials (Bearer tokens, known key prefixes, long base64/hex blobs). \${VAR} env references remain allowed.
- Adds provenance manifest \`plans/test_provenance/ticket-mcp-json-secret-guard-001.json\` (TICKET-MCP-JSON-SECRET-GUARD-001, RED→GREEN).
- Context: a local worktree edit had added an aipass-web-bridge server with an inline Bearer token to \`.mcp.json\`. A hash-based scan verified the token was NEVER committed to any remote ref (no rotation needed). The server is now registered in Claude user scope (\`~/.claude.json\`), and the tracked file is unchanged by this PR.

## Test Plan
- [x] RED: \`python3 -m pytest tests/test_mcp_json_secret_contract.py -v\` → 1 failed (bearer-token in server 'aipass-web-bridge' field 'Authorization') against the dirty worktree
- [x] GREEN: after \`git restore .mcp.json\` → 2 passed
- [x] \`python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD\` → PASSED, test_files_verified=1
- [x] \`python3 scripts/sync_ai_agent_ecosystem.py --check\` → \`[OK] .mcp.json: .mcp.json parses\`

## Known pre-existing CI red (NOT caused by this PR)
\`PyTest & Edge Boundary Testing\` fails on main itself (run 35813457728): \`project/tests/test_prod_version_regression.py\` (5 failures) because the production Vercel deployment now returns a Vercel SSO login page instead of the app. Tracked separately; no required-check branch protection is affected."
```

**Expected output:** PR URL returned; `gh pr view --json state` → OPEN.

### Task 4.3: Monitor checks and report (merge decision belongs to the user)

```bash
gh pr checks --watch   # or: gh pr checks
```

**Expected outcomes:**
- `Test Provenance` → **pass** (manifest verified)
- `Validate Jira Issue Key Prefix` → **pass** (title matches `[KAN-73] ...`)
- `Code Quality & Security Audit`, `Rust PyO3 ...`, `Validate cross-platform agent sync` → pass (as on recent PRs)
- `PyTest & Edge Boundary Testing` → **fail (pre-existing main red — Vercel SSO wall, see PR body)** — expected, do not chase in this PR
- `Vercel` / `Workers Builds` preview checks → may show fail/canceled (as on PRs #60/#68); informational only

Report the check matrix to the user and **ask** whether to merge (e.g. `gh pr merge --squash --delete-branch`).

---

## Phase 5 — Deferred follow-ups (separate tickets; do NOT bundle here)

1. **pr64-fix branch**: fix the `|| Sprint |` double-pipe typo in `ATOMIC_TICKET.md` (line ~50, introduced by `20aec9d1`) and open a `[KAN-67]` PR for the Sprint E registry rows (KAN-68..72). Content is preserved on `origin/pr64-fix`; nothing is lost by waiting.
2. **sync-jira consent fix** (salvage from PR #60): apply this exact diff to `.github/workflows/sync-jira.yml` in both jobs' "Install Teamwork Graph CLI" steps (verified against `git diff origin/main 77c3be52`):
   ```diff
          curl -fsSL https://teamwork-graph.atlassian.com/cli/install | TWG_BIN_DIR="$HOME/.local/bin" bash -s -- --yes
   +      export TWG_CONSENT=1
   +      twg consent --source direct-public-installer --agree || true
          echo "$HOME/.local/bin" >> $GITHUB_PATH
   ```
   (`.github/workflows/` is a docs-only path for the provenance guard — no manifest needed. Needs its own KAN key.)
3. **Vercel SSO incident**: `project/tests/test_prod_version_regression.py` red on main because the production deployment (`horo-consultant-4asht1tqs...vercel.app`) sits behind Vercel SSO. Decide: disable Vercel Authentication for that deployment, or point the regression suite at a public alias. This blocks "all-green" CI on every PR until fixed.
4. **Scheduled workflow failures on main** (`Orchestrator Dispatch`, `Production Synthetic Monitoring`) — audit separately.

---

## Tests / validation summary

| Task | Command | Expected |
|------|---------|----------|
| 0.1 | `git status --porcelain` | only ` M .mcp.json` |
| 1.1 | `claude mcp list` | aipass-web-bridge (user scope) |
| 1.3 | `python3 -m pytest tests/test_mcp_json_secret_contract.py -v` | **1 failed**, 1 passed (RED) |
| 1.4 | `git diff -- .mcp.json` | empty |
| 1.5 | same pytest | **2 passed** (GREEN) |
| 1.5 | `sync_ai_agent_ecosystem.py --check \| grep .mcp.json` | `[OK] .mcp.json: .mcp.json parses` |
| 1.7 | commit with hook | provenance staged gate passes |
| 1.8 | `test_provenance_guard.py verify-pr --base origin/main --head HEAD` | `"status": "PASSED"`, `test_files_verified: 1` |
| 2.1 | `gh pr view 68 --json state` | CLOSED |
| 3.1 | `gh pr view 60 --json state` | CLOSED |
| 4.3 | `gh pr checks` | matrix as documented above |

## Risks, tradeoffs, and open questions

- **Token handling**: the token stays out of the repo but lives in plaintext in `~/.claude.json` (same local trust domain as before). A Doppler-managed `${AIPASS_WEB_BRIDGE_TOKEN}` env-ref inside `.mcp.json` would be repo-shareable, but relies on Claude Code's env expansion in headers and shell-level env injection — heavier; YAGNI unless the user wants the server shared across machines via the repo (open question).
- **Guard scope**: the new test covers only `.mcp.json`. Repo-wide secret scanning (gitleaks) is a separate hardening ticket — not bundled (YAGNI, minimal blast radius).
- **Pre-existing CI red**: every PR will show the PyTest prod-version failures until the Vercel SSO incident (Phase 5.3) is fixed. The PR body pre-documents this so reviewers don't misattribute it.
- **KAN numbering**: `[KAN-73]` is a suggestion — confirm with the user before opening the PR (governance workflow only validates the pattern, not existence).
- **No required checks**: failing checks do not block merges; do not treat a red X as a gate — verify semantics per check name.
- **Ordering hazard**: if `.mcp.json` is restored before the RED run, the RED evidence cannot be reproduced; the manifest fingerprint would then be fabricated — never do that. If RED cannot be reproduced, STOP and report.
- **PR #60 salvage**: the `.mjs` origins contract test is intentionally dropped (nothing in CI executes `.mjs`); if the team wants it, re-land it as a pytest test under its own ticket.
