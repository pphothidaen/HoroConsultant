#!/usr/bin/env python3
"""Read-only Jira Cloud JQL query for the sync-jira.yml workflow.

Replaces the Atlassian Teamwork Graph CLI (`twg jira workitem query`) that
sync-jira.yml used to install and invoke. The CLI cannot run in CI:

  * Its installer shells out to `twg consent`, which refuses to record consent
    without a controlling terminal, so the install step exited 1 and every run
    of sync-jira.yml failed before reaching the query.
  * The `TWG_TOKEN` / `TWG_USER` / `TWG_SITE` secrets it read no longer exist
    in this repository.

Auth is Atlassian Cloud basic auth with the email + API token pair already
provisioned as the `JIRA_EMAIL` / `JIRA_API_TOKEN` repo secrets, with the site
taken from `JIRA_BASE_URL`.

This script is deliberately read-only: it runs one JQL search and prints the
results as JSON. It performs no status transitions and no issue writes, so it
is safe for the bidirectional sync workflow to call on both the file->Jira and
the Jira->file direction.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SEARCH_PATH = "/rest/api/3/search/jql"
FIELDS = "summary,status,project,updated"
MAX_RESULTS = 100


def build_request(
    base_url: str, jql: str, email: str, token: str, max_results: int = MAX_RESULTS
) -> urllib.request.Request:
    """Build the basic-auth Jira search request.

    The JQL travels as a query parameter rather than being interpolated into
    the path, so a quote or backslash in the query cannot break out of the URL.
    """
    query = urllib.parse.urlencode(
        {"jql": jql, "fields": FIELDS, "maxResults": max_results}
    )
    url = f"{base_url.rstrip('/')}{SEARCH_PATH}?{query}"
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return urllib.request.Request(
        url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
        },
    )


def search_jira(
    base_url: str, jql: str, email: str, token: str, max_results: int = MAX_RESULTS
) -> list[dict]:
    """Run the search and return the slimmed-down issue list."""
    missing = [
        name
        for name, value in (
            ("JIRA_BASE_URL", base_url),
            ("JIRA_EMAIL", email),
            ("JIRA_API_TOKEN", token),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"missing credentials: {', '.join(missing)}")

    request = build_request(base_url, jql, email, token, max_results)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Jira search failed: HTTP {exc.code}: {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Jira unreachable: {exc.reason}") from exc

    # Emit only the fields the caller reads, so a large or unexpected Jira
    # payload cannot flood the workflow log.
    issues = []
    for issue in payload.get("issues", []):
        fields = issue.get("fields", {})
        issues.append(
            {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": (fields.get("status") or {}).get("name"),
                "updated": fields.get("updated"),
            }
        )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jql", required=True)
    parser.add_argument("--out", help="write JSON here instead of stdout")
    parser.add_argument("--base-url", default=os.environ.get("JIRA_BASE_URL", ""))
    parser.add_argument("--email", default=os.environ.get("JIRA_EMAIL", ""))
    parser.add_argument("--token", default=os.environ.get("JIRA_API_TOKEN", ""))
    parser.add_argument("--max-results", type=int, default=MAX_RESULTS)
    args = parser.parse_args()

    try:
        issues = search_jira(
            args.base_url, args.jql, args.email, args.token, args.max_results
        )
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1

    document = json.dumps({"issues": issues}, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(document + "\n")
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main())