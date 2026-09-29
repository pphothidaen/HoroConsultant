#!/usr/bin/env python3
"""Adversarial regression tests for the KAN-179 Test-Baseline trailer helper.

These tests exist because the previous suite passed 22/22 while the helper was
BROKEN in three ways. Every defect below was reproduced against the REAL
scripts/test_provenance_guard.py, not against a mock:

  D1  A commit message WITH A BODY gets the trailer GLUED onto the last line
      ("...Ticket: KAN-179Test-Baseline: <sha>"). Every pre-existing fixture
      used a SUBJECT-ONLY message, so the bug was invisible. The guard reads
      the message as a set of stripped lines and compares for an EXACT line, so
      a glued trailer is invisible to it -> SOURCE_COMMIT_MISSING_BASELINE_TRAILER.

  D2  The helper triggers on "ANY staged source path is allowed", but the guard
      requires that when a commit CARRIES the trailer, EVERY non-test path in
      that commit is inside allowed_source_paths. A commit mixing an allowed
      source with a docs/ or unlisted source file therefore gets a trailer that
      makes the guard emit SOURCE_PATH_OUTSIDE_MANIFEST. The helper manufactures
      a failing commit.

  D3  The helper's BYPASS_SUBJECT_PREFIXES skips Revert/fixup!/squash!/amend!,
      but the guard's is_release_or_gov list does NOT exempt them. Those commits
      are silently left without a trailer and then fail
      SOURCE_COMMIT_MISSING_BASELINE_TRAILER. The helper must never suppress a
      trailer the guard actually demands.

The oracle here is the real guard. Tests assert helper/guard AGREEMENT.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "commit_msg_trailer.py")
GUARD_PATH = os.path.join(REPO_ROOT, "scripts", "test_provenance_guard.py")


def load_helper():
    spec = importlib.util.spec_from_file_location("cmt_regression", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["cmt_regression"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def helper():
    return load_helper()


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null"},
    )


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def guard_verify(repo, manifest_rel):
    """Run the REAL provenance guard and return its parsed report."""
    res = subprocess.run(
        [sys.executable, GUARD_PATH, "verify", "--repo", str(repo),
         "--manifest", manifest_rel],
        capture_output=True, text=True,
    )
    return json.loads(res.stdout)


def build_repo(tmp_path, allowed_source_paths, *, manifest_name="t-reg-001.json"):
    """A repo with a real committed baseline: seed -> (test+manifest) -> HEAD.

    Returns (repo, manifest_rel, baseline_sha). HEAD is the baseline commit, so
    a subsequent source commit is exactly the GREEN commit the guard governs.
    """
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")

    (r / "seed.txt").write_text("seed\n")
    git(r, "add", "seed.txt")
    git(r, "commit", "-q", "-m", "chore: seed")
    parent = git(r, "rev-parse", "HEAD").stdout.strip()

    (r / "tests").mkdir()
    (r / "tests" / "test_x.py").write_text("def test_ok():\n    assert True\n")
    rel = f"plans/test_provenance/{manifest_name}"
    d = r / "plans" / "test_provenance"
    d.mkdir(parents=True)
    (d / manifest_name).write_text(json.dumps({
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-KAN-179-REG",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [{"path": "tests/test_x.py",
                        "sha256": sha256_file(r / "tests" / "test_x.py")}],
        "red_tests": [{"command": ["pytest"], "expected_exit": 1,
                       "failure_fingerprint": "boom"}],
        "allowed_source_paths": list(allowed_source_paths),
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "regression fixture",
    }, indent=2))
    git(r, "add", "tests/test_x.py", rel)
    git(r, "commit", "-q", "-m", "test(prov): freeze baseline\n\nTicket: KAN-179")
    return r, rel, git(r, "rev-parse", "HEAD").stdout.strip()


def stage_files(repo, files):
    for path, content in files.items():
        p = repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    git(repo, "add", "-A")


def commit_via_helper(helper, repo, subject, body_lines):
    """Run the REAL helper and commit its output VERBATIM.

    Committing the helper's own bytes is the point: it lets the formatting and
    decision bugs reach the real guard instead of hiding behind a mock.
    """
    message = subject + "\n"
    if body_lines:
        message += "\n" + "\n".join(body_lines) + "\n"
    message += "\nTicket: KAN-179\n"

    out, changed = helper.append_trailer(repo, message, "message")
    (repo / ".git" / "COMMIT_EDITMSG").write_text(out)
    res = git(repo, "commit", "-q", "-F", ".git/COMMIT_EDITMSG")
    assert res.returncode == 0, res.stderr
    return changed, git(repo, "log", "-1", "--pretty=%B").stdout


# ---------------------------------------------------------------------------
# D1 -- a message WITH A BODY must still yield an exact, standalone trailer line
# ---------------------------------------------------------------------------
def test_d1_body_message_trailer_is_its_own_exact_line(helper, tmp_path):
    """The core regression: a body-bearing message must not glue the trailer."""
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    msg = ("feat(core): implement foo\n"
           "\n"
           "This change wires the foo module into the pipeline.\n"
           "Second line of body prose.\n"
           "\n"
           "Ticket: KAN-179\n")
    out, changed = helper.append_trailer(repo, msg, "message")

    assert changed is True, "helper must append the trailer for a provable baseline"
    lines = out.splitlines()
    assert f"Test-Baseline: {baseline}" in lines, (
        "trailer must be an EXACT standalone line, as the guard compares whole "
        f"stripped lines. Got:\n{out!r}"
    )
    # The body must survive verbatim and not be corrupted.
    assert "This change wires the foo module into the pipeline." in lines
    assert "Second line of body prose." in lines
    assert "Ticket: KAN-179" in lines


def test_d1_body_message_glue_breaks_the_real_guard(helper, tmp_path):
    """End-to-end oracle: commit the helper's REAL output, let the guard judge."""
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    subject = "feat(core): implement foo"
    body = ["This change wires the foo module into the pipeline.",
            "Second line of body prose."]
    _changed, committed = commit_via_helper(
        helper, repo, subject, body)

    report = guard_verify(repo, rel)
    assert report["status"] == "PASSED", (
        "the guard rejected a commit the helper called successful.\n"
        f"issues={[i['code'] for i in report['issues']]}\n"
        f"committed message:\n{committed}"
    )
    assert f"Test-Baseline: {baseline}" in [
        ln.strip() for ln in committed.splitlines()
    ]


def test_d1_subject_only_message_still_works(helper, tmp_path):
    """Control: the previously-tested subject-only shape must keep working."""
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    out, changed = helper.append_trailer(repo, "feat(core): implement foo", "message")
    assert changed is True
    assert f"Test-Baseline: {baseline}" in out.splitlines()


# ---------------------------------------------------------------------------
# D2 -- never attach a trailer the guard will reject as OUTSIDE_MANIFEST
# ---------------------------------------------------------------------------
def test_d2_no_trailer_when_a_docs_file_shares_the_commit(helper, tmp_path):
    repo, rel, _ = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "V=1\n", "docs/guide.md": "# guide\n"})

    msg = "feat(core): implement foo\n\nBody.\n"
    out, changed = helper.append_trailer(repo, msg, "message")

    assert changed is False, (
        "helper attached a trailer, but the guard requires EVERY non-test path in "
        "a trailer-carrying commit to be inside allowed_source_paths; docs/guide.md "
        "is not, so the commit would fail SOURCE_PATH_OUTSIDE_MANIFEST.\n"
        f"got:\n{out!r}"
    )
    assert out == msg


def test_d2_no_trailer_when_an_unlisted_source_file_shares_the_commit(helper, tmp_path):
    repo, rel, _ = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "V=1\n", "scripts/bar.py": "W=1\n"})

    msg = "feat(core): implement foo\n\nBody.\n"
    out, changed = helper.append_trailer(repo, msg, "message")

    assert changed is False, (
        "scripts/bar.py is outside allowed_source_paths; attaching the trailer "
        "would make the guard emit SOURCE_PATH_OUTSIDE_MANIFEST.\n"
        f"got:\n{out!r}"
    )
    assert out == msg


def test_d2_docs_mix_guard_agrees_with_helper(helper, tmp_path):
    """Oracle: the helper must not hand the guard a trailer it cannot back up.

    This commit is unfixable by a trailer either way -- the manifest allowlist
    does not cover docs/guide.md, so the commit needs a manifest amendment. The
    helper's job is to stay silent rather than assert a baseline it cannot
    fully back, which would convert a MISSING_TRAILER report into a strictly
    worse SOURCE_PATH_OUTSIDE_MANIFEST report.
    """
    repo, rel, _ = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "V=1\n", "docs/guide.md": "# guide\n"})

    commit_via_helper(helper, repo, "feat(core): implement foo", ["Body."])
    report = guard_verify(repo, rel)
    # The commit legitimately needs no baseline (no single manifest covers it),
    # so the guard must not be handed a bogus trailer.
    assert "SOURCE_PATH_OUTSIDE_MANIFEST" not in [
        i["code"] for i in report["issues"]
    ], [i["message"] for i in report["issues"]]


# ---------------------------------------------------------------------------
# D3 -- the bypass list must not suppress a trailer the guard demands
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("subject", [
    'Revert "feat(core): implement foo"',
    "fixup! feat(core): implement foo",
    "squash! feat(core): implement foo",
    "amend! feat(core): implement foo",
])
def test_d3_bypass_subjects_still_get_a_trailer_the_guard_wants(helper, tmp_path,
                                                               subject):
    """The guard does NOT exempt these subjects, so the helper must not skip."""
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    out, changed = helper.append_trailer(repo, subject + "\n\nBody.\n", "message")

    assert changed is True, (
        f"helper suppressed the trailer for {subject!r}, but the guard's "
        "is_release_or_gov list does not exempt it, so the commit would fail "
        "SOURCE_COMMIT_MISSING_BASELINE_TRAILER."
    )
    assert f"Test-Baseline: {baseline}" in out.splitlines()


def test_d3_bypass_list_matches_the_guard_exemption_list(helper):
    """The helper's bypass prefixes must be a SUBSET of the guard's exempt list.

    A helper-only prefix means "helper stays silent where the guard still
    demands a trailer" -- a guaranteed future failure.
    """
    guard_src = open(GUARD_PATH, encoding="utf-8").read()
    guard_exempt = set()
    for line in guard_src.splitlines():
        stripped = line.strip().strip(",").strip('"').strip("'")
        if stripped in ("feat(release):", "docs(release):", "docs(governance):",
                        "fix(governance):", "build(hf):", "merge:", "Merge"):
            guard_exempt.add(stripped)
    assert guard_exempt, "failed to parse the guard's exemption list"

    extra = set(helper.BYPASS_SUBJECT_PREFIXES) - guard_exempt
    assert not extra, (
        f"helper bypasses subjects the guard does NOT exempt: {sorted(extra)}. "
        "Each one produces a silent no-op the guard then rejects."
    )


# ---------------------------------------------------------------------------
# D4 -- an UNRELATED prose mention of "Test-Baseline:" must not disable the hook
# ---------------------------------------------------------------------------
def test_d4_body_prose_mention_does_not_suppress_the_trailer(helper, tmp_path):
    """should_skip() must only honour a REAL trailer line, not a prose mention.

    A body that documents the trailer format -- e.g. a template with a literal
    "<sha>" placeholder -- is prose, not a trailer. The old prefix-only check
    treated any line starting with "Test-Baseline:" as an existing trailer, so
    documenting the format silently disabled the hook.

    A line carrying a real 40-char SHA IS a genuine existing trailer and must
    still be respected, so the two cases are asserted separately below.
    """
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    msg = ("feat(core): implement foo\n"
           "\n"
           "The guard reads the baseline from the trailer block.\n"
           "Test-Baseline: <sha>\n"
           "That line above is a template placeholder, not a real trailer.\n")
    out, changed = helper.append_trailer(repo, msg, "message")

    assert changed is True, (
        "a prose mention of the trailer format silently disabled the helper"
    )
    assert f"Test-Baseline: {baseline}" in [
        ln.strip() for ln in out.splitlines()
    ]


def test_d4_real_existing_trailer_is_still_respected(helper, tmp_path):
    """Control for D4: a genuine trailer must NOT be duplicated."""
    repo, rel, baseline = build_repo(tmp_path, ["scripts/foo.py"])
    stage_files(repo, {"scripts/foo.py": "VALUE = 1\n"})

    msg = f"feat(core): implement foo\n\nTest-Baseline: {baseline}\n"
    out, changed = helper.append_trailer(repo, msg, "message")

    assert changed is False, "a real existing trailer must suppress a duplicate"
    assert out == msg
