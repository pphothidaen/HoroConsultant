"""Behaviour-matrix pins for the pre-push gate range computation — KAN-257.

Companion to ``tests/test_pre_push_hook.py`` (whose content is frozen by the
KAN-257 review contract and therefore must not gain new cases). The tests here
pin the remaining cells of the range-computation behaviour matrix that the
existing suite does not cover:

  * force-push rewind (remote_sha valid, local_sha an ancestor of it) must
    validate the pushed tip instead of silently free-passing;
  * multi-ref pushes keep accumulating one range per ref;
  * a new-branch push whose tip IS the repository root seed commit still
    resolves a range (the ``<root>^`` caret form is unresolvable, which is
    the root cause of the KAN-257 silent no-op).

The end-to-end tests execute the real hook with bash inside a throwaway git
repository, exactly like ``tests/test_pre_push_hook.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_pre_push_hook import Sandbox, _output

ZERO_SHA = "0" * 40


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path / "repo")


def test_force_push_rewind_validates_the_pushed_tip(sandbox: Sandbox) -> None:
    """A rewind must not become a free pass.

    For a rewind the ``remote..local`` range is empty (local is an ancestor
    of remote), which used to leave NEW_COMMITS empty and made the gate exit
    0 having validated nothing. The gate must validate the tip that is about
    to become the remote head instead. Enforcement stays bounded by design:
    the hook is a read-only gate, and the hard boundary is CI plus the DoD
    production gate on main.
    """
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    rewind_target = sandbox.commit("fix(KAN-250): commit the branch is rewound onto")
    sandbox.write("scripts/other.py", "OTHER = 2\n")
    sandbox.commit("fix(KAN-251): commit being rewound away from")

    # Rewind: local_sha (KAN-250) is an ancestor of remote_sha (KAN-251 tip).
    result = sandbox.run_hook(sandbox.ref_update(rewind_target, sandbox._git("rev-parse", "HEAD")))

    out = _output(result)
    assert "Checking TDD governance and provenance for KAN-250" in out, out
    assert result.returncode == 1, out  # no manifest for KAN-250
    assert "Missing test provenance manifest" in out


def test_force_push_rewind_with_manifest_passes(sandbox: Sandbox) -> None:
    """The rewind validation is a genuine gate, not a trap: it can approve."""
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    rewind_target = sandbox.commit("fix(KAN-250): commit the branch is rewound onto")
    sandbox.add_manifest("kan-250")
    sandbox.write("scripts/other.py", "OTHER = 2\n")
    sandbox.commit("fix(KAN-251): commit being rewound away from")

    result = sandbox.run_hook(sandbox.ref_update(rewind_target, sandbox._git("rev-parse", "HEAD")))

    out = _output(result)
    assert "Checking TDD governance and provenance for KAN-250" in out, out
    assert result.returncode == 0, out
    assert "TRANSITION APPROVED" in out


def test_multi_ref_push_accumulates_one_range_per_ref(sandbox: Sandbox) -> None:
    """Both refs of a multi-ref push contribute their commits to the gate."""
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    side_tip = sandbox.commit("fix(KAN-310): commit on the side branch")
    sandbox._git("branch", "side")
    sandbox.write("scripts/other.py", "OTHER = 2\n")
    main_tip = sandbox.commit("fix(KAN-311): commit on main")

    stdin = (
        f"refs/heads/main {main_tip} refs/heads/main {sandbox.seed}\n"
        f"refs/heads/side {side_tip} refs/heads/side {ZERO_SHA}\n"
    )
    result = sandbox.run_hook(stdin)

    out = _output(result)
    assert "Checking TDD governance and provenance for KAN-310" in out, out
    assert "Checking TDD governance and provenance for KAN-311" in out, out
    assert result.returncode == 1, out  # no manifests for either ticket


def test_new_branch_push_of_the_root_seed_commit_resolves_a_range(sandbox: Sandbox) -> None:
    """A new-branch push whose tip IS the root commit must not silently no-op.

    The KAN-257 root cause: the fallback range ``<oldest-unpushed>^..<head>``
    is fatal when the oldest unpublished commit is the repository root seed
    commit (``<root>^`` does not resolve), the error was swallowed, and the
    gate exited 0 having validated nothing. The seed commit carries no KAN
    key, so the pinned behaviour here is that the push resolves cleanly and
    the pre-existing key-less bypass keeps skipping it (exit 0, no checks) —
    the range must resolve, not the bypass widen.
    """
    zero = "0" * 40
    result = sandbox.run_hook(sandbox.ref_update(sandbox.seed, zero))

    out = _output(result)
    assert "Checking TDD governance" not in out, out  # seed has no KAN key
    assert result.returncode == 0, out
    assert "Missing test provenance manifest" not in out
