"""KAN-222: the provenance guard's branch-awareness is real behaviour, not a constant.

The `pre-rebase-kan214-wip` stash added `_dev_branch_skip_provenance` to
`scripts/test_provenance_guard.py` but never called it, so the feature was
dead code the tests could not see. These tests pin the behaviour it claims:

- a protected branch (main / master / release/*) always requires full
  provenance verification, no exceptions;
- an explicitly recognised dev branch (feat/*, fix/*, wip/*, experiment/*,
  review/*, draft/*, temp/*) may take the soft-guard path;
- ANY unrecognised branch name, including detached HEAD, is fail-closed.

The last one is the property that matters. A soft-guard keyed on "anything
that is not main" would let a typo'd or attacker-chosen branch name skip the
gate, so the allowlist has to be positive-matching and the default has to be
"require provenance".

Run: .venv/bin/python -m pytest tests/test_provenance_branch_guard.py -q
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "test_provenance_guard.py"


def _load_guard():
    """Import the guard script as a module.

    The guard lives in scripts/ and is not an installed package, so it is
    loaded by path. Importing the real module (rather than re-declaring the
    patterns here) is the point: a copy of the constants in this file would
    pass even if the guard's own copy were deleted.
    """
    spec = importlib.util.spec_from_file_location("_guard_under_test", GUARD)
    assert spec is not None and spec.loader is not None, "guard script must be importable"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeGit:
    """Stands in for the guard's _git() so branch name is controllable.

    Constructed to return whatever the test declares, never a real git
    invocation. Returns a valid completed process so the guard's
    `.stdout.strip()` call is exercised as it is in production.
    """

    def __init__(self, branch: str) -> None:
        self.branch = branch

    def __call__(self, *args: str, **kwargs: object) -> "subprocess.CompletedProcess[str]":  # type: ignore[name-defined]
        import subprocess

        assert "rev-parse" in args, f"unexpected git call: {args}"
        return subprocess.CompletedProcess(args=list(args), returncode=0, stdout=self.branch + "\n", stderr="")


@pytest.mark.parametrize(
    "branch",
    ["main", "master", "release/1.2", "release/2026-09"],
)
def test_protected_branches_never_skip_provenance(branch: str) -> None:
    guard = _load_guard()
    guard._git = _FakeGit(branch)
    assert guard._dev_branch_skip_provenance(ROOT) is False, (
        f"{branch!r} is a protected branch and must always require full provenance"
    )


@pytest.mark.parametrize(
    "branch",
    ["feat/kan-222", "fix/sandbox", "wip/scratch", "experiment/try", "review/pr-7", "draft/spec", "temp/one-off"],
)
def test_recognised_dev_branches_take_the_soft_guard(branch: str) -> None:
    guard = _load_guard()
    guard._git = _FakeGit(branch)
    assert guard._dev_branch_skip_provenance(ROOT) is True, (
        f"{branch!r} matches a declared dev pattern and should be soft-guarded"
    )


@pytest.mark.parametrize(
    "branch",
    [
        "HEAD",  # detached
        "mainline",  # a near-miss on "main" — must NOT be protected
        "feat",  # pattern without the "/" suffix
        "feat/",  # empty suffix
        "feature/kan-222",  # "feat/*" must not match "feature/*"
        "release",  # protected pattern without the "/" suffix
        "releasefoo/1",  # must not satisfy "release/*"
        "random-branch",
        "",
    ],
)
def test_unrecognised_branches_fail_closed(branch: str) -> None:
    """The security property: an unrecognised name requires provenance.

    If this ever returns True, any branch name not on the allowlist could
    opt out of the gate, which is the opposite of fail-closed.
    """
    guard = _load_guard()
    guard._git = _FakeGit(branch)
    assert guard._dev_branch_skip_provenance(ROOT) is False, (
        f"{branch!r} is not a declared dev branch and must fail closed"
    )


def test_dev_and_protected_patterns_do_not_overlap() -> None:
    guard = _load_guard()
    overlap = set(guard.PROTECTED_BRANCHES) & set(guard.DEV_BRANCH_PATTERNS)
    assert not overlap, f"a branch matching both lists would be ambiguous: {sorted(overlap)}"
