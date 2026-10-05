#!/usr/bin/env python3
"""Query Jira Cloud issues over the REST v3 search endpoint.

Replaces the Teamwork Graph CLI in orchestrator-dispatch. Two reasons the CLI
cannot run in CI:

  * Its OAuth scopes (`:twg-cli`, `:twg`) are not grantable through the
    Atlassian developer console, so no token it accepts can be provisioned.
  * `twg login` is an interactive OAuth device flow requiring a browser; a
    GitHub runner has none.

`read:jira-work` covers this read-only JQL search, which is all the poller
needs.

Auth is the Atlassian 3LO bearer token produced by
scripts/refresh_twg_token.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SEARCH_PATH = "/rest/api/3/search/jql"
FIELDS = "summary,status,project"
MAX_RESULTS = 50


def build_request(
    base_url: str, jql: str, token: str, max_results: int = MAX_RESULTS
) -> urllib.request.Request:
    """Build the Jira search request.

    The JQL is passed as a query parameter rather than interpolated into the
    path: Atlassian's search endpoint accepts GET with `jql`, and building it
    this way means a quote or backslash in the query cannot break out of the
    URL.
    """
    query = urllib.parse.urlencode(
        {
            "jql": jql,
            "fields": FIELDS,
            "maxResults": max_results,
        }
    )
    url = f"{base_url.rstrip('/')}{SEARCH_PATH}?{query}"
    return urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )


def search_jira(
    base_url: str,
    jql: str,
    token: str,
    max_results: int = MAX_RESULTS,
) -> dict:
    """Run the search and return the decoded payload."""
    if not token:
        raise RuntimeError("no access token: token refresh did not produce one")
    request = build_request(base_url, jql, token, max_results)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Jira search failed: HTTP {exc.code}: {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Jira unreachable: {exc.reason}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jql", required=True)
    parser.add_argument(
        "--base-url", default=os.environ.get("JIRA_BASE_URL", "")
    )
    parser.add_argument(
        "--token", default=os.environ.get("JIRA_ACCESS_TOKEN", "")
    )
    parser.add_argument("--max-results", type=int, default=MAX_RESULTS)
    args = parser.parse_args()

    if not args.base_url:
        print("::error::JIRA_BASE_URL is not set")
        return 1

    try:
        payload = search_jira(
            args.base_url, args.jql, args.token, args.max_results
        )
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1

    # Emit only the fields the caller reads, so a large or unexpected Jira
    # payload cannot flood the workflow log.
    issues = [
        {
            "key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "status": issue.get("fields", {}).get("status", {}).get("name"),
        }
        for issue in payload.get("issues", [])
    ]
    json.dump({"issues": issues}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())