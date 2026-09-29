"""Tests for the pre-push TDD governance hook (.githooks/pre-push) — KAN-180.

Three defects are covered:

  (A) Interpreter selection: the hook must prefer the repository virtualenv
      (``.venv/bin/python3``) over a bare ``python3``, because the system
      interpreter is not guaranteed to carry the repo's dependencies
      (KAN-180 Defect A).
  (B) Documentation-only exemption: when every path changed across the commits
      being pushed is documentation, the test-provenance manifest requirement
      is waived. A docs-only commit has no test to freeze, so no honest
      manifest can exist (KAN-180 Defect B).
  (C) Per-commit coverage: every commit in the pushed range is validated, not
      only ``git log -1`` (KAN-180 Defect C).

The end-to-end tests execute the real hook with bash inside a throwaway git
repository and assert on observed exit codes and output. Static assertions on
the hook body are also present, but they are never treated as sufficient on
their own: a hook can satisfy every body assertion and still be a silent no-op
at runtime (this happened in a previous lane, where a script path was resolved
relative to ``$PWD`` instead of the repository root).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SOURCE = REPO_ROOT / ".githooks" / "pre-push"
_BASH = shutil.which("bash")
BASH = _BASH or "bash"

# Interpreter running this test session; its bin/ directory is injected into
# PATH for the sandbox so that tdd_gate.py can find `pytest`. Do NOT call
# .resolve() here: the repository .venv is a symlink, so resolving follows it
# to the bare uv interpreter, whose bin/ has no pytest.
SESSION_BIN = Path(sys.executable).parent

MANIFEST_GLOB = "plans/test_provenance/*kan-180*.json"

if _BASH is None:  # pragma: no cover - bash is present on every supported host
    pytest.skip("bash is required to execute the pre-push hook", allow_module_level=True)

# Shell utilities the hook body relies on; linked into restricted-PATH sandboxes.
HOOK_SHELL_TOOLS = ("git", "grep", "head", "sed", "printf", "sort", "uniq", "cat", "command")


def _link_tools(bindir: Path) -> None:
    """Expose the hook's shell dependencies in a minimal PATH directory."""
    for tool in HOOK_SHELL_TOOLS:
        found = shutil.which(tool)
        if not found:
            continue
        link = bindir / tool
        if not link.exists():
            link.symlink_to(found)


# ---------------------------------------------------------------------------
# Sandbox helpers
# ---------------------------------------------------------------------------
class Sandbox:
    """A throwaway git repository that executes the real pre-push hook."""

    def __init__(self, root: Path) -> None:
        self.root = root
        # Scratch space OUTSIDE the repository: a helper directory created
        # inside the worktree would be staged by `git add -A` and count as a
        # changed (non-documentation) path, defeating the exemption scenarios.
        self.outside = root.parent / f"{root.name}-scratch"
        self.outside.mkdir(parents=True, exist_ok=True)
        self.hook = root / ".githooks" / "pre-push"
        self.gate_log = root / "gate-invocations.log"
        (root / ".githooks").mkdir(parents=True, exist_ok=True)
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "tests").mkdir(parents=True, exist_ok=True)
        shutil.copy2(HOOK_SOURCE, self.hook)
        # Real gate + real gate tests, so the hook exercises production code.
        shutil.copy2(REPO_ROOT / "scripts" / "tdd_gate.py", root / "scripts" / "tdd_gate.py")
        shutil.copy2(REPO_ROOT / "tests" / "test_tdd_gate.py", root / "tests" / "test_tdd_gate.py")
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "kan180@example.invalid")
        self._git("config", "user.name", "KAN-180 Lane")
        self._git("config", "commit.gpgsign", "false")
        # The sandbox installs a fake .venv; it must never become a changed
        # path, or it would (correctly) defeat the documentation-only exemption.
        self.write(".gitignore", ".venv/\n")
        self.write("README.md", "# sandbox\n")
        self.seed = self.commit("chore: seed sandbox repository")

    # -- plumbing ---------------------------------------------------------
    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout.strip()

    def write(self, relpath: str, text: str) -> Path:
        target = self.root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "--allow-empty", "-m", message)
        return self._git("rev-parse", "HEAD")

    def install_fake_venv(self, log: Path | None = None) -> Path:
        """Create an executable .venv/bin/python3 that records its argv."""
        target = log or (self.outside / "venv-python.log")
        venv_python = self.root / ".venv" / "bin" / "python3"
        venv_python.parent.mkdir(parents=True, exist_ok=True)
        venv_python.write_text(
            "#!/bin/sh\n"
            f'printf "%s\\n" "$*" >> "{target}"\n'
            f'exec "{sys.executable}" "$@"\n',
            encoding="utf-8",
        )
        venv_python.chmod(0o755)
        return target

    def env(self, *, restrict_path: Path | None = None) -> dict[str, str]:
        env = dict(os.environ)
        path_entries = [str(SESSION_BIN)]
        if restrict_path is not None:
            path_entries = [str(restrict_path)]
        else:
            path_entries.append(env.get("PATH", ""))
        env["PATH"] = os.pathsep.join(p for p in path_entries if p)
        env["HOME"] = str(self.root)
        return env

    # Artifacts produced by the hook's own `pytest` invocation, not by the hook.
    _VOLATILE_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}

    def fingerprint(self) -> str:
        """Hash of every worktree file (git/pytest caches excluded): detects hook writes."""
        digest = hashlib.sha256()
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if self._VOLATILE_DIRS & set(rel.parts):
                continue
            digest.update(rel.as_posix().encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def run_hook(self, stdin: str = "", *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [BASH, str(self.hook)],
            cwd=str(self.root),
            input=stdin,
            capture_output=True,
            text=True,
            env=env or self.env(),
        )

    def ref_update(self, local_sha: str, remote_sha: str) -> str:
        return f"refs/heads/main {local_sha} refs/heads/main {remote_sha}\n"

    def add_manifest(self, ticket: str) -> str:
        return self.write(
            f"plans/test_provenance/ticket-{ticket}-sandbox-001.json",
            '{"schema_version": "test-provenance-v1"}\n',
        ).relative_to(self.root).as_posix()


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path / "repo")


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


# ---------------------------------------------------------------------------
# (A) Interpreter selection
# ---------------------------------------------------------------------------
def test_hook_never_invokes_a_bare_python3() -> None:
    """The gate must be invoked through a resolved interpreter, never `python3 x`."""
    body = HOOK_SOURCE.read_text(encoding="utf-8")
    assert "python3 scripts/tdd_gate.py" not in body
    assert re.search(r"python3\s+\"?\$\{?GATE_SCRIPT", body) is None
    # The gate is launched via the resolved $PYTHON variable, not a literal name.
    assert re.search(r'"\$\{?PYTHON\}?"\s+"?\$\{?GATE_SCRIPT\}?"', body) is not None
    # Interpreter selection is present and fail-open.
    assert ".venv/bin/python3" in body
    assert "command -v python3" in body


def test_prefers_repo_venv_interpreter_end_to_end(sandbox: Sandbox) -> None:
    """E2E: an executable .venv/bin/python3 is the interpreter actually used."""
    log = sandbox.install_fake_venv(sandbox.outside / "venv-python.log")
    head = sandbox.write("docs/notes.md", "notes\n")
    sha = sandbox.commit("docs(KAN-180): add notes")
    assert head

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert log.exists(), f"hook did not use the venv interpreter; output={_output(result)}"
    assert "scripts/tdd_gate.py" in log.read_text(encoding="utf-8")


def test_falls_back_to_system_python3_without_venv(sandbox: Sandbox) -> None:
    """E2E: with no .venv the hook must still run the gate via PATH python3."""
    marker = sandbox.outside / "system-python.log"
    bindir = sandbox.outside / "fakebin"
    bindir.mkdir(parents=True, exist_ok=True)
    shim = bindir / "python3"
    shim.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{marker}"\n'
        f'exec "{sys.executable}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    _link_tools(bindir)

    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    sha = sandbox.commit("fix(KAN-180): add source change")

    env = sandbox.env()
    env["PATH"] = os.pathsep.join([str(bindir), str(SESSION_BIN)])
    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed), env=env)

    assert marker.exists(), f"hook did not fall back to PATH python3; output={_output(result)}"
    assert "scripts/tdd_gate.py" in marker.read_text(encoding="utf-8")


def test_gate_finds_pytest_through_the_venv_bin_directory(sandbox: Sandbox) -> None:
    """E2E: tdd_gate.py shells out to a bare `pytest`, so the venv bin must be on PATH.

    Without the PATH fix the gate runs on the venv interpreter but collects
    tests with whatever `pytest` the caller's PATH exposes -- on this host the
    ambient `python3` is 3.9.6, which cannot even import `tomllib`.
    """
    # A venv that is a *complete* environment: interpreter plus its pytest.
    sandbox.install_fake_venv(sandbox.outside / "venv-python.log")
    linked = 0
    for tool in ("pytest", "py.test"):
        found = SESSION_BIN / tool
        if found.exists():
            (sandbox.root / ".venv" / "bin" / tool).symlink_to(found)
            linked += 1
    # Guard against a silently empty venv, which would make this test vacuous.
    assert linked > 0, f"no pytest found in {SESSION_BIN}; the scenario cannot be built"
    # A PATH with git/grep/head but NO python3 and NO pytest anywhere.
    bindir = sandbox.outside / "bare-bin"
    bindir.mkdir(parents=True, exist_ok=True)
    _link_tools(bindir)
    assert not list(bindir.glob("py*")), "the restricted PATH must not contain pytest"

    sandbox.write("docs/notes.md", "notes\n")
    sha = sandbox.commit("docs(KAN-180): documentation change")

    env = sandbox.env(restrict_path=bindir)
    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed), env=env)

    assert result.returncode == 0, _output(result)
    assert "command not found" not in _output(result)
    assert "waived" in _output(result)


def test_fails_open_with_warning_when_no_python_exists(sandbox: Sandbox) -> None:
    """E2E: no interpreter at all must warn and exit 0, never block the push."""
    bindir = sandbox.outside / "pythonless-bin"
    bindir.mkdir(parents=True, exist_ok=True)
    _link_tools(bindir)

    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    sha = sandbox.commit("fix(KAN-180): add source change")

    env = sandbox.env(restrict_path=bindir)
    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed), env=env)

    assert result.returncode == 0, _output(result)
    assert "Python is required" in _output(result)
    assert "skipped" in _output(result).lower()



# ---------------------------------------------------------------------------
# (B) Documentation-only exemption
# ---------------------------------------------------------------------------
def test_docs_only_push_is_waived_and_gate_still_runs(sandbox: Sandbox) -> None:
    """E2E: docs-only range passes, and the gate is genuinely executed."""
    sandbox.write("docs/runbook.md", "# runbook\n")
    sha = sandbox.commit("docs(KAN-180): document the runbook")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 0, _output(result)
    out = _output(result)
    # Proof of life: the gate was executed and its verdict consumed.
    assert "TRANSITION APPROVED" in out or "waived" in out
    assert "Missing test provenance manifest" not in out


def test_docs_only_push_still_requires_manifest_when_one_exists_but_tests_fail(
    sandbox: Sandbox,
) -> None:
    """A docs-only range with a failing test suite must still be rejected."""
    sandbox.write("tests/test_tdd_gate.py", "def test_forced_failure():\n    assert False\n")
    sandbox.write("docs/runbook.md", "# runbook\n")
    sha = sandbox.commit("docs(KAN-180): document the runbook")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 1, _output(result)
    assert "requires all tests to pass" in _output(result)


@pytest.mark.parametrize(
    "doc_path",
    [
        "docs/nested/deep/design.md",
        "plans/adr/0001-decision.md",
        ".agents/LESSONS_LEARNED.md",
        ".agy/notes.md",
        ".antigravity/notes.md",
        ".claude/notes.md",
        ".codex/notes.md",
        ".github/workflows/ci.yml",
        "HANDOFF.md",
        "docs/notes.txt",
        "plans/adr/diagram.svg",
    ],
)
def test_documentation_path_variants_are_exempt(sandbox: Sandbox, doc_path: str) -> None:
    """Every documented documentation path family is treated as documentation."""
    sandbox.write(doc_path, "content\n")
    sha = sandbox.commit("docs(KAN-180): documentation change")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 0, _output(result)
    assert "waived" in _output(result)


@pytest.mark.parametrize(
    "material_path",
    [
        "scripts/feature.py",
        "project/app.py",
        "docsite/notes.txt",
        "tools/agent-broker/Package.swift",
        "configs/feature.toml",
    ],
)
def test_any_non_documentation_path_keeps_the_manifest_requirement(
    sandbox: Sandbox, material_path: str
) -> None:
    """One non-doc path anywhere in the range re-imposes the strict behaviour."""
    sandbox.write("docs/notes.md", "notes\n")
    sandbox.write(material_path, "content\n")
    sha = sandbox.commit("fix(KAN-180): mixed change")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 1, _output(result)
    assert "Missing test provenance manifest" in _output(result)


def test_mixed_range_is_strict_even_when_head_commit_is_docs_only(sandbox: Sandbox) -> None:
    """Exemption is decided on the whole range, not on the tip commit alone."""
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    mid = sandbox.commit("fix(KAN-180): add source change")
    sandbox.write("docs/notes.md", "notes\n")
    head = sandbox.commit("docs(KAN-180): document the source change")

    result = sandbox.run_hook(sandbox.ref_update(head, sandbox.seed))

    assert result.returncode == 1, _output(result)
    assert "Missing test provenance manifest" in _output(result)


def test_material_change_passes_once_a_manifest_exists(sandbox: Sandbox) -> None:
    """The strict path is preserved: with a manifest the gate approves."""
    sandbox.add_manifest("kan-180")
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    sha = sandbox.commit("fix(KAN-180): add source change")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 0, _output(result)
    assert "TRANSITION APPROVED" in _output(result)


# ---------------------------------------------------------------------------
# (C) Per-commit coverage across the pushed range
# ---------------------------------------------------------------------------
def test_earlier_commit_in_range_is_validated(sandbox: Sandbox) -> None:
    """A mid-range commit lacking a manifest blocks the push, not just the tip."""
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    mid = sandbox.commit("fix(KAN-111): first source change")
    sandbox.add_manifest("kan-180")
    head = sandbox.commit("fix(KAN-180): second source change")

    result = sandbox.run_hook(sandbox.ref_update(head, sandbox.seed))

    assert result.returncode == 1, _output(result)
    assert "KAN-111" in _output(result)


def test_every_commit_with_a_manifest_passes(sandbox: Sandbox) -> None:
    """All commits in the range are satisfied, so the push is allowed."""
    sandbox.add_manifest("kan-111")
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    sandbox.commit("fix(KAN-111): first source change")
    sandbox.add_manifest("kan-180")
    sandbox.write("scripts/other.py", "OTHER = 2\n")
    head = sandbox.commit("fix(KAN-180): second source change")

    result = sandbox.run_hook(sandbox.ref_update(head, sandbox.seed))

    assert result.returncode == 0, _output(result)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_ref_deletion_is_ignored(sandbox: Sandbox) -> None:
    """A zero local SHA (branch deletion) must not run or block the gate."""
    zero = "0" * 40
    result = sandbox.run_hook(sandbox.ref_update(zero, sandbox.seed))

    assert result.returncode == 0, _output(result)
    assert "Missing test provenance manifest" not in _output(result)


def test_head_fallback_without_ref_input_stays_strict(sandbox: Sandbox) -> None:
    """With no ref range on stdin the hook validates HEAD without exemption."""
    sandbox.write("docs/notes.md", "notes\n")
    sandbox.commit("docs(KAN-180): documentation change")

    result = sandbox.run_hook(stdin="")

    assert result.returncode == 1, _output(result)
    assert "Missing test provenance manifest" in _output(result)


def test_hook_is_syntactically_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(HOOK_SOURCE)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_hook_never_writes_to_the_repository(sandbox: Sandbox) -> None:
    """The gate stays read-only: the sandbox is byte-identical after a run."""
    sandbox.write("docs/notes.md", "notes\n")
    sha = sandbox.commit("docs(KAN-180): documentation change")
    before = sandbox.fingerprint()

    sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert sandbox.fingerprint() == before


def test_hook_ignores_commits_without_a_ticket_key(sandbox: Sandbox) -> None:
    """Commit messages with no KAN key keep the pre-existing skip behaviour."""
    sandbox.write("scripts/feature.py", "VALUE = 1\n")
    sha = sandbox.commit("chore: unticketed source change")

    result = sandbox.run_hook(sandbox.ref_update(sha, sandbox.seed))

    assert result.returncode == 0, _output(result)
