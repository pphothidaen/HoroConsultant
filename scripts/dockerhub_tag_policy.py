#!/usr/bin/env python3
"""Fail-closed Docker Hub tag existence check for one-time release aliases."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EXISTS = "EXISTS"
MISSING = "MISSING"
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class PolicyCheckError(RuntimeError):
    """Raised when Docker Hub cannot prove whether a tag exists."""


def _safe_component(value: str, label: str) -> str:
    if not _NAME_PATTERN.fullmatch(value):
        raise PolicyCheckError(f"invalid {label}")
    return urllib.parse.quote(value, safe="")


def _open_json(opener: Any, request: urllib.request.Request) -> tuple[int, dict]:
    with opener.open(request, timeout=15) as response:
        status = int(response.status)
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise PolicyCheckError("Docker Hub returned an invalid response shape")
    return status, payload


def tag_status(
    *,
    username: str,
    password: str,
    namespace: str,
    repository: str,
    tag: str,
    opener: Any | None = None,
) -> str:
    """Return EXISTS or MISSING; all ambiguous failures raise fail-closed."""
    if not username or not password:
        raise PolicyCheckError("Docker Hub credentials are missing")
    namespace_path = _safe_component(namespace, "namespace")
    repository_path = _safe_component(repository, "repository")
    tag_path = _safe_component(tag, "tag")
    client = opener or urllib.request.build_opener()
    login_body = json.dumps(
        {"username": username, "password": password}, separators=(",", ":")
    ).encode("utf-8")
    login_request = urllib.request.Request(
        "https://hub.docker.com/v2/users/login",
        data=login_body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        status_code, login_payload = _open_json(client, login_request)
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ):
        raise PolicyCheckError("Docker Hub authentication check failed") from None
    if status_code != 200:
        raise PolicyCheckError("Docker Hub authentication check failed")
    token = login_payload.get("token")
    if not isinstance(token, str) or not token:
        raise PolicyCheckError("Docker Hub authentication response omitted a token")

    tag_request = urllib.request.Request(
        (
            "https://hub.docker.com/v2/namespaces/"
            f"{namespace_path}/repositories/{repository_path}/tags/{tag_path}"
        ),
        headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        tag_status_code, _ = _open_json(client, tag_request)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return MISSING
        raise PolicyCheckError("Docker Hub tag lookup failed") from None
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ):
        raise PolicyCheckError("Docker Hub tag lookup failed") from None
    if tag_status_code == 200:
        return EXISTS
    raise PolicyCheckError("Docker Hub tag lookup returned an unexpected status")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--username", default=os.getenv("DOCKER_USERNAME", ""))
    parser.add_argument("--password", default=os.getenv("DOCKER_PASSWORD", ""))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        status = tag_status(
            username=args.username,
            password=args.password,
            namespace=args.namespace,
            repository=args.repository,
            tag=args.tag,
        )
    except PolicyCheckError:
        print("[ERROR] Docker Hub tag policy check failed; details redacted.", file=sys.stderr)
        return 2
    print(status)
    return 0 if status == EXISTS else 4


if __name__ == "__main__":
    sys.exit(main())
