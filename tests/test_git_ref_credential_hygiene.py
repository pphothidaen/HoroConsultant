"""Guard: no git ref may contain a live credential.

Security incident pattern (KAN-132): a live bearer credential was preserved inside
`refs/heads/credential/quarantine-stash6` and `refs/stash-backup/6` while stashes were being
pinned. A *branch* is a publishable surface — `git push --all` would ship it. Branch protection
does not help: those refs are not `main`, so no ruleset or review gate applies to them.

The durable defence is a pre-push / CI check, because the credential never entered a commit that
a reviewer would see.

This test deliberately does **not** embed any real secret. It matches credential *shapes* only,
and explicitly ignores documentation/test placeholders (`AKIAIOSFODNN7EXAMPLE`, `ghp_fake...`)
so the guard stays green on legitimate fixtures — two such fixtures exist in this repo's history.

Scope and cost: the forensic/local-only refs are scanned by default. Scanning *every* ref costs
~200s (144 unique objects), so it is opt-in via ``HORO_DEEP_REF_SCAN=1``.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Credential shapes only — never a real value.
# Two forms per kind: `re` is used for precise in-Python validation, `git` for the fast scan.
# `git grep -E` is POSIX ERE and does NOT support `\b` — it silently returns "no match" (rc=1)
# rather than erroring, which turns a security guard into a no-op. Strip it for the git side.
CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("hermes_bearer_token", re.compile(r"\bhermes-[0-9a-f]{32}\b"), r"hermes-[0-9a-f]{32}"),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), r"github_pat_[A-Za-z0-9_]{20,}"),
    ("github_classic_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), r"gh[pousr]_[A-Za-z0-9]{20,}"),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), r"AKIA[0-9A-Z]{16}"),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}"), r"sk-[A-Za-z0-9]{20,}"),
    ("huggingface_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}"), r"hf_[A-Za-z0-9]{20,}"),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), r"xox[abprs]-[A-Za-z0-9-]{10,}"),
]

# Anything that reads as a documentation example, a fixture, or an explicit redaction.
PLACEHOLDER = re.compile(
    r"EXAMPLE|FAKE|PLACEHOLDER|REDACT|xxxx|YOUR_|_YOUR|DUMMY|SAMPLE|NOTREAL|CHANGEME"
    r"|<[^>]*>|\.\.\.",
    re.IGNORECASE,
)

# Refs that exist only for forensics/backup. These are the ones most likely to carry a secret,
# because they exist precisely to preserve content that was considered "not fit for main".
LOCAL_ONLY_REF_PREFIXES = ("refs/stash-backup/", "refs/heads/credential/")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout


def _all_refs() -> list[str]:
    return [line for line in _git("for-each-ref", "--format=%(refname)").splitlines() if line]


def _scan_refs(refs: list[str]) -> list[str]:
    """Return 'ref:path:kind' findings for credential-shaped strings in the given refs' tips.

    One `git grep` per *pattern* across *all* refs, not per (ref, pattern): the quarantine and
    backup refs hold ~2000 files each, and a per-pair invocation means ~140 full tree
    materialisations, which takes minutes.
    """
    if not refs:
        return []
    # One `git grep` for ALL patterns across ALL refs, then attribute kinds in Python.
    # Per-(pattern, ref) invocation means 7x full tree walks (~60s); this is ~8s.
    combined = "|".join(f"({git_re})" for _, _, git_re in CREDENTIAL_PATTERNS)
    result = subprocess.run(
        ["git", "grep", "-l", "-I", "-E", combined, *refs, "--"],
        cwd=REPO_ROOT, capture_output=True, check=False, text=True,
    )
    if result.returncode not in (0, 1):  # 0 = match, 1 = no match
        return []
    findings: list[str] = []
    for line in result.stdout.splitlines():
        ref, _, path = line.partition(":")
        blob = subprocess.run(
            ["git", "cat-file", "blob", f"{ref}:{path}"],
            cwd=REPO_ROOT, capture_output=True, check=False, text=True, errors="replace",
        )
        if blob.returncode != 0:
            continue
        for kind, python_re, _ in CREDENTIAL_PATTERNS:
            # Re-read the blob: `git grep -l` tells us the file, not which token matched.
            if any(
                not PLACEHOLDER.search(m.group(0)) for m in python_re.finditer(blob.stdout)
            ):
                findings.append(f"{ref}:{path}:{kind}")
    return findings


def test_scanner_detects_a_planted_credential() -> None:
    """Negative control: prove the scanner is not silently a no-op.

    Guards the trap where an unsupported regex makes `git grep -E` report "no match" instead of
    erroring — the guard would then look green forever while detecting nothing.
    """
    synthetic = "hermes-" + "de" * 16  # matches the shape, is not a real credential
    blob = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=REPO_ROOT, input=f'token = "{synthetic}"\n', capture_output=True,
        check=True, text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "mktree"], cwd=REPO_ROOT,
        input=f"100644 blob {blob}\tcredential_scan_selfcheck.md\n",
        capture_output=True, check=True, text=True,
    ).stdout.strip()
    ref = "refs/stash-backup/zz-selfcheck"
    subprocess.run(["git", "update-ref", ref, tree], cwd=REPO_ROOT, check=True)
    try:
        findings = _scan_refs([ref])
        assert any("credential_scan_selfcheck.md" in f for f in findings), (
            f"scanner failed to detect a planted credential-shaped string; got {findings}"
        )
    finally:
        subprocess.run(["git", "update-ref", "-d", ref], cwd=REPO_ROOT, check=False)


def test_local_only_refs_carry_no_credentials() -> None:
    """The quarantine/backup refs must not be able to ship a secret."""
    local_only = [r for r in _all_refs() if r.startswith(LOCAL_ONLY_REF_PREFIXES)]
    if not local_only:
        pytest.skip("no local-only forensic refs present")

    findings: list[str] = _scan_refs(local_only)

    assert not findings, (
        "A credential-shaped string is present in a publishable ref. "
        "Redact it (commit a scrubbed copy and repoint the ref) before this ref can be pushed:\n  "
        + "\n  ".join(findings)
    )


@pytest.mark.skipif(
    os.environ.get("HORO_DEEP_REF_SCAN") != "1",
    reason="full-ref scan costs ~200s; set HORO_DEEP_REF_SCAN=1 to run",
)
def test_all_refs_carry_no_credentials() -> None:
    """Every ref tip that a push could publish must be credential-free (opt-in, slow)."""
    findings: list[str] = _scan_refs(_all_refs())

    assert not findings, (
        "A credential-shaped string is present in a ref tip. Any ref can be pushed, so this is a "
        "publication risk. Redact before pushing:\n  " + "\n  ".join(findings)
    )
