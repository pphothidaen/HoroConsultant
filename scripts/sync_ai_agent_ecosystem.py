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
    "global_agy_context": ROOT / "AGY.md",
    "claude_project_settings": ROOT / ".claude" / "settings.json",
    "claude_short_context": ROOT / ".claude" / "CLAUDE.md",
    "agy_hooks_manifest": ROOT / ".agy" / "hooks.json",
    "sync_claude_agy": ROOT / "scripts" / "sync_claude_agy_parity.py",
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


def check_hf_static_release_governance() -> CheckResult:
    """Validate the source-of-truth policy, skill, catalog, and release owners."""
    rule_path = ROOT / ".agents" / "rules" / "16-hf-static-release-verification.md"
    claude_rule_path = ROOT / ".claude" / "rules" / "hf-static-release-verification.md"
    skill_path = ROOT / ".agents" / "skills" / "hf-static-release-verification" / "SKILL.md"
    evals_path = skill_path.parent / "evals" / "evals.json"
    catalog_path = ROOT / ".agents" / "AGENTS.md"
    required_files = (rule_path, claude_rule_path, skill_path, evals_path, catalog_path)
    missing = [relative(path) for path in required_files if not path.is_file()]
    if missing:
        return CheckResult("HF Static release governance", False, f"missing: {', '.join(missing)}")

    skill_text = skill_path.read_text(encoding="utf-8")
    try:
        _, frontmatter, _ = skill_text.split("---", 2)
        skill_data = yaml.safe_load(frontmatter) or {}
        eval_data = load_json(evals_path)
    except Exception as error:
        return CheckResult("HF Static release governance", False, f"invalid skill package: {error}")
    if skill_data.get("name") != "hf-static-release-verification":
        return CheckResult("HF Static release governance", False, "skill name is not canonical")
    if not skill_data.get("description") or len(str(skill_data["description"]).strip()) > 100:
        return CheckResult("HF Static release governance", False, "skill description must be 1-100 chars")
    if eval_data.get("skill_name") != skill_data["name"] or not eval_data.get("evals"):
        return CheckResult("HF Static release governance", False, "skill evals are missing or misaligned")
    if "hf-static-release-verification" not in catalog_path.read_text(encoding="utf-8"):
        return CheckResult("HF Static release governance", False, "skill is missing from .agents/AGENTS.md")

    policy_terms = (
        "SDK-aware",
        "fail-closed",
        "exact-cardinality",
        "five canonical viewport",
        "a release claim on failure",
    )
    rule_text = rule_path.read_text(encoding="utf-8")
    normalized_rule_text = rule_text.casefold()
    missing_terms = [term for term in policy_terms if term.casefold() not in normalized_rule_text]
    if missing_terms:
        return CheckResult("HF Static release governance", False, f"rule missing: {', '.join(missing_terms)}")
    claude_text = claude_rule_path.read_text(encoding="utf-8")
    for shared_term in ("SDK-aware", "fail-closed", "exact-cardinality", "five canonical viewports"):
        if shared_term not in claude_text:
            return CheckResult("HF Static release governance", False, f"Claude mirror missing: {shared_term}")

    owner_contracts = {
        "devops": "HF Static Release Gate Owner",
        "qa_tester": "HF Static QA Evidence Owner",
        "code_reviewer": "HF Static Evidence Guard",
        "orchestrator": "HF Static Final Decision Owner",
    }
    alias_files = {
        "devops": ("devops.agent",),
        "qa_tester": ("qa-tester.agent", "qa_tester.agent"),
        "code_reviewer": ("code-reviewer.agent", "code_reviewer.agent"),
        "orchestrator": ("orchestrator.agent",),
    }
    for owner, filenames in alias_files.items():
        definitions = []
        for filename in filenames:
            path = ROOT / ".antigravity" / "agents" / filename
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception as error:
                return CheckResult("HF Static release governance", False, f"invalid {relative(path)}: {error}")
            if "hf-static-release-verification" not in data.get("tools", []):
                return CheckResult("HF Static release governance", False, f"{filename} missing release skill")
            if owner_contracts[owner] not in str(data.get("system_prompt", "")):
                return CheckResult("HF Static release governance", False, f"{filename} missing owner contract")
            definitions.append(data)
        if len(definitions) == 2 and definitions[0] != definitions[1]:
            return CheckResult("HF Static release governance", False, f"{owner} alias definitions differ")

        downstream_json = ROOT / ".agents" / "agents" / owner / "agent.json"
        downstream_codex = ROOT / ".codex" / "agents" / f"{owner}.toml"
        try:
            downstream_data = load_json(downstream_json)
            codex_text = downstream_codex.read_text(encoding="utf-8")
        except Exception as error:
            return CheckResult(
                "HF Static release governance",
                False,
                f"stale or missing generated role for {owner}: {error}",
            )
        if "hf-static-release-verification" not in downstream_data.get("tools", []):
            return CheckResult(
                "HF Static release governance", False, f"{relative(downstream_json)} missing release skill"
            )
        if owner_contracts[owner] not in str(downstream_data.get("system_prompt", "")):
            return CheckResult(
                "HF Static release governance", False, f"{relative(downstream_json)} missing owner contract"
            )
        if "hf-static-release-verification" not in codex_text or owner_contracts[owner] not in codex_text:
            return CheckResult(
                "HF Static release governance", False, f"{relative(downstream_codex)} is stale"
            )

    return CheckResult(
        "HF Static release governance",
        True,
        "rule, Claude mirror, skill, evals, catalog, and four owner contracts aligned",
    )


def check_context_handoff_governance(sync: bool = False) -> CheckResult:
    canonical = ROOT / ".agents" / "skills" / "anti-cognitive-decay" / "SKILL.md"
    if not canonical.is_file():
        return CheckResult("anti-cognitive-decay skill", False, "canonical skill missing")
    canonical_bytes = canonical.read_bytes()
    mirrors = (
        ROOT / ".antigravity" / "skills" / "anti-cognitive-decay" / "SKILL.md",
        ROOT / ".claude" / "skills" / "anti-cognitive-decay" / "SKILL.md",
        ROOT / ".agy" / "skills" / "anti-cognitive-decay" / "SKILL.md",
    )
    if sync:
        for mirror in mirrors:
            mirror.parent.mkdir(parents=True, exist_ok=True)
            mirror.write_bytes(canonical_bytes)
        return CheckResult("anti-cognitive-decay skill sync", True, "mirrors synchronized")

    for mirror in mirrors:
        if not mirror.is_file():
            return CheckResult("anti-cognitive-decay skill", False, f"missing mirror: {relative(mirror)}")
        if mirror.read_bytes() != canonical_bytes:
            return CheckResult("anti-cognitive-decay skill", False, f"anti-cognitive-decay drift detected in {relative(mirror)}")
    return CheckResult("anti-cognitive-decay skill", True, "canonical and generated mirrors aligned")


def check_plan_completion_and_release_notes_governance() -> CheckResult:
    rule_path = ROOT / ".agents" / "rules" / "22-plan-completion-and-release-notes.md"
    claude_rule_path = ROOT / ".claude" / "rules" / "plan-completion-release-notes.md"
    rn_path = ROOT / "ReleaseNotes.md"
    
    if not rule_path.is_file():
        return CheckResult("Plan completion governance", False, f"missing: {relative(rule_path)}")
    if not claude_rule_path.is_file():
        return CheckResult("Plan completion governance", False, f"missing: {relative(claude_rule_path)}")
    if not rn_path.is_file():
        return CheckResult("Plan completion governance", False, f"missing: {relative(rn_path)}")
        
    rule_text = rule_path.read_text(encoding="utf-8")
    mandatory_terms = ["Executive Summary", "Architectural Deliverables", "Verification Matrix", "Milestone Rollup", "Live Production Endpoints", "Archived Plans List"]
    missing_rule_terms = [t for t in mandatory_terms if t not in rule_text]
    if missing_rule_terms:
        return CheckResult("Plan completion governance", False, f"rule missing terms: {', '.join(missing_rule_terms)}")
        
    rn_text = rn_path.read_text(encoding="utf-8")
    missing_rn_terms = [t for t in mandatory_terms if t not in rn_text]
    if missing_rn_terms:
        return CheckResult("Plan completion governance", False, f"ReleaseNotes.md missing sections: {', '.join(missing_rn_terms)}")
        
    plans_dir = ROOT / "plans"
    stale_files = []
    if plans_dir.is_dir():
        for file in plans_dir.iterdir():
            if file.is_file() and file.name.endswith(".md"):
                if file.name not in [
                    "plan.md",
                ]:
                    stale_files.append(file.name)
    if stale_files:
        return CheckResult("Plan completion governance", False, f"stale plans found: {', '.join(stale_files)}")
        
    return CheckResult("Plan completion governance", True, "Rule 22 enforced, ReleaseNotes aligned, plans clean")


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
        check_hf_static_release_governance(),
        check_context_handoff_governance(sync=False),
        check_plan_completion_and_release_notes_governance(),
        run_command("Antigravity/Gemini/AGY sync", [sys.executable, "scripts/sync_sdlc_agents.py", "--check", "--use-python"]),
        run_command("Codex/OpenAI sync", [sys.executable, "scripts/sync_codex_agents.py", "--check"]),
        run_command("Claude Code <-> AGY CLI Parity", [sys.executable, "scripts/sync_claude_agy_parity.py", "--check"]),
    ]


def print_results(results: list[CheckResult]) -> None:
    for result in results:
        prefix = "[OK]" if result.ok else "[ERROR]"
        print(f"{prefix} {result.name}: {result.detail}")


def sync_then_check() -> int:
    check_context_handoff_governance(sync=True)
    sync_results = [
        run_command("Antigravity/Gemini/AGY sync write", [sys.executable, "scripts/sync_sdlc_agents.py", "--sync"]),
        run_command("Codex/OpenAI sync write", [sys.executable, "scripts/sync_codex_agents.py", "--sync"]),
        run_command("Claude Code <-> AGY CLI Parity sync write", [sys.executable, "scripts/sync_claude_agy_parity.py", "--sync"]),
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
