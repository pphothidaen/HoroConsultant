"""Guard: no test may use a subprocess CWD that can shadow an importable module.

Several tests spawn a fresh interpreter with ``cwd="/tmp"`` (see
``project/tests/test_rust_extensions.py``).  For ``python -c`` the interpreter
prepends the CWD to ``sys.path[0]``, so any file in that directory named after
an importable module -- ``inspect.py``, ``json.py``, ``bisect.py`` -- silently
replaces the stdlib module for the whole subprocess.

That failure mode is maximally confusing: the subprocess dies deep inside an
unrelated import (``dataclasses`` -> ``inspect``), and the test then reports a
domain error such as "required native kernel is missing" that has nothing to do
with the real cause.  It has already cost real debugging time: two stray probe
scripts left in ``/tmp`` by an earlier session broke two Rust-extension tests.

This test makes the contamination loud and local instead of remote and cryptic.
It is deliberately read-only: it reports, it never deletes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories that are used as a subprocess CWD somewhere in the suite.  Each
# entry is (description, resolved path).  ``/tmp`` is a symlink to
# ``/private/tmp`` on macOS, so it is resolved before scanning.
_CWD_IN_USE: tuple[tuple[str, Path], ...] = (
    ("project/tests/test_rust_extensions.py (cwd='/tmp')", Path("/tmp")),
)


def _importable_names() -> frozenset[str]:
    """Names that a stray file in a CWD could shadow.

    Includes the standard library plus every already-installed third-party
    top-level module, because a stray ``numpy.py`` or ``yaml.py`` in a temp
    directory is just as capable of hijacking an import.
    """
    names: set[str] = set(getattr(sys, "stdlib_module_names", ()))
    try:
        import importlib.util

        for entry in sys.path:
            if not entry:
                continue
            try:
                for candidate in Path(entry).glob("*.py"):
                    if candidate.stem.isidentifier() and not candidate.stem.startswith("_"):
                        names.add(candidate.stem)
                for candidate in Path(entry).iterdir():
                    if candidate.is_dir() and (candidate / "__init__.py").exists():
                        if candidate.name.isidentifier() and not candidate.name.startswith("_"):
                            names.add(candidate.name)
            except (OSError, ValueError):
                continue
    except Exception:  # pragma: no cover - defensive only
        pass
    return frozenset(names)


@pytest.mark.parametrize("description, cwd", _CWD_IN_USE, ids=[d for d, _ in _CWD_IN_USE])
def test_subprocess_cwd_contains_no_import_shadowing_modules(description: str, cwd: Path) -> None:
    """A CWD used by a test must not be able to hijack ``import``."""
    if not cwd.is_dir():
        pytest.skip(f"{cwd} does not exist on this platform")

    shadowable = _importable_names()
    offenders: list[str] = []

    for path in sorted(cwd.glob("*.py")):
        stem = path.stem
        if stem in shadowable and not stem.startswith("_"):
            offenders.append(stem)

    assert not offenders, (
        f"{cwd} (used as a subprocess CWD by {description}) contains module(s) named "
        f"{sorted(offenders)}. Because the CWD is prepended to sys.path for `python -c`, "
        f"these shadow the real module and break every test that spawns an interpreter "
        f"there, typically with a misleading error. Move or rename them; do not delete "
        f"work that may still be in use."
    )


def test_tmp_dir_is_not_reused_as_a_scratch_directory() -> None:
    """Document why the suite must prefer pytest's ``tmp_path`` over a shared temp dir.

    ``/tmp`` is shared by every process on the machine, so probe scripts written
    there outlive the session that created them. ``tmp_path`` is per-test and
    auto-cleaned, which is why the fix is to stop using a shared CWD rather than
    to keep policing ``/tmp``.
    """
    assert not (Path("/tmp") / "conftest.py").exists(), (
        "A conftest.py in the shared /tmp directory would be auto-loaded by any pytest "
        "run rooted there. Never write test configuration into a shared temp dir."
    )
    assert _REPO_ROOT.is_dir()
