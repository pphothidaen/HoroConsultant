from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import scripts.branch_migration_action_priority_guard as branch_guard
import scripts.smart_quality_gate as smart_gate


ROOT = Path(__file__).resolve().parents[2]
AUDIT_SCRIPT = ROOT / "scripts" / "audit_canonical_5_viewports.py"
BRANCH_GUARD_SCRIPT = ROOT / "scripts" / "branch_migration_action_priority_guard.py"
SMART_GATE_SCRIPT = ROOT / "scripts" / "smart_quality_gate.py"

EXPECTED_VIEWPORT_NAMES = (
    "mobile_375x667",
    "tablet_768x1024",
    "laptop_1280x800",
    "desktop_1440x900",
    "desktop_1920x1080",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.AST:
    return ast.parse(_read(path), filename=str(path))


def _is_main_guard(test: ast.AST) -> bool:
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _top_level_call_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(stmt, ast.If) and _is_main_guard(stmt.test):
            continue
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                name = _call_name(node.func)
                if name:
                    names.add(name)
    return names


def _run_help(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_audit_script_is_ast_only_and_entrypoint_guarded() -> None:
    tree = _tree(AUDIT_SCRIPT)
    source = _read(AUDIT_SCRIPT)
    top_level_calls = _top_level_call_names(tree)

    assert ast.get_docstring(tree)
    assert any(
        isinstance(node, ast.If) and _is_main_guard(node.test)
        for node in tree.body
    )
    assert "main()" in source
    assert "uvicorn.run(" in source
    assert "asyncio.run(" in source
    assert "urllib.request.urlopen(" in source
    assert "main" not in top_level_calls
    assert "asyncio.run" not in top_level_calls
    assert "uvicorn.run" not in top_level_calls
    assert "urllib.request.urlopen" not in top_level_calls

    for viewport in EXPECTED_VIEWPORT_NAMES:
        assert viewport in source
    for page_label in ("Main Dashboard (/)", "Admin Panel (/admin)", "HITL Review Studio (/hitl-studio)"):
        assert page_label in source


def test_branch_migration_guard_cli_help_is_closed_and_audit_only() -> None:
    result = _run_help(BRANCH_GUARD_SCRIPT)

    assert result.returncode == 0, result.stderr
    assert "--phase" in result.stdout
    assert "--check" in result.stdout
    assert "--strict" in result.stdout
    assert "--json-output" in result.stdout
    assert "--repo" in result.stdout
    assert "Action Priority Guard" in result.stdout


def test_smart_quality_gate_cli_help_and_tier_classifier_contract() -> None:
    result = _run_help(SMART_GATE_SCRIPT)

    assert result.returncode == 0, result.stderr
    assert "--auto" in result.stdout
    assert "--tier" in result.stdout
    assert "Tiered Quality Gate" in result.stdout

    assert smart_gate.determine_tier_from_changes([]) == 1
    assert smart_gate.determine_tier_from_changes(["README.md"]) == 1
    assert smart_gate.determine_tier_from_changes(["scripts/example.py"]) == 2
    assert smart_gate.determine_tier_from_changes(["project/core/example.py"]) == 2
    assert smart_gate.determine_tier_from_changes(["public/app.js"]) == 3
    assert smart_gate.determine_tier_from_changes(["project/static/site.css"]) == 3


def test_branch_guard_surface_is_the_canonical_five_viewport_set() -> None:
    assert branch_guard.CANONICAL_VIEWPORTS == EXPECTED_VIEWPORT_NAMES
