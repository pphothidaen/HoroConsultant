#!/usr/bin/env python3
"""Synchronize and validate the HoroConsultant AI agent ecosystem.

This is the umbrella gate for keeping agent definitions usable across:

- Claude Code: `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/rules/*`
- ChatGPT/OpenAI Codex: generated `.codex/agents/*.toml`
- Gemini / Google AGY Subagent: `.antigravity/agents/*`, `.agents/agents/*`
- Hermes: routing/parity scripts and generated `hermes` role
- thClaws CLI: universal/thClaws bridge scripts

Use `--check` in CI and before release claims. Use `--sync` after changing
legacy agent definitions or skills, then commit the generated repo files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_AGENT_ROLES = {
    "orchestrator",
    "business_analyst",
    "developer",
    "qa_tester",
    "devops",
    "code_reviewer",
    "hermes",
}

REQUIRED_PLATFORM_FILES = {
    "global_codex_context": ROOT / "AGENTS.md",
    "global_claude_context": ROOT / "CLAUDE.md",
    "claude_project_settings": ROOT / ".claude" / "settings.json",
    "claude_short_context": ROOT / ".claude" / "CLAUDE.md",
    "gemini_parity_config": ROOT / ".agents" / "config" / "gemini_parity.yaml",
    "hermes_router": ROOT / "scripts" / "hermes_agy_router.py",
    "hermes_runner": ROOT / "scripts" / "hermes_sdlc_runner.sh",
    "thclaws_bridge": ROOT / "scripts" / "run_thclaws_bridge.py",
    "universal_bridge": ROOT / "scripts" / "run_universal_bridge.py",
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_command(name: str, command: list[str]) -> CheckResult:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    detail = output.splitlines()[-1] if output else "no output"
    return CheckResult(name=name, ok=result.returncode == 0, detail=detail)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_json_file(name: str, path: Path) -> CheckResult:
    try:
        load_json(path)
    except Exception as error:
        return CheckResult(name, False, f"{relative(path)}: {error}")
    return CheckResult(name, True, f"{relative(path)} parses")


def check_required_files() -> CheckResult:
    missing = [
        f"{label}={relative(path)}"
        for label, path in REQUIRED_PLATFORM_FILES.items()
        if not path.exists()
    ]
    if missing:
        return CheckResult("required platform files", False, ", ".join(missing))
    return CheckResult("required platform files", True, f"{len(REQUIRED_PLATFORM_FILES)} files present")


def check_settings_roles() -> CheckResult:
    try:
        settings = load_json(ROOT / "settings.json")
    except Exception as error:
        return CheckResult("settings role map", False, str(error))

    models = settings.get("models", {})
    missing = sorted(role for role in REQUIRED_AGENT_ROLES if role not in models)
    if missing:
        return CheckResult("settings role map", False, f"missing roles: {', '.join(missing)}")
    if settings.get("default_agent") != "orchestrator":
        return CheckResult("settings role map", False, "default_agent must be orchestrator")
    return CheckResult("settings role map", True, f"{len(REQUIRED_AGENT_ROLES)} core roles mapped")


def check_claude_hooks() -> CheckResult:
    settings_path = ROOT / ".claude" / "settings.json"
    try:
        settings = load_json(settings_path)
    except Exception as error:
        return CheckResult("claude hooks", False, str(error))

    pre_tool = settings.get("hooks", {}).get("PreToolUse", [])
    commands: list[str] = []
    matchers: list[str] = []
    for group in pre_tool:
        if isinstance(group, dict):
            matchers.append(str(group.get("matcher", "")))
            for hook in group.get("hooks", []):
                if isinstance(hook, dict):
                    commands.append(str(hook.get("command", "")))

    joined_matchers = "|".join(matchers)
    missing_tools = [
        tool
        for tool in ("Bash", "Read", "Grep", "Glob", "Edit", "Write", "MultiEdit")
        if tool not in joined_matchers
    ]
    if missing_tools:
        return CheckResult("claude hooks", False, f"missing matchers: {', '.join(missing_tools)}")
    if not any("pre_tool_guard.py" in command for command in commands):
        return CheckResult("claude hooks", False, "pre_tool_guard.py is not registered")
    if not (ROOT / ".claude" / "hooks" / "pre_tool_guard.py").exists():
        return CheckResult("claude hooks", False, "pre_tool_guard.py is missing")
    return CheckResult("claude hooks", True, "PreToolUse guard registered")


def check_claude_rules() -> CheckResult:
    rules_dir = ROOT / ".claude" / "rules"
    required = {
        "api-contract.md",
        "frontend-contract.md",
        "testing-and-release.md",
        "secrets-and-devops.md",
        "orchestrator-subagents.md",
    }
    if not rules_dir.is_dir():
        return CheckResult("claude rules", False, ".claude/rules missing")

    found = {path.name for path in rules_dir.glob("*.md")}
    missing = sorted(required - found)
    if missing:
        return CheckResult("claude rules", False, f"missing rules: {', '.join(missing)}")

    for rule in sorted(rules_dir.glob("*.md")):
        content = rule.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            return CheckResult("claude rules", False, f"{relative(rule)} missing frontmatter")
        try:
            _, frontmatter, _ = content.split("---", 2)
            data = yaml.safe_load(frontmatter) or {}
        except Exception as error:
            return CheckResult("claude rules", False, f"{relative(rule)} invalid frontmatter: {error}")
        if not data.get("description") or not data.get("paths"):
            return CheckResult("claude rules", False, f"{relative(rule)} needs description and paths")

    return CheckResult("claude rules", True, f"{len(found)} rule files valid")


def check_codex_agents_present() -> CheckResult:
    codex_dir = ROOT / ".codex" / "agents"
    missing = sorted(
        role for role in REQUIRED_AGENT_ROLES if not (codex_dir / f"{role}.toml").exists()
    )
    if missing:
        return CheckResult("codex generated roles", False, f"missing: {', '.join(missing)}")
    return CheckResult("codex generated roles", True, f"{len(REQUIRED_AGENT_ROLES)} core roles present")


def check_hermes_and_thclaws_contract() -> CheckResult:
    hermes_text = (ROOT / "scripts" / "hermes_agy_router.py").read_text(encoding="utf-8")
    universal_text = (ROOT / "scripts" / "run_universal_bridge.py").read_text(encoding="utf-8")
    thclaws_text = (ROOT / "scripts" / "run_thclaws_bridge.py").read_text(encoding="utf-8")

    expected = {
        "agy1": hermes_text,
        "agy2": hermes_text,
        "agy3": hermes_text,
        "hybrid": universal_text,
        "thclaws": universal_text + thclaws_text,
    }
    missing = [needle for needle, haystack in expected.items() if needle not in haystack]
    if missing:
        return CheckResult("hermes/thClaws contract", False, f"missing markers: {', '.join(missing)}")
    return CheckResult("hermes/thClaws contract", True, "routing and bridge markers present")


def run_checks() -> list[CheckResult]:
    return [
        check_required_files(),
        check_json_file("settings.json", ROOT / "settings.json"),
        check_json_file(".mcp.json", ROOT / ".mcp.json"),
        check_json_file(".claude/settings.json", ROOT / ".claude" / "settings.json"),
        check_settings_roles(),
        check_claude_hooks(),
        check_claude_rules(),
        check_codex_agents_present(),
        check_hermes_and_thclaws_contract(),
        run_command("Antigravity/Gemini/AGY sync", [sys.executable, "scripts/sync_sdlc_agents.py", "--check", "--use-python"]),
        run_command("Codex/OpenAI sync", [sys.executable, "scripts/sync_codex_agents.py", "--check"]),
    ]


def print_results(results: list[CheckResult]) -> None:
    for result in results:
        prefix = "[OK]" if result.ok else "[ERROR]"
        print(f"{prefix} {result.name}: {result.detail}")


def sync_then_check() -> int:
    sync_results = [
        run_command("Antigravity/Gemini/AGY sync write", [sys.executable, "scripts/sync_sdlc_agents.py", "--sync"]),
        run_command("Codex/OpenAI sync write", [sys.executable, "scripts/sync_codex_agents.py", "--sync"]),
    ]
    print_results(sync_results)
    if not all(result.ok for result in sync_results):
        return 1

    check_results = run_checks()
    print_results(check_results)
    return 0 if all(result.ok for result in check_results) else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only ecosystem sync validation.")
    mode.add_argument("--sync", action="store_true", help="Write generated sync targets, then validate.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sync:
        return sync_then_check()

    results = run_checks()
    print_results(results)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
