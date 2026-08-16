"""Tests for fail-closed Docker Hub one-time tag selection."""

from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "dockerhub_tag_policy.py"


def _load_module():
    assert SCRIPT.exists(), f"missing tag policy: {SCRIPT.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location("dockerhub_tag_policy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, payload: dict, status: int = 200):
        self._body = json.dumps(payload).encode()
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._body


class _Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, **_kwargs):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_existing_private_tag_is_detected_with_authenticated_hub_api():
    policy = _load_module()
    opener = _Opener(_Response({"token": "jwt"}), _Response({"name": "v1.0"}))

    status = policy.tag_status(
        username="owner",
        password="secret",
        namespace="owner",
        repository="image",
        tag="v1.0",
        opener=opener,
    )

    assert status == policy.EXISTS
    assert opener.requests[1].get_header("Authorization") == "Bearer jwt"


def test_only_an_authenticated_404_is_treated_as_missing():
    policy = _load_module()
    missing = urllib.error.HTTPError(
        url="https://hub.docker.com/tag",
        code=404,
        msg="not found",
        hdrs=None,
        fp=io.BytesIO(b'{"detail":"not found"}'),
    )
    opener = _Opener(_Response({"token": "jwt"}), missing)

    status = policy.tag_status(
        username="owner",
        password="secret",
        namespace="owner",
        repository="image",
        tag="v1.0",
        opener=opener,
    )

    assert status == policy.MISSING


def test_auth_and_network_failures_are_not_misclassified_as_missing():
    policy = _load_module()
    opener = _Opener(urllib.error.URLError("secret-bearing diagnostic"))

    try:
        policy.tag_status(
            username="owner",
            password="CANARY_SECRET",
            namespace="owner",
            repository="image",
            tag="v1.0",
            opener=opener,
        )
    except policy.PolicyCheckError as exc:
        assert "CANARY_SECRET" not in str(exc)
        assert "secret-bearing diagnostic" not in str(exc)
    else:
        raise AssertionError("network failure must fail closed")
