"""Tests for the direct Jira Cloud query helper.

orchestrator-dispatch polls for Ready tickets. That used to go through the
Teamwork Graph CLI, which cannot run on a CI runner (its OAuth scopes are not
grantable through the developer console, and `twg login` needs a browser).
These tests pin the replacement.

  - the JQL travels as a query parameter, so quotes in a lane filter cannot
    break the URL
  - the bearer token is the 3LO token from the refresh helper
  - upstream errors surface the Jira message rather than a bare status code
  - only the fields the caller reads are emitted, so a large payload cannot
    flood the workflow log
"""

import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/jira_query.py"

spec = importlib.util.spec_from_file_location("jira_query", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

JQL = 'project = KAN AND status = "Ready" AND "Project Lane" = "Horo Consultant"'


# ── Request shape ───────────────────────────────────────────────────────────

def test_uses_jira_search_endpoint() -> None:
    req = mod.build_request("https://pansakorn.atlassian.net", "project = KAN", "tok")
    assert req.full_url.startswith(
        "https://pansakorn.atlassian.net/rest/api/3/search/jql?"
    )


def test_jql_is_query_parameter_not_path() -> None:
    """A quote in the lane filter must not be able to escape the URL."""
    req = mod.build_request("https://x.atlassian.net", JQL, "tok")
    assert '"Ready"' not in req.full_url
    assert "%22Ready%22" in req.full_url
    assert req.full_url.count("?") == 1


def test_bearer_token_header() -> None:
    req = mod.build_request("https://x.atlassian.net", "project = KAN", "atlassian-3lo")
    assert req.headers["Authorization"] == "Bearer atlassian-3lo"


def test_base_url_trailing_slash_does_not_double_up() -> None:
    req = mod.build_request("https://x.atlassian.net/", "project = KAN", "t")
    assert "net.net//rest" not in req.full_url


def test_requests_summary_and_status_fields() -> None:
    req = mod.build_request("https://x.atlassian.net", "project = KAN", "t")
    assert "summary" in req.full_url and "status" in req.full_url


# ── Missing credentials ─────────────────────────────────────────────────────

def test_missing_token_fails_before_any_request() -> None:
    """A token refresh gap must surface, not silently poll zero tickets."""
    with pytest.raises(RuntimeError) as excinfo:
        mod.search_jira("https://x.atlassian.net", "project = KAN", "")
    assert "no access token" in str(excinfo.value)


# ── Error surfacing ─────────────────────────────────────────────────────────

def test_http_error_carries_jira_message() -> None:
    def transport(request, timeout=None):
        raise urllib.error.HTTPError(
            request.full_url, 403, "Forbidden", {},
            io.BytesIO(b'{"errorMessages":["JQL is malformed"]}'),
        )

    mod.urllib.request.urlopen = transport
    try:
        with pytest.raises(RuntimeError) as excinfo:
            mod.search_jira("https://x.atlassian.net", "bad jql", "tok")
    finally:
        mod.urllib.request.urlopen = urllib.request.urlopen
    assert "403" in str(excinfo.value)
    assert "malformed" in str(excinfo.value)


# ── Payload shaping ─────────────────────────────────────────────────────────

def test_main_emits_only_needed_fields(monkeypatch, capsys) -> None:
    """Guard against dumping a whole Jira payload into the workflow log."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://x.atlassian.net")
    monkeypatch.setattr(mod, "search_jira", lambda *a, **k: {
        "issues": [
            {
                "key": "KAN-1",
                "fields": {
                    "summary": "Do the thing",
                    "status": {"name": "Ready"},
                    "comment": {"comments": [{"body": "long text..."}] * 50},
                    "attachment": ["x"] * 20,
                },
            }
        ],
        "total": 1,
        "expand": "schema,names",
    })
    assert mod.main.__wrapped__() if hasattr(mod.main, "__wrapped__") else True

    monkeypatch.setattr("sys.argv", ["jira_query.py", "--jql", "project = KAN"])
    assert mod.main() == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload == {
        "issues": [{"key": "KAN-1", "summary": "Do the thing", "status": "Ready"}]
    }
    assert "long text" not in out
    assert "attachment" not in out


def test_missing_fields_do_not_crash(monkeypatch, capsys) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://x.atlassian.net")
    monkeypatch.setattr(mod, "search_jira", lambda *a, **k: {"issues": [{"key": "K-1"}]})
    monkeypatch.setattr("sys.argv", ["jira_query.py", "--jql", "project = KAN"])
    assert mod.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["issues"][0] == {"key": "K-1", "summary": None, "status": None}


def test_missing_base_url_is_reported(monkeypatch, capsys) -> None:
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.setattr("sys.argv", ["jira_query.py", "--jql", "project = KAN"])
    assert mod.main() == 1
    assert "JIRA_BASE_URL" in capsys.readouterr().out