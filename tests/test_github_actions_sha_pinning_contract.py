"""Contract test: all GitHub Actions are pinned to immutable commit SHAs (KAN-291).

M1 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Supply-chain hardening (Red Team CRITICAL-1): an action referenced by a mutable
tag (`actions/checkout@v4`) can be re-pointed by its upstream maintainer at any
time, so a CI run can execute attacker-controlled code without any change to this
repository. Pinning every action to a full 40-hex commit SHA removes that
indirection, and `.github/dependabot.yml` keeps the pins from silently rotting.

This test is deliberately strict:
  * every `uses:` entry must resolve to a 40-hex SHA (no `@v4`, no `@stable`);
  * `.github/dependabot.yml` must exist and must watch the `github-actions`
    ecosystem so the pins are maintained rather than frozen forever.

The `.yml.legacy` file is excluded: it is an archived workflow that is never
loaded by the Actions runner, so it carries no supply-chain exposure.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
DEPENDABOT_YML = ROOT / ".github" / "dependabot.yml"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _workflow_files() -> list[Path]:
    """All loaded workflow files (archived `.legacy` copies are excluded)."""
    return sorted(
        p for p in WORKFLOWS_DIR.iterdir() if p.suffix in (".yml", ".yaml")
    )


def _uses_entries(doc: object) -> list[str]:
    """Collect every `uses:` value from a parsed workflow document."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "uses" and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)
    return found


@pytest.fixture(scope="module")
def workflow_uses() -> dict[str, list[str]]:
    """Map workflow filename -> list of `uses:` values."""
    result: dict[str, list[str]] = {}
    for path in _workflow_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict):
            result[path.name] = _uses_entries(doc)
    return result


@pytest.fixture(scope="module")
def dependabot_doc() -> dict:
    assert DEPENDABOT_YML.is_file(), ".github/dependabot.yml must exist (M1)"
    doc = yaml.safe_load(DEPENDABOT_YML.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


# ── every action is SHA-pinned ───────────────────────────────────────────

def test_workflows_directory_has_content(workflow_uses: dict) -> None:
    """Guard against a vacuous pass if the glob ever stops matching."""
    assert len(workflow_uses) >= 20, (
        f"Expected the repo's workflow inventory to load, got {len(workflow_uses)} files"
    )


def test_every_action_is_pinned_to_full_sha(workflow_uses: dict) -> None:
    offenders: list[str] = []
    checked = 0
    for fname, entries in workflow_uses.items():
        for entry in entries:
            checked += 1
            if "@" not in entry:
                offenders.append(f"{fname}: {entry} (no @ref)")
                continue
            ref = entry.rsplit("@", 1)[1]
            if not SHA_RE.match(ref):
                offenders.append(f"{fname}: {entry} (mutable ref, not a 40-hex SHA)")

    assert checked > 0, "No `uses:` entries found — the scan did not run"
    assert not offenders, (
        "Unpinned GitHub Actions detected (supply-chain risk, M1/KAN-291):\n"
        + "\n".join(f"  - {o}" for o in offenders)
    )


def test_pinned_actions_carry_version_comments(workflow_uses: dict) -> None:
    """Pins must be annotated with their version so Dependabot can bump them.

    Dependabot's github-actions updater matches the `# vX.Y.Z` comment against
    upstream releases. A bare SHA with no comment would pin forever.
    """
    for path in _workflow_files():
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "uses:" not in line:
                continue
            if re.search(r"uses:\s*\S+@[0-9a-f]{40}", line) and "#" not in line:
                pytest.fail(
                    f"{path.name}:{lineno} pins a SHA without a version comment: {line.strip()}"
                )


# ── dependabot keeps the pins fresh ──────────────────────────────────────

def test_dependabot_watches_github_actions(dependabot_doc: dict) -> None:
    ecosystems = {
        u.get("package-ecosystem") for u in dependabot_doc.get("updates", [])
    }
    assert "github-actions" in ecosystems, (
        "Dependabot must watch the github-actions ecosystem so SHA pins are "
        "bumped automatically instead of rotting (M1/KAN-291). "
        f"Found: {sorted(e for e in ecosystems if e)}"
    )
