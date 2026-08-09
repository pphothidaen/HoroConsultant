"""Behavioral tests for the backward-compatible Codex agent synchronizer."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync_codex_agents.py"
SOURCE_DIR = ROOT / ".agents" / "agents"


def source_agents() -> dict[str, dict[str, object]]:
    """Load the legacy files that define the migration's public contract."""
    return {
        source.parent.name: json.loads(source.read_text(encoding="utf-8"))
        for source in sorted(SOURCE_DIR.glob("*/agent.json"))
    }


def run_sync(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the real CLI without modifying the repository's generated files."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_sync_generates_valid_codex_toml_from_every_legacy_agent(tmp_path: Path) -> None:
    """Catch a generator that drops roles, corrupts TOML, or loses the role prompt."""
    output_dir = tmp_path / "codex-agents"

    result = run_sync("--source-dir", str(SOURCE_DIR), "--output-dir", str(output_dir))

    assert result.returncode == 0, result.stdout + result.stderr
    expected_agents = source_agents()
    assert {path.stem for path in output_dir.glob("*.toml")} == set(expected_agents)

    for name, source in expected_agents.items():
        generated = tomllib.loads((output_dir / f"{name}.toml").read_text(encoding="utf-8"))
        assert generated["name"] == source["name"]
        assert generated["description"] == source["description"]
        assert str(source["system_prompt"]) in generated["developer_instructions"]


def test_check_rejects_a_stale_generated_agent_file(tmp_path: Path) -> None:
    """Catch a check mode that reports success after a generated role has drifted."""
    output_dir = tmp_path / "codex-agents"
    initial = run_sync("--source-dir", str(SOURCE_DIR), "--output-dir", str(output_dir))
    assert initial.returncode == 0, initial.stdout + initial.stderr

    (output_dir / "developer.toml").write_text('name = "stale"\n', encoding="utf-8")
    checked = run_sync(
        "--source-dir", str(SOURCE_DIR), "--output-dir", str(output_dir), "--check"
    )

    assert checked.returncode == 1
    assert "[ERROR] Stale Codex agent definition: developer.toml" in checked.stdout
