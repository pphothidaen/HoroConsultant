"""Guard: no test may run a subprocess with a shared, world-writable CWD.

Several tests spawn a fresh interpreter with a controlled working directory. For
``python -c`` the interpreter prepends the CWD to ``sys.path[0]``, so a file in
that directory named after an importable module -- ``inspect.py``, ``json.py``,
``bisect.py`` -- silently replaces the real one for the whole subprocess.

That failure mode is maximally confusing: the subprocess dies deep inside an
unrelated import (``dataclasses`` -> ``inspect``) and the test then reports a
domain error that has nothing to do with the real cause. It already cost real
debugging time here: two stray probe scripts an earlier session left in the
shared temp directory broke two Rust-extension tests with a misleading
"required native kernel is missing" assertion.

The hardened call sites now use a private, per-invocation directory, so this test
no longer needs to police any one directory. It asserts the *invariant* that keeps
them fixed: a subprocess CWD must never be a shared location. That form is
self-maintaining -- it catches the next author who reaches for ``/tmp``, in a
file this test has never seen.

Passing ``-P``/``PYTHONSAFEPATH`` is deliberately NOT treated as the fix on its
own: it requires Python 3.11 while this project supports 3.10, and it does not
cover nested interpreters.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories any process on the machine can write to. Using one as a subprocess
# CWD makes the suite's imports depend on ambient filesystem state.
_SHARED_DIRS = frozenset({"/tmp", "/var/tmp", "/private/tmp", "/private/var/tmp"})

_SEARCH_ROOTS = ("tests", "project/tests", "rust_core/tests")


def _iter_test_sources() -> list[Path]:
    files: list[Path] = []
    for rel in _SEARCH_ROOTS:
        root = _REPO_ROOT / rel
        if root.is_dir():
            files.extend(sorted(root.rglob("*.py")))
    return files


def _literal_string(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _is_subprocess_call(node: ast.AST) -> bool:
    """True for ``subprocess.run`` / ``Popen`` / ``check_output`` and friends."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return isinstance(func.value, ast.Name) and func.value.id == "subprocess"
    if isinstance(func, ast.Name):
        return func.id in {"run", "Popen", "check_output", "check_call"}
    return False


def test_no_test_uses_a_shared_directory_as_a_subprocess_cwd() -> None:
    """A shared CWD lets unrelated files hijack the child's imports."""
    offenders: list[str] = []
    self_name = Path(__file__).name

    for path in _iter_test_sources():
        # This guard legitimately names those directories.
        if path.name == self_name:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_subprocess_call(node):
                continue
            for keyword in node.keywords:
                if keyword.arg != "cwd":
                    continue
                value = _literal_string(keyword.value)
                if value is not None and value.rstrip("/") in _SHARED_DIRS:
                    offenders.append(
                        f"{path.relative_to(_REPO_ROOT)}:{node.lineno} subprocess cwd={value!r}"
                    )

    assert not offenders, (
        "These call sites run a subprocess with a shared, world-writable working "
        "directory. Because `python -c` prepends the CWD to sys.path, any stray file "
        "named after an importable module is imported instead of the real one, "
        "producing failures that point at the wrong thing:\n  "
        + "\n  ".join(offenders)
        + "\nUse a private per-invocation directory instead: tempfile."
        'TemporaryDirectory() (preferred, works on every supported interpreter) or '
        "pytest's tmp_path fixture."
    )


def test_shared_temp_dirs_hold_no_stdlib_named_modules() -> None:
    """Belt-and-braces: a shared dir must not be able to hijack an import.

    The invariant test above is the real protection. This one is a canary for the
    machine rather than the repo: if something re-arms a shared temp directory,
    any *other* project or agent session using it as a CWD is exposed too, and it
    is worth saying so loudly rather than cleaning up silently.
    """
    present = [d for d in sorted(_SHARED_DIRS) if Path(d).is_dir()]
    if not present:
        pytest.skip("no shared temp directory present on this platform")

    for directory in present:
        offenders = [
            p.name
            for p in Path(directory).glob("*.py")
            if p.stem in getattr(sys, "stdlib_module_names", ()) and not p.stem.startswith("_")
        ]
        assert not offenders, (
            f"{directory} contains {sorted(offenders)}, which shadow the standard "
            f"library for any interpreter started with that directory as its CWD. "
            f"Move or rename them; do not delete work that may still be in use."
        )
