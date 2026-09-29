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
import json
import os
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
GATE_PATH = os.path.join(REPO_ROOT, "scripts", "jira_label_gate.py")
COMMIT_MSG_HOOK = os.path.join(REPO_ROOT, ".githooks", "commit-msg")
PRE_COMMIT_HOOK = os.path.join(REPO_ROOT, ".githooks", "pre-commit")


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


class _Patched:
    """Context manager yielding the live mocks _patched installs.

    mock.patch.object() returns a PATCHER, which has no call_count; the
    mock with the recorded calls is only available as the __enter__ result.
    """

    def __init__(self, gate, issue, status):
        import unittest.mock as mock
        self._client = mock.patch.object(
            gate, "build_client",
            return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None),
        )
        self._fetch = mock.patch.object(gate, "fetch_issue", return_value=(status, issue))

    def __enter__(self):
        self.build_client = self._client.__enter__()
        self.fetch_issue = self._fetch.__enter__()
        return self

    def __exit__(self, *exc):
        self._fetch.__exit__(*exc)
        return self._client.__exit__(*exc)


def _patched(gate, issue, status=200):
    """Mock build_client/fetch_issue exactly as tests/test_jira_label_gate.py does."""
    return _Patched(gate, issue, status)


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
        patched = _patched(_gate, KAN_130)
        with patched as mocks:
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
        patched = _patched(_gate, KAN_181)
        with patched as mocks:
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
        patched = _patched(_gate, KAN_130)
        with patched as mocks:
            rc = _gate.cmd_check({}, "KAN-130")
        out = capsys.readouterr().out
        assert rc == 0
        assert out.strip() == "[OK] KAN-130 carries agent label: agent-developer_core"

    def test_missing_summary_never_warns(self, _gate, capsys):
        """Ticket payload without a summary is not evidence of mismatch."""
        patched = _patched(_gate, {"fields": {"labels": ["agent-hermes"]}})
        with patched as mocks:
            rc = _gate.cmd_check({}, "KAN-105", "feat: totally unrelated subject")
        out = capsys.readouterr().out
        assert rc == 0
        assert "[WARN]" not in out

    def test_warning_output_is_pure_ascii(self, _gate, capsys):
        """scripts/AGENTS.md forbids unicode in script output."""
        patched = _patched(_gate, KAN_130)
        with patched as mocks:
            _gate.cmd_check({}, "KAN-130", "[KAN-130] fix: rotate webhook credential")
        out = capsys.readouterr().out
        out.encode("ascii")  # raises on any non-ASCII byte


class TestExitCodeContractUnchanged:
    """The load-bearing contract: a scope check must not perturb any exit code."""

    def test_unlabeled_ticket_still_fails_closed(self, _gate, capsys):
        patched = _patched(_gate, {"fields": {"labels": ["bug"], "summary": "Bug"}})
        with patched as mocks:
            rc = _gate.cmd_check({}, "KAN-105", "feat: something")
        assert rc == 1
        assert "[ERROR] KAN-105 has no agent-* label" in capsys.readouterr().out

    @pytest.mark.parametrize("status", [401, 403, 404, 500, 503])
    def test_unverifiable_still_fails_open(self, _gate, status):
        patched = _patched(_gate, {}, status=status)
        with patched as mocks:
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
        patched = _patched(_gate, KAN_130)
        with patched as mocks:
            _gate.cmd_check({}, "KAN-130", "fix: rotate webhook credential")
        assert mocks.fetch_issue.call_count == 1, "scope check must not issue a new HTTP request"


class TestScopeCheckIsWiringOnly:
    """Guards against the warning being decoupled from the return value."""

    def test_warning_does_not_change_return_value(self, _gate):
        """Same ticket, two commits: rc identical whether scope matches or not."""
        patched = _patched(_gate, KAN_181)
        with patched as mocks:
            matched = _gate.cmd_check({}, "KAN-181", "feat: add label scope validation")
        patched = _patched(_gate, KAN_181)
        with patched as mocks:
            mismatched = _gate.cmd_check({}, "KAN-181", "feat: tune unrelated postgres index")
        assert matched == mismatched == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ---------------------------------------------------------------------------
# KAN-181 production wiring.
#
# Everything above this section calls cmd_check() directly with a message. The
# CLI never did that: main() dispatched `cmd_check(env, args.key)` with no
# third argument, so the scope heuristic was unreachable from either hook and
# ran in production exactly never. These tests drive the real entry points --
# the argparse dispatch in main() and the .githooks shell hooks executed as
# real processes against a real git repository -- because a passing unit test
# on cmd_check proves nothing about whether the feature fires.
# ---------------------------------------------------------------------------

_MISMATCH_SUMMARY = "Renewable lease fencing tokens for agent dispatch"
_MATCHING_SUMMARY = "Scope relevance validation for the agent label gate"


def _issue_payload(labels, summary):
    return {"fields": {"labels": labels, "summary": summary,
                       "status": {"name": "In Progress"}}}


class _LabeledIssue(_Patched):
    """_Patched pinned to the common case: HTTP 200 with labels+summary."""

    def __init__(self, gate, payload):
        super().__init__(gate, payload, 200)


class TestCliForwardsCommitMessage:
    """main() is the production entry point; it must carry the message."""

    def test_check_subcommand_warns_on_scope_mismatch(self, tmp_path, capsys):
        """The CLI path, not cmd_check, must reach the scope heuristic."""
        gate = load_gate_module()
        message = tmp_path / "COMMIT_EDITMSG"
        message.write_text(
            "[KAN-130] feat: unrelated telemetry exporter retry budget\n",
            encoding="utf-8",
        )
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            rc = gate.main(["check", "KAN-130", "--message-file", str(message)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[WARN] KAN-130 scope does not appear related to this commit." in out
        assert "Renewable lease fencing" in out
        assert "telemetry exporter retry" in out

    def test_check_subcommand_silent_when_scope_matches(self, tmp_path, capsys):
        gate = load_gate_module()
        message = tmp_path / "COMMIT_EDITMSG"
        message.write_text(
            "[KAN-130] feat(governance): scope relevance validation for the "
            "agent label gate\n",
            encoding="utf-8",
        )
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MATCHING_SUMMARY)):
            rc = gate.main(["check", "KAN-130", "--message-file", str(message)])
        assert rc == 0
        assert "scope does not appear related" not in capsys.readouterr().out

    def test_check_subcommand_without_message_stays_silent(self, capsys):
        """No message is not-evaluable, never a mismatch (backward compatible)."""
        gate = load_gate_module()
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            rc = gate.main(["check", "KAN-130"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[OK] KAN-130 carries agent label: agent-hermes" in out
        assert "scope does not appear related" not in out

    def test_inline_message_flag_is_forwarded(self, capsys):
        gate = load_gate_module()
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            rc = gate.main([
                "check", "KAN-130", "--message",
                "[KAN-130] feat: unrelated telemetry exporter retry budget",
            ])
        assert rc == 0
        assert "scope does not appear related" in capsys.readouterr().out

    def test_missing_message_file_fails_open(self, tmp_path, capsys):
        """A message file that vanished must never break or block a commit."""
        gate = load_gate_module()
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            rc = gate.main([
                "check", "KAN-130", "--message-file", str(tmp_path / "absent"),
            ])
        assert rc == 0
        assert "scope does not appear related" not in capsys.readouterr().out

    def test_git_comment_lines_are_stripped(self, tmp_path, capsys):
        """COMMIT_EDITMSG carries the editor template; its comments are not intent.

        The template comment here deliberately repeats the word "lease" from the
        ticket summary. If comments were tokenized they would create a phantom
        scope match and silently suppress a genuine mismatch warning.
        """
        gate = load_gate_module()
        message = tmp_path / "COMMIT_EDITMSG"
        message.write_text(
            "# Changes to be committed: lease renewal logic\n"
            "# On branch fix-kan-181\n"
            "\n"
            "[KAN-130] feat: unrelated telemetry exporter retry budget\n"
            "\n"
            "Test-Baseline: 0123456789abcdef0123456789abcdef01234567\n",
            encoding="utf-8",
        )
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            rc = gate.main(["check", "KAN-130", "--message-file", str(message)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "scope does not appear related" in out
        # The reported subject is the real subject, not the template comment.
        assert "[KAN-130] feat: unrelated telemetry exporter retry budget" in out
        assert "lease renewal logic" not in out

    def test_unlabeled_ticket_still_blocks_via_cli(self, capsys):
        """Wiring the message must not soften the one load-bearing exit code."""
        gate = load_gate_module()
        with _LabeledIssue(gate, _issue_payload(["backend"], _MISMATCH_SUMMARY)):
            rc = gate.main(["check", "KAN-130", "--message", "anything"])
        assert rc == 1
        assert "has no agent-* label" in capsys.readouterr().out

    def test_cli_output_is_ascii(self, tmp_path, capsys):
        """scripts/AGENTS.md: gate stdout must stay ASCII."""
        gate = load_gate_module()
        message = tmp_path / "COMMIT_EDITMSG"
        message.write_text(
            "[KAN-130] feat: \u00e9telemetry \u65e5\u672c\u8a9e retry budget\n",
            encoding="utf-8",
        )
        with _LabeledIssue(gate, _issue_payload(["agent-hermes"], _MISMATCH_SUMMARY)):
            gate.main(["check", "KAN-130", "--message-file", str(message)])
        assert capsys.readouterr().out.isascii()


# A stand-in for scripts/jira_label_gate.py used when driving the real hooks.
# It records the argv it was handed so the test can assert the hook forwards a
# commit message, and echoes a canned gate report so exit-code handling in the
# hook (0 pass / 1 block / 2 fail-open) can be exercised without a network.
_STUB_GATE = '''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["STUB_GATE_ARGV"], "w", encoding="utf-8") as handle:
    json.dump(sys.argv[1:], handle)
sys.stdout.write(os.environ.get("STUB_GATE_STDOUT", ""))
sys.stderr.write(os.environ.get("STUB_GATE_STDERR", ""))
sys.exit(int(os.environ.get("STUB_GATE_EXIT", "0")))
'''


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def hook_repo(tmp_path):
    """A real git repo wired to the real .githooks, with the Jira call stubbed.

    core.hooksPath is set so the hooks under test run as real processes
    during a real `git commit`, which is the only way to prove the feature
    actually fires in production.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo.parent, "init", "-q", str(repo))
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "KAN-181 Test")
    _git(repo, "config", "core.hooksPath", os.path.join(REPO_ROOT, ".githooks"))
    (repo / "scripts").mkdir()
    (repo / "scripts" / "jira_label_gate.py").write_text(_STUB_GATE, encoding="utf-8")
    (repo / "readme.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "readme.txt")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _commit(hook_repo, message, env_extra=None):
    """Run a real `git commit` and return the CompletedProcess."""
    env = dict(os.environ)
    env.setdefault("STUB_GATE_ARGV", str(hook_repo / "argv.json"))
    env.update(env_extra or {})
    # Keep the test hermetic: never let the developer's real .env or a stray
    # credential leak into the stubbed gate.
    env.pop("JIRA_API_TOKEN", None)
    env.pop("JIRA_EMAIL", None)
    return subprocess.run(
        ["git", "-C", str(hook_repo), "commit", "--allow-empty", "-m", message],
        capture_output=True, text=True, env=env,
    )


def _stub_argv(hook_repo):
    return json.loads((hook_repo / "argv.json").read_text(encoding="utf-8"))


def _hook_output(result):
    """git relays hook stdout to stderr; check both."""
    return (result.stdout or "") + (result.stderr or "")


def _message_from_argv(hook_repo, argv):
    """Read the file the gate was pointed at, resolved against the repo root.

    git runs hooks with the repo top level as the working directory, so the
    gate resolves a relative COMMIT_EDITMSG path correctly; the test has to do
    the same to inspect it.
    """
    path = Path(argv[argv.index("--message-file") + 1])
    if not path.is_absolute():
        path = hook_repo / path
    return path.read_text(encoding="utf-8")


class TestCommitMsgHookPassesMessage:
    """commit-msg receives the real message file as $1; it must forward it."""

    def test_hook_forwards_the_commit_message(self, hook_repo):
        result = _commit(hook_repo, "[KAN-130] feat: unrelated telemetry retry budget")
        assert result.returncode == 0, result.stderr
        argv = _stub_argv(hook_repo)
        assert "check" in argv and "KAN-130" in argv
        assert "--message-file" in argv
        assert "unrelated telemetry retry budget" in _message_from_argv(hook_repo, argv)

    def test_hook_message_is_this_commit_not_a_stale_one(self, hook_repo):
        """The gate must see the message being committed, not COMMIT_EDITMSG.

        This is the KAN-181 defect in production shape: a stale key left in
        .git/COMMIT_EDITMSG from a previous commit satisfied the gate for an
        unrelated commit.
        """
        _commit(hook_repo, "[KAN-130] feat: unrelated telemetry retry budget")
        first = _message_from_argv(hook_repo, _stub_argv(hook_repo))
        _commit(hook_repo, "[KAN-999] feat: a completely different subject line")
        second_argv = _stub_argv(hook_repo)
        second = _message_from_argv(hook_repo, second_argv)
        assert "KAN-999" in second_argv
        assert "KAN-130" not in second_argv
        assert "completely different subject" in second
        assert second != first

    def test_hook_never_blocks_on_a_scope_warning(self, hook_repo):
        """A [WARN] scope mismatch must not fail the commit (exit 0 from gate)."""
        result = _commit(
            hook_repo,
            "[KAN-130] feat: unrelated telemetry retry budget",
            {"STUB_GATE_STDOUT": "[WARN] KAN-130 scope does not appear related.\n",
             "STUB_GATE_EXIT": "0"},
        )
        assert result.returncode == 0, result.stderr
        assert "unrelated telemetry retry budget" in _git(hook_repo, "log", "-1", "--format=%s")

    def test_hook_still_blocks_on_unlabeled_ticket(self, hook_repo):
        result = _commit(
            hook_repo,
            "[KAN-130] feat: unrelated telemetry retry budget",
            {"STUB_GATE_STDOUT": "[ERROR] KAN-130 has no agent-* label.\n",
             "STUB_GATE_EXIT": "1"},
        )
        assert result.returncode != 0
        assert "agent-* label" in _hook_output(result)
        assert "seed" == _git(hook_repo, "log", "-1", "--format=%s").strip()

    def test_hook_fails_open_without_jira_credentials(self, hook_repo):
        result = _commit(
            hook_repo,
            "[KAN-130] feat: unrelated telemetry retry budget",
            {"STUB_GATE_STDOUT": "[WARN] credentials unavailable.\n",
             "STUB_GATE_EXIT": "2"},
        )
        assert result.returncode == 0, result.stderr
        assert "credentials unavailable" in _hook_output(result)

    def test_hook_does_not_edit_the_commit_message(self, hook_repo):
        """Read-only contract: commit-msg must never rewrite the message.

        Asserted on the COMMITTED message, which is the artifact a user sees.
        git legitimately rewrites .git/COMMIT_EDITMSG itself, so that file is
        not a valid probe; the committed body is.
        """
        message = "[KAN-130] feat: unrelated telemetry retry budget"
        _commit(hook_repo, message)
        body = _git(hook_repo, "log", "-1", "--format=%B").strip()
        assert body == message
        # The KAN-179 trailer belongs to prepare-commit-msg, never to this gate.
        assert "Test-Baseline:" not in body
        body_text = Path(COMMIT_MSG_HOOK).read_text(encoding="utf-8")
        assert "never edits the commit message" in body_text
        assert "commit_msg_trailer.py" not in body_text


class TestPreCommitHookResolvesMessageFile:
    """pre-commit hardcoded .git/COMMIT_EDITMSG, which is a FILE in a worktree.

    In a linked worktree .git is a gitfile, so `.git/COMMIT_EDITMSG` never
    resolves and the whole gate silently no-ops. `git rev-parse --git-path` is
    the only form that works in both a normal clone and a worktree.
    """

    def test_hook_uses_git_path_not_a_hardcoded_dot_git(self):
        """The primary resolution must be rev-parse, not a literal path.

        A `.git/COMMIT_EDITMSG` fallback may remain (non-git contexts), so this
        pins that rev-parse is what actually decides the path.
        """
        body = Path(PRE_COMMIT_HOOK).read_text(encoding="utf-8")
        assert "rev-parse --git-path COMMIT_EDITMSG" in body
        first_assignment = body.index("COMMIT_MSG_FILE=")
        assert body[first_assignment:].lstrip().startswith(
            "COMMIT_MSG_FILE=$(git rev-parse --git-path COMMIT_EDITMSG"
        )

    def test_pre_commit_resolves_the_real_path_in_a_worktree(self, tmp_path):
        main_repo = tmp_path / "main"
        main_repo.mkdir()
        _git(tmp_path, "init", "-q", str(main_repo))
        _git(main_repo, "config", "user.email", "t@example.invalid")
        _git(main_repo, "config", "user.name", "T")
        (main_repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(main_repo, "add", "seed.txt")
        _git(main_repo, "commit", "-q", "-m", "seed")
        worktree = tmp_path / "wt"
        _git(main_repo, "worktree", "add", "-q", str(worktree), "-b", "wtbranch")

        # In a worktree .git is a file, which is what breaks the hardcoded path.
        assert (worktree / ".git").is_file()

        editmsg = Path(_git(worktree, "rev-parse", "--git-path", "COMMIT_EDITMSG").strip())
        if not editmsg.is_absolute():
            editmsg = worktree / editmsg
        editmsg.parent.mkdir(parents=True, exist_ok=True)
        editmsg.write_text("[KAN-130] unrelated telemetry retry budget\n", encoding="utf-8")

        (worktree / "scripts").mkdir()
        (worktree / "scripts" / "jira_label_gate.py").write_text(_STUB_GATE, encoding="utf-8")
        env = dict(os.environ, STUB_GATE_ARGV=str(worktree / "argv.json"))
        result = subprocess.run(
            ["sh", str(PRE_COMMIT_HOOK)], cwd=str(worktree), capture_output=True,
            text=True, env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        argv = json.loads((worktree / "argv.json").read_text(encoding="utf-8"))
        assert "--message-file" in argv
        assert "unrelated telemetry retry budget" in Path(
            argv[argv.index("--message-file") + 1]
        ).read_text(encoding="utf-8")
