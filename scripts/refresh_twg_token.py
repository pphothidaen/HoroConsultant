#!/usr/bin/env python3
"""Refresh the TWG (Atlassian 3LO) OAuth access token.

Why this exists
---------------
Atlassian forces *rotating refresh tokens* on newly created OAuth 2.0 (3LO)
integrations: every refresh invalidates the previous refresh token and
returns a new one. Access tokens live ~8h.

GitHub Actions runners are ephemeral. `twg auth refresh` reads credentials
from the CLI's local auth storage, which does not exist on a fresh runner,
so the CLI cannot self-refresh in CI. The refresh_token has to be carried
across runs as a secret and the refresh_token grant performed here.

The rotated refresh_token is written back to the repository secret so the
next run starts from a live credential.

Usage
-----
    TWG_CLIENT_ID=... TWG_CLIENT_SECRET=... TWG_REFRESH_TOKEN=... \\
        python3 scripts/refresh_twg_token.py

Prints the access token on stdout. Also emits `access_token` to
$GITHUB_OUTPUT when that variable is present.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

TOKEN_URL = "https://auth.atlassian.com/oauth/token"
SECRET_NAME = "TWG_REFRESH_TOKEN"

# Transport is injectable so tests can exercise the success and failure paths
# without reaching Atlassian.
Transport = Callable[[str, dict[str, str], dict[str, str]], dict[str, Any]]


def build_request_body(
    client_id: str, client_secret: str, refresh_token: str
) -> dict[str, str]:
    """Build the refresh_token grant payload."""
    return {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }


def default_transport(
    url: str, body: dict[str, str], headers: dict[str, str]
) -> dict[str, Any]:
    """POST the grant to the token endpoint."""
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(body).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def request_new_token(
    body: dict[str, str], transport: Transport = default_transport
) -> dict[str, Any]:
    """Exchange a refresh_token for a fresh access token.

    Raises RuntimeError with the server's own message on failure — the
    Atlassian error body names the actual problem (revoked token, wrong
    client), and swallowing it would surface as a bare 401 much later.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    try:
        return transport(TOKEN_URL, body, headers)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"token refresh failed: HTTP {exc.code}: {detail[:400]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"token endpoint unreachable: {exc.reason}") from exc


def persist_refresh_token(token: str, repo: str) -> None:
    """Write the rotated refresh_token back to the repository secret.

    Rotating tokens are single-use: failing to persist here means the next
    scheduled run starts from a token Atlassian has already invalidated.
    """
    subprocess.run(
        ["gh", "secret", "set", SECRET_NAME, "--body", token, "--repo", repo],
        check=True,
        capture_output=True,
        text=True,
    )


def emit_github_output(name: str, value: str) -> None:
    """Append to $GITHUB_OUTPUT when running under Actions."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    client_id = os.environ.get("TWG_CLIENT_ID", "")
    client_secret = os.environ.get("TWG_CLIENT_SECRET", "")
    refresh_token = os.environ.get("TWG_REFRESH_TOKEN", "")

    missing = [
        name
        for name, value in (
            ("TWG_CLIENT_ID", client_id),
            ("TWG_CLIENT_SECRET", client_secret),
            ("TWG_REFRESH_TOKEN", refresh_token),
        )
        if not value
    ]
    if missing:
        # Missing configuration is a setup problem, not an outage: exit 0 so a
        # scheduled run cannot flip the MTTR monitor into breach because
        # provisioning has not happened yet.
        print(f"::notice::Skipping refresh; not configured: {', '.join(missing)}")
        return 0

    body = build_request_body(client_id, client_secret, refresh_token)
    try:
        response = request_new_token(body)
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1

    access_token = response.get("access_token", "")
    rotated_refresh = response.get("refresh_token", "")
    if not access_token:
        print("::error::token endpoint returned no access_token")
        return 1

    emit_github_output("access_token", access_token)

    if rotated_refresh:
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        if repo:
            try:
                persist_refresh_token(rotated_refresh, repo)
            except subprocess.CalledProcessError as exc:
                print(f"::error::failed to persist rotated refresh_token: {exc.stderr[:300]}")
                return 1

    print(access_token)
    return 0


if __name__ == "__main__":
    sys.exit(main())