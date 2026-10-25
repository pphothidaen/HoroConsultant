#!/usr/bin/env python3
"""
30-minute scope grill response monitor for KAN-73.
Polls Jira comments on KAN-73. If no response from the ticket owner
(Pansakorn) after 30 minutes since the grill comment was posted,
flags KAN-73 as Blocked (label + comment + attempt workflow transition).
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# --- Config ---
ISSUE_KEY = "KAN-73"
OWNER_DISPLAY_NAME = "Pansakorn (林金龍) Phothidaen"
OWNER_EMAIL = "pansakorn@gmail.com"
POLL_INTERVAL_SEC = 120        # check every 2 minutes
RESPONSE_WINDOW_SEC = 30 * 60  # 30 minutes
COMMENT_POSTED_AT = datetime.now(timezone.utc)  # reference time
GRILL_COMMENT_ID = None  # ID of the grill comment (excluded from response detection)

# --- Load credentials from .env ---
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
import base64
_env = {}
with open(ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if line.startswith("JIRA_BASE_URL="):
            _env["JIRA_BASE_URL"] = line.split("=", 1)[1].strip()
        if line.startswith("JIRA_EMAIL="):
            _env["JIRA_EMAIL"] = line.split("=", 1)[1].strip()
        if line.startswith("JIRA_API_TOKEN="):
            _env["JIRA_API_TOKEN"] = line.split("=", 1)[1].strip()

if not _env.get("JIRA_API_TOKEN"):
    print("FATAL: JIRA_API_TOKEN not found in .env")
    exit(1)

BASE_URL = _env.get("JIRA_BASE_URL", "https://pansakorn.atlassian.net")
# Jira Cloud REST API with API token uses Basic auth: base64(email:token)
_auth_str = f"{_env['JIRA_EMAIL']}:{_env['JIRA_API_TOKEN']}"
_auth_b64 = base64.b64encode(_auth_str.encode("utf-8")).decode("ascii")

HEADERS = {
    "Authorization": f"Basic {_auth_b64}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

JIRA_EMAIL = "pansakorn@gmail.com"


def api_request(method, url, payload=None):
    """Jira REST API request with retry on 429/503."""
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    retries = 0
    max_retries = 4
    while retries <= max_retries:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.getcode()
                raw = resp.read().decode("utf-8")
                print(f"  HTTP {status} {method} {url.replace(BASE_URL, '')}")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code in (429, 503) and retries < max_retries:
                wait = 25 if e.code == 429 else 15
                print(f"  HTTP {e.code} — retrying in {wait}s (attempt {retries+1}/{max_retries})")
                time.sleep(wait)
                retries += 1
                continue
            print(f"  HTTP {e.code}: {body[:300]}")
            return None
        except Exception as e:
            if retries < max_retries:
                print(f"  Error: {e} — retrying (attempt {retries+1}/{max_retries})")
                time.sleep(15)
                retries += 1
                continue
            print(f"  Fatal error: {e}")
            return None
    return None


def get_issue_comments():
    """Fetch all comments on KAN-73, sorted by creation time."""
    url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}/comment?maxResults=100&orderBy=created"
    result = api_request("GET", url)
    if result:
        return result.get("comments", [])
    return []


SCOPE_GRILL_MARKER = "9dim-grill-kan73-scope"
SCOPE_GRILL_KEYWORDS = ["scope grill", "9-dimension", "9 dimension", "9dimension"]


def parse_jira_timestamp(ts_str):
    """Parse Jira timestamp (handles both Z and +0700 / +07:00 formats)."""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    elif len(ts_str) >= 5 and ts_str[-5] in "+-":
        ts_str = ts_str[:-2] + ":" + ts_str[-2:]
    return datetime.fromisoformat(ts_str)


def body_to_str(body):
    """Normalize comment body (str or ADF dict) to a searchable string."""
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        return json.dumps(body)
    return str(body)


SCOPE_GRILL_COMMENT = (
    "## 📋 9-Dimension Scope Grill — KAN-73\n\n"
    "**Parent Epic:** Gemini Bridge Integration — MCP toggle, circuit breaker, CI/CD\n"
    "**Owner:** Pansakorn (林金龍) Phothidaen\n"
    "**Spec:** `docs/gemini-bridge-mcp-toggle.md`\n"
    "**Full intake doc:** `plans/intake/sprint-f-jira-grill.md`\n\n"
    "Please respond within **30 minutes**. If no response, KAN-73 will be flagged as **Blocked**.\n\n"
    "### 1. Requirements\n"
    "- Q: Which specific behaviors must be byte-identical to the legacy HybridRouter chain when the bridge is disabled? (e.g., empty birth_context, malformed JSON, non-Thai queries)\n"
    "- Q: Circuit breaker failover: Gemini Bridge → Cloudflare AI → local model. Is this the exact failover priority, or should Ollama qwen2.5:7b remain first as in the legacy chain (section 6.2 of spec)?\n"
    "- Q: Are there any acceptance criteria beyond the per-ticket checklists? (e.g., minimum pass rate, coverage thresholds)\n\n"
    "### 2. Constraints\n"
    "- Q: KAN-74 RED phase requires 3 test files committed and failing. Must tests be committed to a specific branch or to main?\n"
    "- Q: Are there constraints on test execution time? Do CI integration tests need to complete within a hard deadline (e.g., 180s)?\n"
    "- Q: Can tests run against the production URL (`https://gemini-web-bridge.pansakorn-pho.workers.dev`) directly, or must they use a staging environment?\n\n"
    "### 3. Dependencies\n"
    "- Q: Does KAN-76's provenance manifest depend on the bridge being deployed to a specific version/branch? If so, which?\n"
    "- Q: Are there any pending changes to `project/core/gemini_bridge_client.py` or the spec doc (`docs/gemini-bridge-mcp-toggle.md`) that tests must account for?\n"
    "- Q: Does the CI/CD workflow (KAN-76) depend on downstream systems (Render.com, GitHub Actions runners, Doppler sync) having specific permissions or secrets available?\n\n"
    "### 4. Acceptance Criteria\n"
    "- Q: For KAN-74 GREEN phase — \"All tests pass after implementation.\" Should these tests pass against production, staging, or both? What's the exact verification command?\n"
    "- Q: For KAN-75 — Circuit breaker state machine (closed → open → half-open → closed) — must this be tested via unit tests, integration tests, or both?\n"
    "- Q: For KAN-76 — \"Provenance manifest generated and attached to releases\" — what format? (e.g., SPDX SBOM, in-toto attestation, CycloneDX) And must it be a GitHub release asset, a Render artifact, or a comment on the PR?\n\n"
    "### 5. Edge Cases\n"
    "- Q: Beyond the documented fail-fast HTTP statuses (503/422/429/401/timeout), what edge cases must tests cover? (e.g., HTTP 400 with invalid JSON body, HTTP 500 from Worker, network partition causing `ConnectionError`, SSL/TLS errors)\n"
    "- Q: For PDF mode: what happens if the `pdf_url` artifact expires (TTL 3600s) before the client downloads it? Must this be tested?\n"
    "- Q: What happens when the NotebookLM notebook scope is valid but the notebook is empty or has no relevant knowledge? Is that a bridge-level error or a valid empty response?\n\n"
    "### 6. Integrations\n"
    "- Q: KAN-76 mentions GitHub Actions workflow. Which existing workflow YAML should be extended, or should a new one be created? (e.g., `.github/workflows/integration.yml`)\n"
    "- Q: Does the provenance manifest need to integrate with any existing observability stack (e.g., Sentry, DataDog, custom logging)?\n"
    "- Q: The failover chain includes Ollama, Gemini API, and Cloudflare AI. Are these upstreams already configured in CI/CD, or do tests need to mock them?\n\n"
    "### 7. Security\n"
    "- Q: The spec states Bearer token must never be committed. Do test fixtures use mock tokens or a dedicated test token provisioned in Doppler? How is token rotation handled in test environments?\n"
    "- Q: PDF artifact download uses unguessable-key URLs with no Bearer. Are there any rate-limiting or IP-restriction controls on the `/artifacts/{key}` endpoint that tests must account for?\n"
    "- Q: Does the provenance manifest need to include vulnerability scanning results (e.g., `pip-audit`, `bandit`) as part of CI?\n\n"
    "### 8. Rollback Plan\n"
    "- Q: The runtime toggle (`GEMINI_WEB_BRIDGE_ENABLED`) can be flipped to `false` via Doppler + `scripts/sync-render-secrets.sh`. Is there a documented runbook for operators to execute this rollback?\n"
    "- Q: If KAN-76's CI/CD integration introduces a regression, is there a specific commit/rollback protocol (e.g., revert PR, rollback Render deploy, revert Doppler secret)?\n"
    "- Q: For the circuit breaker specifically — if all failover paths fail, what's the final user-facing behavior? Must tests verify this terminal fallback path?\n\n"
    "### 9. Success Metrics\n"
    "- Q: Beyond test pass/fail, what are the measurable success criteria for this sprint? (e.g., bridge response latency < X seconds, error rate < Y%, query volume routed to bridge > Z%)\n"
    "- Q: How will success be measured in production after toggle is enabled? Are there dashboards or SLOs defined?\n"
    "- Q: Is there a target date for production toggle enablement, and does the 30-min response window here align with the sprint timeline?\n\n"
    "---\n"
    "⏰ **30-minute response window started now.** Automated by BA Intake Scope Grill Monitor.\n"
    f"— {SCOPE_GRILL_MARKER}"
)


def post_scope_grill():
    """Post the 9-dimension scope grill comment to KAN-73."""
    payload = {"body": make_adf_doc(SCOPE_GRILL_COMMENT)}
    url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}/comment"
    return api_request("POST", url, payload)


def make_adf_doc(markdown_text):
    """Convert a markdown-ish string into a minimal Atlassian Document Format (ADF) doc.

    Jira REST API v3 requires comments to be ADF, not a plain string.
    This parser supports paragraphs (blank-line-separated) and
    GFM-style unordered lists (- item / * item).
    """
    doc = {"type": "doc", "version": 1, "content": []}
    paragraphs = markdown_text.split("\n\n")
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Detect a list: every non-empty line starts with "- " or "* "
        lines = para.split("\n")
        is_list = all(l.strip().startswith(("- ", "* ")) or l.strip() == "" for l in lines if l.strip())
        if is_list:
            list_items = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                text = line[2:] if line.startswith(("- ")) or line.startswith("* ") else line
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": text}]
                    }]
                })
            doc["content"].append({"type": "bulletList", "content": list_items})
        else:
            doc["content"].append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para}]
            })
    return doc


def is_grill_comment(body_text):
    """Check if a comment body is a scope grill comment.
    Detects the marker (new posts by this script) and content keywords
    (for grill comments posted by previous runs/versions that lack the marker).
    """
    if SCOPE_GRILL_MARKER in body_text:
        return True
    body_lower = body_text.lower()
    for kw in SCOPE_GRILL_KEYWORDS:
        if kw in body_lower:
            return True
    return False


def find_existing_grill_comment():
    """Check if the scope grill comment was already posted.
    Returns (creation_datetime, comment_id) or (None, None)."""
    comments = get_issue_comments()
    for c in comments:
        body_text = body_to_str(c.get("body", ""))
        if is_grill_comment(body_text):
            created_str = c.get("created", "")
            try:
                dt = parse_jira_timestamp(created_str)
                return (dt, c.get("id"))
            except (ValueError, TypeError):
                pass
    return (None, None)


def add_blocker_comment():
    """Add a comment explaining KAN-73 is now blocked due to no response."""
    text = (
        "⛔ Blocked — No Scope Grill Response (30-min window expired)\n\n"
        f"The 9-dimension scope grill question set was posted on {COMMENT_POSTED_AT.strftime('%Y-%m-%d %H:%M UTC')} "
        "but no response has been received from the ticket owner within the 30-minute window.\n\n"
        "Action taken:\n"
        "- KAN-73 flagged as Blocked (label + comment)\n"
        "- Parent Epic KAN-38 notified\n\n"
        "To unblock: owner must review and respond to the scope questions in the intake doc "
        "(`plans/intake/sprint-f-jira-grill.md`) or directly on this ticket. "
        "Once clarifications are provided, remove the `blocked` label.\n\n"
        "— Automated by BA Intake Scope Grill Monitor"
    )
    payload = {"body": make_adf_doc(text)}
    url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}/comment"
    return api_request("POST", url, payload)


def add_blocked_label():
    """Add 'blocked' label to KAN-73."""
    body = {"update": {"labels": [{"add": "blocked"}]}}
    url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}"
    return api_request("PUT", url, body)


def get_available_transitions():
    """Get available workflow transitions for KAN-73."""
    url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}/transitions"
    result = api_request("GET", url)
    if result:
        return result.get("transitions", [])
    return []


def attempt_blocked_transition(transitions):
    """Try to find and apply a 'Blocked' status transition."""
    for t in transitions:
        tname = (t.get("name", "") + " " + t.get("to", {}).get("name", "")).lower()
        if "blocked" in tname:
            body = {"transition": {"id": t["id"]}}
            url = f"{BASE_URL}/rest/api/3/issue/{ISSUE_KEY}/transitions"
            print(f"  Attempting transition: {t['name']} (id={t['id']})")
            return api_request("POST", url, body)
    print("  No 'Blocked' transition available — applying label + comment only.")
    return None


def main():
    global COMMENT_POSTED_AT, GRILL_COMMENT_ID

    now = datetime.now(timezone.utc)
    print(f"[grill-monitor] Started at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"[grill-monitor] Target issue: {ISSUE_KEY}")
    print(f"[grill-monitor] Owner: {OWNER_DISPLAY_NAME} ({OWNER_EMAIL})")
    print(f"[grill-monitor] Polling every {POLL_INTERVAL_SEC}s for {RESPONSE_WINDOW_SEC // 60} minutes")

    # --- Post scope grill (or detect existing) ---
    existing_time, existing_id = find_existing_grill_comment()
    if existing_time:
        COMMENT_POSTED_AT = existing_time
        GRILL_COMMENT_ID = existing_id
        print(f"[grill-monitor] ✅ Scope grill already posted on KAN-73 at "
              f"{COMMENT_POSTED_AT.strftime('%Y-%m-%d %H:%M:%S UTC')} (comment ID: {GRILL_COMMENT_ID})")
        print(f"[grill-monitor] NOT duplicating grill comment — using existing posting time as reference.")
    else:
        print(f"[grill-monitor] No existing grill comment found. Posting 9-dimension scope grill to {ISSUE_KEY}...")
        result = post_scope_grill()
        if result is not None:
            comment_id = result.get("id", "unknown")
            print(f"[grill-monitor] ✅ Scope grill posted (comment ID: {comment_id})")
            COMMENT_POSTED_AT = datetime.now(timezone.utc)
            GRILL_COMMENT_ID = comment_id
        else:
            print(f"[grill-monitor] ⚠️  Failed to post scope grill (HTTP error or network failure). Starting monitor anyway.")
            COMMENT_POSTED_AT = now

    deadline = COMMENT_POSTED_AT + timedelta(seconds=RESPONSE_WINDOW_SEC)
    print(f"[grill-monitor] Response window ends at {deadline.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    remaining_at_start = (deadline - now).total_seconds()
    if remaining_at_start <= 0:
        print("[grill-monitor] ⛔ 30-minute window already expired before monitoring started. Flagging KAN-73 as Blocked.")
    else:
        while datetime.now(timezone.utc) < deadline:
            comments = get_issue_comments()
            owner_response = False
            for c in comments:
                author = c.get("author", {})
                display_name = author.get("displayName", "")
                email = author.get("emailAddress", "")
                # Exclude any scope grill comments (by content keywords)
                body_text = body_to_str(c.get("body", ""))
                if is_grill_comment(body_text):
                    continue
                if display_name == OWNER_DISPLAY_NAME or email == OWNER_EMAIL:
                    created_str = c.get("created", "")
                    try:
                        created_dt = parse_jira_timestamp(created_str)
                        if created_dt > COMMENT_POSTED_AT:
                            owner_response = True
                            body_preview = body_to_str(c.get("body", ""))[:200]
                            print(f"[grill-monitor] Found owner response: '{body_preview}...' at {created_str}")
                            break
                    except (ValueError, TypeError):
                        pass
            if owner_response:
                print("SCOPE CONFIRMED")
                print("[grill-monitor] ✅ Owner responded within window. No blocking action taken.")
                return

            remaining = deadline - datetime.now(timezone.utc)
            print(f"[grill-monitor] No owner response yet. Remaining: {remaining}. Comments checked: {len(comments)}")
            time.sleep(POLL_INTERVAL_SEC)

    # --- 30-min window expired, no response ---
    print("[grill-monitor] ⛔ 30-minute window expired. No owner response. Flagging KAN-73 as Blocked.")

    # 1. Add 'blocked' label
    add_blocked_label()
    print("[grill-monitor] Added 'blocked' label to KAN-73")

    # 2. Attempt workflow transition to Blocked status
    transitions = get_available_transitions()
    attempt_blocked_transition(transitions)

    # 3. Add explanatory comment
    add_blocker_comment()
    print("[grill-monitor] Added blocker comment to KAN-73")

    print("[grill-monitor] Done. KAN-73 is now blocked. Parent Epic KAN-38 notified.")
    print("BLOCKED")


if __name__ == "__main__":
    main()
