#!/usr/bin/env python3
"""Auto-create a Jira issue when a Team Red / Team Blue check fails.

Run by the `if: failure()` step in .github/workflows/post-deploy-tdd.yml.

Jira connection details are read ONLY from the runner environment
(JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY). They are
never required by this workflow file itself (no secrets block), so when the
environment is absent the call degrades gracefully and prints an ASCII notice
instead of raising. The surrounding workflow's explicit "Fail job" step still
marks the run failed, so governance signaling is preserved even without Jira
credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
EMAIL = os.environ.get("JIRA_USER_EMAIL", os.environ.get("JIRA_EMAIL", ""))
TOKEN = os.environ.get("JIRA_API_TOKEN", "")
PROJECT = os.environ.get("JIRA_PROJECT_KEY", "KAN")
TIMEOUT_SECONDS = 20


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, str]:
    if not BASE_URL or not TOKEN:
        return 0, ""
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("ascii") if payload is not None else b""
    req = urllib.request.Request(url, data=data or None, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("Authorization", "Basic " + _basic(EMAIL, TOKEN))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.status, resp.read().decode("ascii", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("ascii", errors="replace")
    except (urllib.error.URLError, OSError):
        return 0, ""


def _basic(email: str, token: str) -> str:
    import base64

    raw = f"{email}:{token}".encode("ascii")
    return base64.b64encode(raw).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-create a Jira issue on post-deploy TDD failure.")
    parser.add_argument("--team", required=True, choices=["teamred", "teamblue"],
                        help="Which team job failed.")
    parser.add_argument("--summary", default="Post-deploy TDD failure",
                        help="Jira issue summary.")
    args = parser.parse_args()

    print("=== Auto-create Jira Issue (on failure) ===")
    print(f"Team: {args.team}")

    if not BASE_URL or not TOKEN:
        print("NOTICE: JIRA_BASE_URL / JIRA_API_TOKEN not set in environment.")
        print("No Jira issue created. The workflow Fail step still records failure.")
        return 0

    description = {
        "type": "doc",
        "version": {"number": 1},
        "body": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "value": f"Post-deploy TDD job '{args.team}' failed in workflow "
                                 f"{os.environ.get('GITHUB_WORKFLOW', 'post-deploy-tdd')}.",
                    }
                ],
            }
        ],
    }

    payload = {
        "fields": {
            "project": {"key": PROJECT},
            "issuetype": {"name": "Bug"},
            "summary": f"[post-deploy-tdd] {args.team} failure: {args.summary}",
            "description": description,
            "labels": ["post-deploy-tdd", args.team, "auto-created"],
        }
    }

    status, body = _request("POST", "/rest/api/3/issue", payload)
    if status in (200, 201):
        key = ""
        try:
            key = json.loads(body).get("key", "")
        except json.JSONDecodeError:
            pass
        print(f"Jira issue created: {key}")
        return 0

    print(f"NOTICE: Jira issue creation failed (HTTP {status}).")
    print("The workflow Fail step still records failure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
