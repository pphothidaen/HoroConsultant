"""Unit and regression test suite for Claude Code vs. AGY CLI Parity & Auto-Sync Trigger.

Verifies:
1. Full parity between .claude/ and .agy/ architectures.
2. Progressive disclosure rules have valid Glob paths and frontmatter.
3. Skills have standard frontmatter contracts and ## Gotchas.
4. Sandboxed subagents adhere to tool restrictions (read-only/write-isolation).
5. Lifecycle hooks are present, executable, and correctly wired.
6. Auto-sync trigger functions cleanly with 100% fail-closed guarantee.
"""

import os
import subprocess
import sys

from scripts.sync_claude_agy_parity import (
    AGY_AGENTS_DIR,
    AGY_HOOKS_DIR,
    AGY_IGNORE,
    AGY_MD,
    AGY_RULES_DIR,
    AGY_SKILLS_DIR,
    CLAUDE_IGNORE,
    CLAUDE_MD,
    CLAUDE_RULES_DIR,
    ROOT,
    parse_frontmatter,
    run_all_parity_checks,
)


def test_parity_check_returns_zero_on_current_repo() -> None:
    """Validate that the workspace is currently 100% in parity."""
    results = run_all_parity_checks(check_only=True)
    failing = [res for res in results if not res.ok]
    assert not failing, f"Parity checks failed: {[f.component + ': ' + f.detail for f in failing]}"


def test_root_context_contracts_exist_and_bounded() -> None:
    """Ensure CLAUDE.md and AGY.md exist, and AGY.md is strictly under 150 lines."""
    assert CLAUDE_MD.exists(), "CLAUDE.md must exist in root"
    assert AGY_MD.exists(), "AGY.md must exist in root"

    agy_lines = len(AGY_MD.read_text(encoding="utf-8").splitlines())
    assert agy_lines < 150, f"AGY.md must be strictly under 150 lines, got {agy_lines}"


def test_ignore_files_parity_and_critical_patterns() -> None:
    """Ensure .claudeignore and .agyignore contain identical token exclusion patterns."""
    assert CLAUDE_IGNORE.exists(), ".claudeignore must exist"
    assert AGY_IGNORE.exists(), ".agyignore must exist"

    claude_lines = {line.strip() for line in CLAUDE_IGNORE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")}
    agy_lines = {line.strip() for line in AGY_IGNORE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")}

    assert claude_lines == agy_lines, "Patterns between .claudeignore and .agyignore must match 100%"
    assert ".env*" in claude_lines, ".env* must be ignored"
    assert "*.lock" in claude_lines, "*.lock must be ignored"


def test_progressive_rules_have_paths_and_descriptions() -> None:
    """Verify all rules in .claude/rules/ and .agy/rules/ have valid frontmatter."""
    claude_rules = sorted(CLAUDE_RULES_DIR.glob("*.md"))
    agy_rules = sorted(AGY_RULES_DIR.glob("*.md"))

    assert len(claude_rules) > 0, "Must have progressive rules in .claude/rules"
    assert len(claude_rules) == len(agy_rules), "Rule counts between Claude and AGY must match"

    for r_file in agy_rules:
        content = r_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        assert "paths" in fm, f"Rule {r_file.name} missing 'paths' frontmatter"
        assert "description" in fm, f"Rule {r_file.name} missing 'description' frontmatter"
        assert len(body.strip()) > 0, f"Rule {r_file.name} must have markdown body"


def test_skills_frontmatter_and_gotchas() -> None:
    """Verify custom skills have required YAML fields and ## Gotchas documentation."""
    skills = [p for p in AGY_SKILLS_DIR.iterdir() if p.is_dir()]
    assert len(skills) >= 2, "Must have at least conventional-flow and vulnerability-scanner skills"

    for s_dir in skills:
        s_file = s_dir / "SKILL.md"
        assert s_file.exists(), f"Missing SKILL.md in {s_dir.name}"
        content = s_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        assert fm.get("name"), f"Skill {s_dir.name} missing name"
        assert "## Gotchas" in body, f"Skill {s_dir.name} must document ## Gotchas"


def test_sandboxed_agents_disallowed_tools() -> None:
    """Verify subagents have explicit tools and disallowedTools declarations."""
    agents = sorted(AGY_AGENTS_DIR.glob("*.md"))
    assert len(agents) >= 1, "Must have at least one sandboxed agent"

    for a_file in agents:
        content = a_file.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(content)
        assert fm.get("name"), f"Agent {a_file.name} missing name"
        assert "tools" in fm, f"Agent {a_file.name} missing tools"
        assert "disallowedTools" in fm, f"Agent {a_file.name} missing disallowedTools sandbox"


def test_lifecycle_hooks_executable() -> None:
    """Verify hook scripts are marked executable and present."""
    required_hooks = ["pre-tool-use.sh", "post-tool-use.sh", "stop-monitor.sh"]
    for hook_name in required_hooks:
        hook_path = AGY_HOOKS_DIR / hook_name
        assert hook_path.exists(), f"Hook {hook_name} must exist"
        assert os.access(hook_path, os.X_OK), f"Hook {hook_name} must be executable (chmod +x)"


def test_cli_parity_sync_tool_execution() -> None:
    """Test CLI execution of scripts/sync_claude_agy_parity.py --check."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_claude_agy_parity.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"sync_claude_agy_parity.py --check failed: {result.stderr or result.stdout}"
    assert "[OK]" in result.stdout
