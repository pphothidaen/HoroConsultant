#!/usr/bin/env python3
"""Admit production only from complete, trusted GitHub Actions evidence."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

REQUIRED_WORKFLOWS = (
    "ci.yml", "lint.yml", "ai_agent_ecosystem_sync.yml",
    "test_provenance.yml", "ai_cicd.yml",
)
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class GateError(RuntimeError):
    """Sanitized release denial; never includes transport bodies or credentials."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GateError("GitHub API redirect rejected")


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GateError("GitHub API JSON contains duplicate members")
        result[key] = value
    return result


def _reject_constant(_value):
    raise GateError("GitHub API JSON contains nonfinite values")


def _request_json(url, token):
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "HoroConsultant-release-ci-gate",
    })
    with build_opener(_NoRedirect()).open(request, timeout=30) as response:
        if response.status != 200:
            raise GateError("GitHub API response was not successful")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise GateError("GitHub API response exceeds the evidence limit")
        payload = json.loads(raw, object_pairs_hook=_json_pairs, parse_constant=_reject_constant)
        return payload, dict(response.headers.items())


def _object(value):
    if not isinstance(value, Mapping):
        raise GateError("GitHub API evidence has invalid object shape")
    return value


def _integer(value, *, minimum=1):
    if type(value) is not int or value < minimum:
        raise GateError("GitHub API evidence has invalid numeric identity")
    return value


def verify_release(repository, source_sha, token, *, request_json=None):
    """Require all five latest push runs on the selected current main commit.

    REST workflow file lookup establishes the numeric workflow identity. Runs
    are filtered by SHA, branch and event, then independently validated rather
    than trusting those filters. Incomplete pagination is a denial, not a
    reason to accept an older green result. Re-running the release after all
    checks finish is safe; this verifier never starts or re-runs workflows.
    """
    if (
        not isinstance(repository, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_][A-Za-z0-9_.-]*", repository) is None
        or not isinstance(source_sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_sha) is None
        or not isinstance(token, str)
        or not token.strip()
        or any(ord(char) < 33 or ord(char) > 126 for char in token)
    ):
        raise GateError("Release repository, source SHA or token is invalid")
    transport = request_json or _request_json
    base = f"https://api.github.com/repos/{repository}"

    def fetch(path):
        try:
            payload, headers = transport(f"{base}/{path}", token)
        except Exception:
            # An HTTP exception can contain credentials or a response body.
            raise GateError("GitHub API request failed; release denied") from None
        _object(payload)
        _object(headers)
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
            raise GateError("GitHub API headers are invalid")
        # Only a complete single page is admissible; never follow API links.
        if any(k.lower() == "link" and v.strip() for k, v in headers.items()):
            raise GateError("GitHub API evidence is paginated or ambiguous")
        return payload

    def verify_main():
        if fetch("commits/main").get("sha") != source_sha:
            raise GateError("Selected source is no longer current main; release denied")

    verify_main()
    evidence = []
    workflow_ids = set()
    for filename in REQUIRED_WORKFLOWS:
        path = f".github/workflows/{filename}"
        identity = fetch(f"actions/workflows/{filename}")
        workflow_id = _integer(identity.get("id"))
        if (
            identity.get("path") != path or identity.get("state") != "active"
            or workflow_id in workflow_ids
        ):
            raise GateError("Required workflow identity is invalid or ambiguous")
        workflow_ids.add(workflow_id)
        query = urlencode({"head_sha": source_sha, "branch": "main", "event": "push", "per_page": 100})
        payload = fetch(f"actions/workflows/{workflow_id}/runs?{query}")
        count = _integer(payload.get("total_count"), minimum=0)
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list) or not runs or count != len(runs) or count > 100:
            raise GateError("Required workflow runs are missing or incomplete")
        seen_attempts = set()
        id_to_number = {}
        number_to_id = {}
        for run in runs:
            _object(run)
            run_id = _integer(run.get("id"))
            run_number = _integer(run.get("run_number"))
            attempt = _integer(run.get("run_attempt"))
            if (
                _integer(run.get("workflow_id")) != workflow_id
                or run.get("path") not in (path, path + "@main", path + "@refs/heads/main")
                or run.get("head_sha") != source_sha
                or run.get("head_branch") != "main"
                or run.get("event") != "push"
                or _object(run.get("repository")).get("full_name") != repository
                or _object(run.get("head_repository")).get("full_name") != repository
            ):
                raise GateError("Workflow run is not bound to the trusted release source")
            if (
                (run_id, attempt) in seen_attempts
                or id_to_number.get(run_id, run_number) != run_number
                or number_to_id.get(run_number, run_id) != run_id
            ):
                raise GateError("Workflow run identity or attempt is ambiguous")
            seen_attempts.add((run_id, attempt))
            id_to_number[run_id] = run_number
            number_to_id[run_number] = run_id
        latest = max(runs, key=lambda run: (run["run_number"], run["run_attempt"]))
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise GateError(f"Required workflow {filename} is not green; retry release after checks complete")
        evidence.append({
            "workflow_id": workflow_id, "run_id": latest["id"],
            "run_attempt": latest["run_attempt"], "source_sha": source_sha,
            "conclusion": "success",
        })
    verify_main()
    return {"status": "PASSED", "source_sha": source_sha, "workflows": evidence}


def main(argv=None, *, request_json=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_release(args.repository, args.source_sha, os.environ.get("GH_TOKEN", ""), request_json=request_json)
    except GateError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
