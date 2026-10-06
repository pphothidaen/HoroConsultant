"""Guard the patched dependency versions pinned in lockfiles.

Dependabot flagged urllib3 (uv.lock) and rustls (rust_core/Cargo.lock) as
vulnerable; PR #140 bumped the locked versions to the first patched releases.
These guards fail if a lockfile refresh regresses either package below the
patched version while the advisory ranges are still open.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UV_LOCK = REPO_ROOT / "uv.lock"
CARGO_LOCK = REPO_ROOT / "rust_core" / "Cargo.lock"


def _locked_version(lock_text: str, package: str) -> str:
    blocks = re.split(r"\n\[\[package\]\]", lock_text)
    for block in blocks:
        name_match = re.search(r'name = "([^"]+)"', block)
        version_match = re.search(r'version = "([^"]+)"', block)
        if name_match and version_match and name_match.group(1) == package:
            return version_match.group(1)
    raise AssertionError(f"package {package!r} not found in lockfile")


def test_urllib3_pinned_to_patched_release() -> None:
    version = _locked_version(UV_LOCK.read_text(encoding="utf-8"), "urllib3")
    assert tuple(int(p) for p in version.split(".")) >= (2, 8, 0), (
        f"urllib3 {version} is inside the vulnerable ranges fixed by 2.8.0"
    )


def test_rustls_pinned_to_patched_release() -> None:
    version = _locked_version(CARGO_LOCK.read_text(encoding="utf-8"), "rustls")
    assert tuple(int(p) for p in version.split(".")) >= (0, 23, 45), (
        f"rustls {version} is inside the vulnerable range fixed by 0.23.45"
    )
