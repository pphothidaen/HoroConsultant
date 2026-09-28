"""Contract tests for the CI-failure callback in .github/workflows/jira-governance.yml.

These guard the Hermes V2 HMAC webhook contract. The auth scheme, the fail-closed
curl flags, and the injection boundary are all security-relevant and each has
previously been wrong in ways a YAML lint cannot detect.

See: hermes-webhook-bridge/references/hmac-signature.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "jira-governance.yml"


def _load() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _dispatch_step() -> dict:
    job = _load()["jobs"]["notify-agent-on-failure"]
    steps = job["steps"]
    assert steps, "notify-agent-on-failure must have at least one step"
    return steps[-1]


def _script() -> str:
    return _dispatch_step()["run"]


def test_workflow_is_valid_yaml() -> None:
    """Guard against a malformed workflow silently disabling governance."""
    assert isinstance(_load()["jobs"], dict)


def test_dispatch_uses_hmac_signature_v2() -> None:
    """The receiver validates Hermes V2: X-Webhook-Timestamp + X-Webhook-Signature-V2."""
    script = _script()
    assert "X-Webhook-Signature-V2" in script
    assert "X-Webhook-Timestamp" in script


def test_dispatch_signs_timestamp_dot_body() -> None:
    """Signature input is exactly '${TIMESTAMP}.${BODY}' per the receiver contract."""
    script = _script()
    assert re.search(r'\$\{TIMESTAMP\}\.\$\{BODY\}', script), (
        "HMAC input must be ${TIMESTAMP}.${BODY}"
    )
    assert "openssl dgst -sha256 -hmac" in script


def test_dispatch_does_not_use_bearer_token_auth() -> None:
    """Static bearer auth is not the receiver's contract and must not reappear."""
    assert "Authorization: Bearer" not in _script()


def test_dispatch_uses_fail_closed_curl() -> None:
    """curl without -f exits 0 on HTTP 4xx/5xx, silently disabling the callback."""
    assert re.search(r"curl\s+-[a-zA-Z]*f", _script()), "curl must use -f to fail closed"


def test_dispatch_enables_strict_shell() -> None:
    """set -euo pipefail so a signing/transport failure aborts the step."""
    assert "set -euo pipefail" in _script()


def test_pr_controlled_values_are_not_interpolated_into_script() -> None:
    """Script injection guard: PR branch name is attacker-controlled.

    GitHub Actions expands ${{ }} inside `run:` before the shell sees it, so an
    expression referencing pull_request fields inside the script body is a
    command-injection vector. Such values must arrive via `env:` instead.
    """
    script = _script()
    assert "github.event.pull_request" not in script, (
        "untrusted pull_request fields must not be interpolated into the run block"
    )
    env = _dispatch_step().get("env", {})
    assert "GH_BRANCH" in env, "PR branch must be passed through env"


def test_secret_is_not_exposed_to_the_script_body() -> None:
    """Secrets belong in env:, not spliced into the shell text."""
    env = _dispatch_step().get("env", {})
    assert env.get("HERMES_TOKEN", "").startswith("${{ secrets."), (
        "HERMES_TOKEN must be populated from secrets context"
    )
    assert "secrets." not in _script()
