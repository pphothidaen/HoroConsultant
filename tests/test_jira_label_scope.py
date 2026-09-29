#!/usr/bin/env python3
"""Scope-relevance validation for the Jira agent-label gate - KAN-181.

Root cause this suite pins: `cmd_check` in scripts/jira_label_gate.py only
validated LABEL PRESENCE. A stale ticket key that happened to carry an
agent-* label satisfied the gate even when the ticket's scope had nothing to
do with the commit (e.g. KAN-130 "Unified WorkerRuntime Abstraction" cited by
webhook/credential commits).

Design constraint: scope matching is heuristic, so a mismatch must WARN and
still return 0. The fail-closed/fail-open exit-code contract (0 = agent label
present, 1 = present-but-unlabeled, 2 = cannot verify) is load-bearing and
must be preserved exactly.
"""

import importlib.util
import os

import pytest

GATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "jira_label_gate.py",
)


def load_gate_module():
    spec = importlib.util.spec_from_file_location("jira_label_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def _gate():
    return load_gate_module()


# Real KAN-130 / KAN-181 summaries, so the fixtures mirror the real defect.
KAN_130 = {
    "fields": {
        "labels": ["agent-developer_core"],
        "summary": "[Sprint K - FEAT 1] Unified WorkerRuntime Abstraction & "
                   "Pre-Spawn Selection Engine",
    }
}
KAN_181 = {
    "fields": {
        "labels": ["agent-orchestrator", "agent-hermes"],
        "summary": "Label scope validation for agent-label governance gate",
    }
}


def _patched(gate, issue, status=200):
    """Mock build_client/fetch_issue exactly as tests/test_jira_label_gate.py does."""
    import unittest.mock as mock
    return (
        mock.patch.object(
            gate, "build_client",
            return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None),
        ),
        mock.patch.object(gate, "fetch_issue", return_value=(status, issue)),
    )


class TestScopeTokenization:
    """Unit coverage for the scope tokenizer."""

    def test_drops_ticket_key_and_governance_boilerplate(self, _gate):
        """The ticket key itself and the agent-* roster are not scope signal."""
        tokens = _gate.scope_tokens("[KAN-181] feat: agent-hermes webhook rotation")
        assert "kan" not in tokens
        assert "181" not in tokens
        assert "agent" not in tokens
        assert "hermes" not in tokens
        assert "webhook" in tokens
        assert "rotation" in tokens

    def test_drops_stopwords_and_short_tokens(self, _gate):
        tokens = _gate.scope_tokens("the fix for a flaky test in CI")
        assert "the" not in tokens
        assert "for" not in tokens
        assert "in" not in tokens
        # "fix"/"test" are too generic/short to be scope signal
        assert "flaky" in tokens

    def test_normalizes_plurals(self, _gate):
        assert "label" in _gate.scope_tokens("webhooks and labels")
        assert "webhook" in _gate.scope_tokens("webhooks and labels")

    def test_unicode_em_dash_summary_still_tokenizes(self, _gate):
        tokens = _gate.scope_tokens("Concurrency Control Plane - Leases & Fencing")
        assert "concurrency" in tokens
        assert "leases" in tokens
        assert "fencing" in tokens

    def test_empty_input_yields_no_tokens(self, _gate):
        assert _gate.scope_tokens("") == set()
        assert _gate.scope_tokens("   \n\t ") == set()


class TestScopeOverlap:
    """Unit coverage for the overlap decision."""

    def test_related_commit_shares_tokens(self, _gate):
        """A commit that names the ticket's subject matter is related."""
        summary = "Label scope validation for agent-label governance gate"
        message = "[KAN-181] feat(governance): add scope validation to label gate"
        overlap = _gate.scope_overlap(summary, message)
        assert overlap, "expected shared scope tokens for a genuinely related commit"
        assert {"label", "validation"} & overlap

    def test_unrelated_commit_shares_nothing(self, _gate):
        """The live defect: KAN-130 scope vs a webhook/credential commit."""
        summary = KAN_130["fields"]["summary"]
        message = "[KAN-130] fix(provenance): rotate webhook credential store"
        assert _gate.scope_overlap(summary, message) == set()

    def test_lease_ticket_vs_webhook_commit_is_unrelated(self, _gate):
        summary = ("[Sprint K - FEAT 3] Concurrency Control Plane: Renewable "
                   "Leases & Monotonic Fencing Tokens")
        message = "[KAN-133] feat(webhook): dispatch inbound webhook events"
        assert _gate.scope_overlap(summary, message) == set()

    def test_missing_summary_is_not_evaluable(self, _gate):
        """No summary in the payload means no evidence - must not WARN."""
        assert _gate.scope_overlap("", "feat: anything at all") is None
        assert _gate.scope_overlap(None, "feat: anything at all") is None

    def test_missing_commit_message_is_not_evaluable(self, _gate):
        """Backward-compatible call sites pass no message; stay silent."""
        assert _gate.scope_overlap("Label scope validation", "") is None
        assert _gate.scope_overlap("Label scope validation", None) is None

    def test_summary_with_only_noise_is_not_evaluable(self, _gate):
        """A summary of pure stopwords/boilerplate cannot be judged."""
        assert _gate.scope_overlap("agent-hermes", "[KAN-1] chore: fix it") is None

    def test_empty_commit_is_not_evaluable(self, _gate):
        assert _gate.scope_overlap("Unified WorkerRuntime Abstraction", "") is None


class TestCmdCheckScopeWarning:
    """End-to-end coverage of the REAL cmd_check wiring."""

    def test_scope_mismatch_warns_but_still_passes(self, _gate, capsys):
        """A labeled but off-scope ticket WARNs and returns 0 (never blocks)."""
        client, fetch = _patched(_gate, KAN_130)
        with client, fetch:
            rc = _gate.cmd_check(
                {}, "KAN-130",
                "[KAN-130] fix(provenance): rotate webhook credential store",
            )
        out = capsys.readouterr().out
        assert rc == 0, f"scope mismatch must not block the commit, got {rc}"
        assert "[WARN]" in out
        # The warning must name BOTH sides so an author can self-correct.
        assert "WorkerRuntime" in out
        assert "rotate webhook credential store" in out
        assert "KAN-130" in out

    def test_scope_match_emits_no_warning(self, _gate, capsys):
        client, fetch = _patched(_gate, KAN_181)
        with client, fetch:
            rc = _gate.cmd_check(
                {}, "KAN-181",
                "[KAN-181] feat(governance): add label scope validation",
            )
        out = capsys.readouterr().out
        assert rc == 0
        assert "[WARN]" not in out
        assert "[OK] KAN-181 carries agent label: agent-orchestrator, agent-hermes" in out

    def test_no_message_keeps_legacy_output_exactly(self, _gate, capsys):
        """Existing callers pass no message: byte-identical [OK] line, no warn."""
        client, fetch = _patched(_gate, KAN_130)
        with client, fetch:
            rc = _gate.cmd_check({}, "KAN-130")
        out = capsys.readouterr().out
        assert rc == 0
        assert out.strip() == "[OK] KAN-130 carries agent label: agent-developer_core"

    def test_missing_summary_never_warns(self, _gate, capsys):
        """Ticket payload without a summary is not evidence of mismatch."""
        client, fetch = _patched(_gate, {"fields": {"labels": ["agent-hermes"]}})
        with client, fetch:
            rc = _gate.cmd_check({}, "KAN-105", "feat: totally unrelated subject")
        out = capsys.readouterr().out
        assert rc == 0
        assert "[WARN]" not in out

    def test_warning_output_is_pure_ascii(self, _gate, capsys):
        """scripts/AGENTS.md forbids unicode in script output."""
        client, fetch = _patched(_gate, KAN_130)
        with client, fetch:
            _gate.cmd_check({}, "KAN-130", "[KAN-130] fix: rotate webhook credential")
        out = capsys.readouterr().out
        out.encode("ascii")  # raises on any non-ASCII byte


class TestExitCodeContractUnchanged:
    """The load-bearing contract: a scope check must not perturb any exit code."""

    def test_unlabeled_ticket_still_fails_closed(self, _gate, capsys):
        client, fetch = _patched(_gate, {"fields": {"labels": ["bug"], "summary": "Bug"}})
        with client, fetch:
            rc = _gate.cmd_check({}, "KAN-105", "feat: something")
        assert rc == 1
        assert "[ERROR] KAN-105 has no agent-* label" in capsys.readouterr().out

    @pytest.mark.parametrize("status", [401, 403, 404, 500, 503])
    def test_unverifiable_still_fails_open(self, _gate, status):
        client, fetch = _patched(_gate, {}, status=status)
        with client, fetch:
            rc = _gate.cmd_check({}, "KAN-999", "feat: something unrelated")
        assert rc == 2, f"status {status} must stay fail-open (2), got {rc}"

    def test_missing_credentials_still_fails_open_without_network(self, _gate, monkeypatch):
        import unittest.mock as mock
        for var in ("JIRA_API_TOKEN", "JIRA_EMAIL", "JIRA_BASE_URL"):
            monkeypatch.delenv(var, raising=False)
        with mock.patch.object(_gate, "fetch_issue") as fetch:
            rc = _gate.cmd_check({}, "KAN-105", "feat: something")
        assert rc == 2
        fetch.assert_not_called()

    def test_no_additional_http_calls(self, _gate):
        """Scope checking must reuse the existing fetch_issue response only."""
        import unittest.mock as mock
        client, fetch = _patched(_gate, KAN_130)
        with client, fetch:
            _gate.cmd_check({}, "KAN-130", "fix: rotate webhook credential")
        assert fetch.call_count == 1, "scope check must not issue a new HTTP request"


class TestScopeCheckIsWiringOnly:
    """Guards against the warning being decoupled from the return value."""

    def test_warning_does_not_change_return_value(self, _gate):
        """Same ticket, two commits: rc identical whether scope matches or not."""
        client, fetch = _patched(_gate, KAN_181)
        with client, fetch:
            matched = _gate.cmd_check({}, "KAN-181", "feat: add label scope validation")
        client, fetch = _patched(_gate, KAN_181)
        with client, fetch:
            mismatched = _gate.cmd_check({}, "KAN-181", "feat: tune unrelated postgres index")
        assert matched == mismatched == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
