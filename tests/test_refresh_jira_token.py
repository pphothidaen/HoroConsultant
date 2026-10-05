"""Tests for the Atlassian 3LO OAuth refresh helper.

Atlassian forces rotating refresh tokens on new 3LO integrations and
GitHub runners are ephemeral, so the refresh_token grant has to run in the
workflow. These tests pin the behaviour that matters operationally:

  - the grant payload is a refresh_token grant (not authorization_code)
  - a rotated refresh_token is written back, because single-use tokens make
    that the difference between a working and a broken next run
  - unconfigured runs exit 0, so provisioning delay cannot raise an SLO breach
  - server errors surface the Atlassian message instead of a bare failure
"""

import importlib.util
import io
import subprocess
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/refresh_jira_token.py"
WORKFLOW = REPO_ROOT / ".github/workflows/orchestrator-dispatch.yml"

spec = importlib.util.spec_from_file_location("refresh_jira_token", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


# ── Grant payload ───────────────────────────────────────────────────────────

def test_uses_refresh_token_grant() -> None:
    body = mod.build_request_body("cid", "csecret", "rtoken")
    assert body["grant_type"] == "refresh_token"
    assert body["client_id"] == "cid"
    assert body["client_secret"] == "csecret"
    assert body["refresh_token"] == "rtoken"


def test_grant_payload_omits_unrelated_fields() -> None:
    """No scope field: a refresh must not widen access."""
    body = mod.build_request_body("cid", "csecret", "rtoken")
    assert "scope" not in body
    assert "redirect_uri" not in body


def test_request_posts_to_atlassian_token_endpoint() -> None:
    seen: dict = {}

    def transport(url, body, headers):
        seen.update(url=url, body=body, headers=headers)
        return {"access_token": "at", "refresh_token": "rt"}

    mod.request_new_token(mod.build_request_body("c", "s", "r"), transport)
    assert seen["url"] == "https://auth.atlassian.com/oauth/token"
    assert seen["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


# ── Rotating token persistence ──────────────────────────────────────────────

def test_rotated_refresh_token_is_persisted(monkeypatch) -> None:
    """The whole point of rotating tokens: the old one is already dead."""
    calls: list = []

    def fake_persist(token: str, repo: str) -> None:
        calls.append((token, repo))

    monkeypatch.setattr(mod, "persist_refresh_token", fake_persist)
    monkeypatch.setenv("GITHUB_REPOSITORY", "pphothidaen/HoroConsultant")
    monkeypatch.setenv("JIRA_CLIENT_ID", "c")
    monkeypatch.setenv("JIRA_CLIENT_SECRET", "s")
    monkeypatch.setenv("JIRA_REFRESH_TOKEN", "old")
    monkeypatch.setattr(mod, "request_new_token", lambda body: {
        "access_token": "at", "refresh_token": "rotated-new"})

    assert mod.main() == 0
    assert calls == [("rotated-new", "pphothidaen/HoroConsultant")]


def test_failure_to_persist_is_a_hard_error(monkeypatch) -> None:
    """Silently losing the rotated token breaks every later run."""
    def boom(token, repo):
        raise subprocess.CalledProcessError(1, "gh", stderr="no permission")

    monkeypatch.setattr(mod, "persist_refresh_token", boom)
    monkeypatch.setenv("GITHUB_REPOSITORY", "pphothidaen/HoroConsultant")
    monkeypatch.setenv("JIRA_CLIENT_ID", "c")
    monkeypatch.setenv("JIRA_CLIENT_SECRET", "s")
    monkeypatch.setenv("JIRA_REFRESH_TOKEN", "old")
    monkeypatch.setattr(mod, "request_new_token", lambda body: {
        "access_token": "at", "refresh_token": "rotated-new"})

    assert mod.main() == 1


def test_workflow_refreshes_token_before_query() -> None:
    """A static JIRA_ACCESS_TOKEN cannot work: access tokens expire in ~8h."""
    text = WORKFLOW.read_text(encoding="utf-8")
    refresh_idx = text.find("scripts/refresh_jira_token.py")
    poll_idx = text.find("scripts/jira_query.py")
    assert refresh_idx != -1, "workflow never calls the refresh helper"
    assert poll_idx != -1, "Jira poll step disappeared"
    assert refresh_idx < poll_idx, (
        "refresh must run before the Jira query, otherwise the poll uses an "
        "already-expired token"
    )


def test_workflow_exposes_refreshed_token_to_jira() -> None:
    """JIRA_ACCESS_TOKEN must read the refresh step output."""
    text = WORKFLOW.read_text(encoding="utf-8").replace(" ", "").replace("\n", "")
    assert "JIRA_ACCESS_TOKEN:${{steps.jira-token.outputs.access_token}}" in text, (
        "JIRA_ACCESS_TOKEN is not wired to the refresh output"
    )


def test_workflow_does_not_invoke_twg() -> None:
    """The Teamwork Graph CLI is gone: unusable scopes and no CI login."""
    text = WORKFLOW.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue  # comments explain why the CLI was removed
        for token in ("twg ", "TWG_", "twg-token"):
            assert token not in stripped, f"workflow still invokes {token!r}: {line}"


def test_workflow_passes_refresh_inputs() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in ("JIRA_CLIENT_ID", "JIRA_CLIENT_SECRET", "JIRA_REFRESH_TOKEN"):
        assert f"{name}: ${{{{ secrets.{name} }}}}" in text, (
            f"{name} is not wired into the refresh helper"
        )


def test_workflow_no_dead_jira_user_email() -> None:
    """JIRA_USER_EMAIL is not a repo secret; the dead reference must be gone."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "JIRA_USER_EMAIL" not in text, (
        "dead secrets.JIRA_USER_EMAIL reference must be removed"
    )


# ── Unconfigured runs ───────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "missing", ["JIRA_CLIENT_ID", "JIRA_CLIENT_SECRET", "JIRA_REFRESH_TOKEN"]
)
def test_unconfigured_exits_zero(monkeypatch, missing, capsys) -> None:
    """Provisioning has not happened yet is not an SLO breach."""
    for name in ("JIRA_CLIENT_ID", "JIRA_CLIENT_SECRET", "JIRA_REFRESH_TOKEN"):
        monkeypatch.setenv(name, "x")
    monkeypatch.delenv(missing)
    assert mod.main() == 0
    assert "Skipping refresh" in capsys.readouterr().out


# ── Error surfacing ─────────────────────────────────────────────────────────

def test_http_error_carries_atlassian_message() -> None:
    """A bare 401 hides whether the token was revoked or the client wrong."""
    def transport(url, body, headers):
        raise urllib.error.HTTPError(
            url, 401, "Unauthorized", {}, io.BytesIO(b'{"error":"invalid_grant"}')
        )

    with pytest.raises(RuntimeError) as excinfo:
        mod.request_new_token({"grant_type": "refresh_token"}, transport)
    assert "401" in str(excinfo.value)
    assert "invalid_grant" in str(excinfo.value)


def test_network_failure_is_reported() -> None:
    def transport(url, body, headers):
        raise urllib.error.URLError("connection refused")

    with pytest.raises(RuntimeError) as excinfo:
        mod.request_new_token({"grant_type": "refresh_token"}, transport)
    assert "unreachable" in str(excinfo.value)


def test_response_without_access_token_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("JIRA_CLIENT_ID", "c")
    monkeypatch.setenv("JIRA_CLIENT_SECRET", "s")
    monkeypatch.setenv("JIRA_REFRESH_TOKEN", "old")
    monkeypatch.setattr(mod, "request_new_token", lambda body: {"scope": "x"})
    assert mod.main() == 1


# ── Secret hygiene ──────────────────────────────────────────────────────────

def test_secret_reaches_gh_via_argv_not_interpolation() -> None:
    """Passing the token through --body keeps it out of shell history."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "ATATT" not in source
    assert '"--body", token' in source


def test_script_is_executable_and_has_shebang() -> None:
    assert SCRIPT.read_text(encoding="utf-8").startswith("#!")


def test_access_token_is_emitted_to_github_output(monkeypatch, tmp_path) -> None:
    out = tmp_path / "gh_output"
    out.write_text("")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("JIRA_CLIENT_ID", "c")
    monkeypatch.setenv("JIRA_CLIENT_SECRET", "s")
    monkeypatch.setenv("JIRA_REFRESH_TOKEN", "old")
    monkeypatch.setattr(mod, "request_new_token", lambda body: {"access_token": "at"})

    assert mod.main() == 0
    assert "access_token=at" in out.read_text()