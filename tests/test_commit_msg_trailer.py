#!/usr/bin/env python3
"""Tests for the prepare-commit-msg Test-Baseline trailer helper -- KAN-179.

The helper appends `Test-Baseline: <sha>` ONLY when the baseline is provable.
It must never guess. Each test below names the contract it pins.
"""

import importlib.util
import json
import os
import subprocess

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "commit_msg_trailer.py")
HOOK_PATH = os.path.join(REPO_ROOT, ".githooks", "prepare-commit-msg")


def load_module():
    spec = importlib.util.spec_from_file_location("commit_msg_trailer", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def trailer():
    return load_module()


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "Tester")
    (r / "README.md").write_text("x\n")
    git(r, "add", "README.md")
    git(r, "commit", "-q", "-m", "init")
    return r


def write_manifest(repo, name, allowed_source_paths, *, parent=None):
    """Create + commit a manifest, return (relative_path, baseline_sha)."""
    parent = parent or git(repo, "rev-parse", "HEAD").stdout.strip()
    d = repo / "plans" / "test_provenance"
    d.mkdir(parents=True, exist_ok=True)
    rel = f"plans/test_provenance/{name}"
    (d / name).write_text(json.dumps({
        "schema_version": "test-provenance-v1",
        "ticket_id": f"TICKET-{name}",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [{"path": "tests/test_x.py", "sha256": "0" * 64}],
        "red_tests": [{"command": ["pytest"], "expected_exit": 1,
                       "failure_fingerprint": "boom"}],
        "allowed_source_paths": allowed_source_paths,
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "test fixture",
    }))
    git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", f"test(prov): freeze baseline for {name}")
    return rel, git(repo, "rev-parse", "HEAD").stdout.strip()


# --------------------------------------------------------------------------
# 1. Happy path, mirroring the real TDD flow:
#    RED commit freezes test+manifest (becomes baseline);
#    GREEN commit stages ONLY source -> trailer must be appended.
# --------------------------------------------------------------------------
def test_appends_trailer_for_source_commit_after_baseline(trailer, repo):
    _, baseline = write_manifest(repo, "t-001.json", ["scripts/foo.py"])

    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/foo.py")

    msg = "feat(core): implement foo"
    out, changed = trailer.append_trailer(repo, msg, None)

    assert changed is True
    assert f"Test-Baseline: {baseline}" in out
    assert out.rstrip().endswith(f"Test-Baseline: {baseline}")


# --------------------------------------------------------------------------
# 2. The RED commit itself stages test + manifest, no source => no trailer.
# --------------------------------------------------------------------------
def test_baseline_commit_itself_gets_no_trailer(trailer, repo):
    d = repo / "plans" / "test_provenance"
    d.mkdir(parents=True)
    (d / "t-002.json").write_text("{}")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("def test_ok():\n    assert True\n")
    git(repo, "add", "plans/test_provenance/t-002.json", "tests/test_x.py")

    msg = "test(prov): freeze baseline"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg


# --------------------------------------------------------------------------
# 3. No manifest governs these paths => byte-identical.
# --------------------------------------------------------------------------
def test_uncovered_source_path_is_untouched(trailer, repo):
    write_manifest(repo, "t-003.json", ["scripts/foo.py"])
    (repo / "scripts").mkdir()
    (repo / "scripts" / "unrelated.py").write_text("X = 1\n")
    git(repo, "add", "scripts/unrelated.py")

    msg = "feat(core): implement unrelated"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg


# --------------------------------------------------------------------------
# 4. AMBIGUITY: two manifests both allow the path => refuse to guess.
# --------------------------------------------------------------------------
def test_ambiguous_two_manifests_is_untouched(trailer, repo):
    write_manifest(repo, "t-004a.json", ["scripts/"])
    write_manifest(repo, "t-004b.json", ["scripts/foo.py"])
    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/foo.py")

    msg = "feat(core): implement foo"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg


# --------------------------------------------------------------------------
# 5. Docs-only commit is skipped even with a governing manifest present.
# --------------------------------------------------------------------------
def test_docs_only_commit_is_skipped(trailer, repo):
    write_manifest(repo, "t-005.json", ["scripts/"])
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("# doc\n")
    git(repo, "add", "docs/guide.md")

    msg = "docs(KAN-1): update guide"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg


# --------------------------------------------------------------------------
# 6. Already-present trailer is never duplicated.
# --------------------------------------------------------------------------
def test_existing_trailer_is_not_duplicated(trailer, repo):
    _, baseline = write_manifest(repo, "t-006.json", ["scripts/foo.py"])
    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 2\n")
    git(repo, "add", "scripts/foo.py")

    msg = f"feat(core): implement foo\n\nTest-Baseline: {baseline}"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg
    assert out.count("Test-Baseline:") == 1


# --------------------------------------------------------------------------
# 7. Merge / release / governance / build subjects are skipped.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("subject", [
    "Merge pull request #123 from pphothidaen/branch",
    "feat(release): v1.2.3",
    "docs(release): publish notes",
    "docs(governance): update rule",
    "fix(governance): harden gate",
    "build(hf): package",
    'Revert "bad commit"',
    "fixup! feat(core): something",
])
def test_release_and_merge_subjects_are_skipped(trailer, repo, subject):
    write_manifest(repo, "t-007.json", ["scripts/foo.py"])
    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/foo.py")

    out, changed = trailer.append_trailer(repo, subject, None)
    assert changed is False
    assert out == subject


# --------------------------------------------------------------------------
# 8. Manifest with MULTIPLE add-commits => baseline ambiguous => no-op.
# --------------------------------------------------------------------------
def test_multiple_add_commits_is_ambiguous_and_untouched(trailer, repo):
    d = repo / "plans" / "test_provenance"
    d.mkdir(parents=True)
    rel = "plans/test_provenance/t-008.json"
    (d / "t-008.json").write_text(json.dumps({
        "allowed_source_paths": ["scripts/foo.py"],
    }))
    git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", "test(prov): add manifest")
    # Remove and re-add so git reports two add-commits for the same path.
    git(repo, "rm", "-q", rel)
    git(repo, "commit", "-q", "-m", "chore: drop manifest")
    d.mkdir(parents=True, exist_ok=True)
    (d / "t-008.json").write_text(json.dumps({
        "allowed_source_paths": ["scripts/foo.py"],
    }))
    git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", "test(prov): re-add manifest")

    adds = git(repo, "log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split()
    assert len(adds) == 2, "fixture must produce two add-commits"

    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/foo.py")

    msg = "feat(core): implement foo"
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is False
    assert out == msg


# --------------------------------------------------------------------------
# 9. Trailing-newline handling must not corrupt the message.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("suffix", ["", "\n", "\n\n"])
def test_trailing_newline_variants(trailer, repo, suffix):
    _, baseline = write_manifest(repo, f"t-009-{len(suffix)}.json", ["scripts/foo.py"])
    (repo / "scripts").mkdir()
    (repo / "scripts" / "foo.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/foo.py")

    msg = "feat(core): implement foo" + suffix
    out, changed = trailer.append_trailer(repo, msg, None)
    assert changed is True
    assert f"Test-Baseline: {baseline}" in out
    # Original text preserved verbatim, trailer appended at the end.
    assert out.startswith(msg.rstrip("\n"))
    assert out.rstrip().endswith(f"Test-Baseline: {baseline}")


# --------------------------------------------------------------------------
# 10. The hook is installed, executable, and delegates to the helper.
# --------------------------------------------------------------------------
def test_prepare_commit_msg_hook_is_installed():
    assert os.path.exists(HOOK_PATH), f"missing hook: {HOOK_PATH}"
    assert os.access(HOOK_PATH, os.X_OK), f"hook not executable: {HOOK_PATH}"
    body = open(HOOK_PATH, encoding="utf-8").read()
    assert "commit_msg_trailer.py" in body
    assert "--message-file" in body


# --------------------------------------------------------------------------
# 12. END-TO-END (the bug unit tests missed): a real `git commit` inside this
#     repo must actually gain the trailer. A previous implementation was a
#     SILENT no-op -- the helper returned None, the hook exited 0, and the
#     commit looked successful while carrying no trailer at all.
# --------------------------------------------------------------------------
def test_end_to_end_real_commit_gains_trailer(trailer, repo):
    """Drive the real helper through a real commit sequence."""
    _, baseline = write_manifest(repo, "e2e-001.json", ["scripts/thing.py"])

    (repo / "scripts").mkdir()
    (repo / "scripts" / "thing.py").write_text("VALUE = 1\n")
    git(repo, "add", "scripts/thing.py")

    # This is exactly what prepare-commit-msg does: read the message file,
    # rewrite it, then commit. If the helper no-ops, the message is unchanged.
    msg_file = repo / ".git" / "COMMIT_EDITMSG"
    msg_file.write_text("feat(core): implement thing\n")
    out, changed = trailer.append_trailer(repo, msg_file.read_text(), "message")
    msg_file.write_text(out)

    assert changed is True, "helper no-op'd: this is the silent-no-op regression"
    assert f"Test-Baseline: {baseline}" in msg_file.read_text()

    res = git(repo, "commit", "-q", "-F", str(msg_file))
    body = git(repo, "log", "-1", "--pretty=%B").stdout
    assert f"Test-Baseline: {baseline}" in body, (
        f"committed message lost the trailer:\n{body}"
    )


# --------------------------------------------------------------------------
# 13. The hook must WARN (not silently exit 0) when the helper is missing.
# --------------------------------------------------------------------------
def test_hook_warns_when_helper_missing(tmp_path):
    """A shared core.hooksPath must not turn this into a silent no-op."""
    fake_repo = tmp_path / "other"
    fake_repo.mkdir()
    git(fake_repo, "init", "-q", "-b", "main")
    git(fake_repo, "config", "user.email", "t@example.com")
    git(fake_repo, "config", "user.name", "T")
    (fake_repo / "README.md").write_text("x\n")
    git(fake_repo, "add", "README.md")
    git(fake_repo, "commit", "-q", "-m", "init")

    msg = fake_repo / ".git" / "COMMIT_EDITMSG"
    msg.write_text("feat(core): something\n")
    before = msg.read_text()

    res = subprocess.run(
        ["sh", HOOK_PATH, str(msg), "message"],
        cwd=str(fake_repo), capture_output=True, text=True,
    )
    assert res.returncode == 0, "hook must never block a commit"
    assert "WARN" in res.stdout, (
        f"missing helper must warn, got stdout={res.stdout!r}"
    )
    assert msg.read_text() == before, "message must be untouched"


# --------------------------------------------------------------------------
# 14. commit-msg must REMAIN read-only -- KAN-179 must not break its contract.
# --------------------------------------------------------------------------
def test_commit_msg_hook_remains_read_only():
    body = open(os.path.join(REPO_ROOT, ".githooks", "commit-msg"), encoding="utf-8").read()
    assert "Read-only gate" in body
    assert "never edits the commit message" in body
    assert "commit_msg_trailer.py" not in body
