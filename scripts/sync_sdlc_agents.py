#!/usr/bin/env python3
"""
scripts/sync_sdlc_agents.py
============================
Antigravity CLI Agent & Skill Synchronizer.

Primary Specification Source:
  - .agents/agents/*/agent.json (Canonical workspace agent definitions)

Downstream & Global Targets:
  - .antigravity/agents/*.agent (Generated Antigravity YAML agent format)
  - .agents/agents/*/agent.md and loose JSON/Markdown outputs
  - ~/.gemini/config/agents/ & ~/.agy-account-1/.gemini/config/agents/ (Global CLI Customization Engine)

Usage:
  python3 scripts/sync_sdlc_agents.py --sync
  python3 scripts/sync_sdlc_agents.py --check
  python3 scripts/sync_sdlc_agents.py --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANTIGRAVITY_DIR = ROOT / ".antigravity" / "agents"
AGENTS_DIR = ROOT / ".agents" / "agents"
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9_-]+")


def normalize_agent_name(raw_name: str) -> str:
    """Normalizes agent name to standard underscore format."""
    return raw_name.strip().replace("-", "_")


def is_safe_identifier(value: object) -> bool:
    """Accept only path-safe lowercase role and tool identifiers."""
    return isinstance(value, str) and IDENTIFIER_PATTERN.fullmatch(value) is not None


def parse_antigravity_agent(filepath: Path) -> dict[str, Any]:
    """Parses a Google Antigravity .agent YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    name = normalize_agent_name(data.get("name", filepath.stem))
    return {
        "name": name,
        "display_name": data.get("display_name", name),
        "description": data.get("description", ""),
        "model": data.get("model", "Gemini 3.6 Flash"),
        "effort": data.get("effort", "standard"),
        "thinking": bool(data.get("thinking", False)),
        "system_prompt": data.get("system_prompt", ""),
        "tools": data.get("tools", []),
        "fallback_agent": data.get("fallback_agent", "orchestrator" if name != "orchestrator" else "default")
    }


def build_antigravity_yaml(agent_data: dict[str, Any], override_name: str | None = None) -> str:
    """Converts canonical agent dict to Antigravity .agent YAML format."""
    name = override_name or agent_data["name"]
    display_name = agent_data.get("display_name", agent_data.get("role", name))
    model = agent_data.get("model", "Gemini 3.6 Flash")
    effort = str(agent_data.get("effort", agent_data.get("thinking_effort", "standard"))).lower()
    thinking = (
        agent_data["thinking"]
        if "thinking" in agent_data
        else effort in {"high", "xhigh", "max"}
    )

    ag_dict = {
        "name": name,
        "display_name": display_name if isinstance(display_name, str) else name,
        "description": agent_data.get("description", ""),
        "model": model,
        "effort": effort,
        "thinking": bool(thinking),
        "system_prompt": agent_data.get("system_prompt", ""),
        "tools": agent_data.get("tools", []),
        "fallback_agent": agent_data.get("fallback_agent", "orchestrator" if name != "orchestrator" else "default")
    }

    return yaml.dump(ag_dict, sort_keys=False, allow_unicode=True)


def build_agent_json(agent_data: dict[str, Any]) -> str:
    """Converts agent dict to JSON spec format for Antigravity CLI."""
    name = agent_data["name"]
    role = agent_data.get("role", agent_data.get("display_name", name))
    thinking_effort = str(
        agent_data.get(
            "thinking_effort",
            agent_data.get("effort", "high" if agent_data.get("thinking") else "standard"),
        )
    ).title()

    json_dict = {
        "name": name,
        "role": role,
        "model": agent_data.get("model", "Gemini 3.6 Flash"),
        "thinking_effort": thinking_effort,
        "description": agent_data.get("description", ""),
        "tools": agent_data.get("tools", []),
        "system_prompt": agent_data.get("system_prompt", ""),
        "thinking": agent_data.get("thinking", False),
        "fallback_agent": agent_data.get(
            "fallback_agent", "orchestrator" if name != "orchestrator" else "default"
        ),
    }
    return json.dumps(json_dict, indent=2, ensure_ascii=False)


def build_agent_md(agent_data: dict[str, Any]) -> str:
    """Converts canonical agent dict to Markdown agent.md with YAML frontmatter."""
    name = agent_data["name"]
    role = agent_data.get("role", agent_data.get("display_name", name))

    frontmatter = {
        "name": name,
        "display_name": role,
        "description": agent_data.get("description", ""),
        "role": role,
        "model": agent_data.get("model", "Gemini 3.6 Flash"),
        "thinking_effort": str(
            agent_data.get(
                "thinking_effort",
                agent_data.get("effort", "high" if agent_data.get("thinking") else "standard"),
            )
        ).title(),
        "tools": agent_data.get("tools", []),
        "thinking": agent_data.get("thinking", False),
        "fallback_agent": agent_data.get(
            "fallback_agent", "orchestrator" if name != "orchestrator" else "default"
        ),
    }

    yaml_header = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    body = str(agent_data.get("system_prompt", f"System Prompt for {name} agent."))
    if name == "default":
        body = body.rstrip()
    return f"---\n{yaml_header}\n---\n\n{body}\n"


def load_all_primary_agents() -> dict[str, dict[str, Any]]:
    """Load nested canonical JSON definitions, never generated YAML or loose JSON."""
    if not AGENTS_DIR.is_dir():
        raise ValueError(f"canonical agents directory is missing: {AGENTS_DIR}")
    source_files = sorted(AGENTS_DIR.glob("*/agent.json"))
    if not source_files:
        raise ValueError(f"canonical agents directory has no nested agent.json files: {AGENTS_DIR}")
    agents: dict[str, dict[str, Any]] = {}
    for filepath in source_files:
        try:
            if not is_safe_identifier(filepath.parent.name):
                raise ValueError("role directory is not a safe identifier")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("definition must be a JSON object")
            required_strings = (
                "name",
                "role",
                "model",
                "thinking_effort",
                "description",
                "system_prompt",
            )
            for field in required_strings:
                value = data.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"missing nonempty string '{field}'")
            if not is_safe_identifier(data["name"]):
                raise ValueError("'name' is not a safe identifier")
            tools = data.get("tools")
            if (
                not isinstance(tools, list)
                or not tools
                or any(not is_safe_identifier(tool) for tool in tools)
            ):
                raise ValueError("'tools' must be a nonempty list of safe identifiers")
            if "thinking" in data and type(data["thinking"]) is not bool:
                raise ValueError("optional 'thinking' must be boolean")
            if "fallback_agent" in data and not is_safe_identifier(data["fallback_agent"]):
                raise ValueError("optional 'fallback_agent' must be a safe identifier")
            name = normalize_agent_name(data["name"])
            if name != normalize_agent_name(filepath.parent.name):
                raise ValueError(
                    f"declared name '{name}' does not match directory '{filepath.parent.name}'"
                )
            if name in agents:
                raise ValueError(f"duplicate canonical definition for '{name}'")
            agents[name] = data
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid canonical agent definition {filepath}: {error}") from error
    return agents


def sync_skills(check_only: bool = False) -> int:
    """Synchronizes and validates agent skills from .agents/skills/ into .antigravity/skills/."""
    AGENTS_SKILLS_DIR = ROOT / ".agents" / "skills"
    ANTIGRAVITY_SKILLS_DIR = ROOT / ".antigravity" / "skills"

    mismatches = 0

    if not AGENTS_SKILLS_DIR.is_dir():
        print(f"[ERROR] Canonical skills directory is missing: {AGENTS_SKILLS_DIR}")
        return 1
    if not check_only:
        ANTIGRAVITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(AGENTS_SKILLS_DIR.iterdir()):
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                print(f"[ERROR] Missing SKILL.md in {skill_dir}")
                mismatches += 1
                continue

            content = skill_md.read_text(encoding="utf-8")
            # Parse frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1]) or {}
                        skill_name = fm.get("name", "")
                        skill_desc = fm.get("description", "")
                        if not skill_name:
                            print(f"[ERROR] Skill in {skill_dir.name} missing 'name' in frontmatter")
                            mismatches += 1
                        if not skill_desc:
                            print(f"[ERROR] Skill '{skill_dir.name}' missing 'description' in frontmatter")
                            mismatches += 1
                        elif len(skill_desc.strip()) > 100:
                            print(
                                f"[ERROR] Skill '{skill_name}' description exceeds 100 chars "
                                f"({len(skill_desc.strip())} chars). Keep concise to fit context budget!"
                            )
                            mismatches += 1
                    except Exception as error:
                        print(f"[ERROR] Invalid YAML frontmatter in {skill_md}: {error}")
                        mismatches += 1

            target_dir = ANTIGRAVITY_SKILLS_DIR / skill_dir.name
            target_md = target_dir / "SKILL.md"

            if check_only:
                if not target_md.exists():
                    print(f"[ERROR] Missing synced SKILL.md in .antigravity/skills/{skill_dir.name}/")
                    mismatches += 1
                elif target_md.read_text(encoding="utf-8") != content:
                    print(f"[ERROR] Synced SKILL.md mismatch in .antigravity/skills/{skill_dir.name}/")
                    mismatches += 1
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                target_md.write_text(content, encoding="utf-8")

    return mismatches


def sync_all_agents(check_only: bool = False, list_only: bool = False) -> bool:
    """Syncs, checks, or lists agent definitions for Antigravity CLI."""
    try:
        agents = load_all_primary_agents()
    except ValueError as error:
        print(f"[ERROR] {error}")
        return False
    if not check_only:
        ANTIGRAVITY_DIR.mkdir(parents=True, exist_ok=True)
    elif not ANTIGRAVITY_DIR.is_dir():
        print(f"[ERROR] Generated Antigravity agents directory is missing: {ANTIGRAVITY_DIR}")
        return False

    print(f"[INFO] Discovered {len(agents)} canonical nested agent definitions in .agents/agents/")

    if list_only:
        print("\n==========================================================================================")
        print(f"{'AGENT NAME':<24} | {'ROLE / DISPLAY NAME':<40} | {'MODEL':<20}")
        print("==========================================================================================")
        for name, data in sorted(agents.items()):
            role = data.get("role", data.get("display_name", name))
            model = data.get("model", "Gemini 3.6 Flash")
            print(f"{name:<24} | {role:<40} | {model:<20}")
        print("==========================================================================================\n")
        return True

    mismatches = 0

    for name, data in sorted(agents.items()):
        ag_filename_underscore = ANTIGRAVITY_DIR / f"{name}.agent"
        ag_filename_hyphen = ANTIGRAVITY_DIR / f"{name.replace('_', '-')}.agent"
        agent_md_dir = AGENTS_DIR / name
        agent_md_file = agent_md_dir / "agent.md"
        top_level_agent_md = AGENTS_DIR / f"{name}.md"
        top_level_agent_json = AGENTS_DIR / f"{name}.json"
        generated = {
            ag_filename_underscore: build_antigravity_yaml(data, override_name=name),
            ag_filename_hyphen: build_antigravity_yaml(data, override_name=name),
            agent_md_file: build_agent_md(data),
            top_level_agent_md: build_agent_md(data),
            top_level_agent_json: build_agent_json(data),
        }

        if check_only:
            for output_path, expected_content in generated.items():
                try:
                    actual_content = output_path.read_text(encoding="utf-8")
                except OSError:
                    print(f"[ERROR] Missing generated agent artifact: {output_path}")
                    mismatches += 1
                    continue
                if actual_content != expected_content:
                    print(f"[ERROR] Generated agent artifact drift: {output_path}")
                    mismatches += 1
        else:
            # The nested agent.json is the read-only canonical input. Only
            # YAML, Markdown, and loose JSON outputs are generated here.
            agent_md_dir.mkdir(parents=True, exist_ok=True)
            for output_path, expected_content in generated.items():
                output_path.write_text(expected_content, encoding="utf-8")

            print(f"[OK] Synced Antigravity agent '{name}' -> .antigravity & .agents")

    skill_mismatches = sync_skills(check_only=check_only)
    mismatches += skill_mismatches

    agents_entries = [{"name": name, "path": f"{name}/agent.md"} for name in sorted(agents)]
    agents_json_content = json.dumps({"entries": agents_entries}, indent=2, ensure_ascii=False)
    manifest_paths = (ROOT / ".agents" / "agents.json", AGENTS_DIR / "agents.json")

    if check_only:
        for manifest_path in manifest_paths:
            try:
                actual_content = manifest_path.read_text(encoding="utf-8")
            except OSError:
                print(f"[ERROR] Missing generated agent manifest: {manifest_path}")
                mismatches += 1
                continue
            if actual_content != agents_json_content:
                print(f"[ERROR] Generated agent manifest drift: {manifest_path}")
                mismatches += 1
    else:
        print("[OK] Synchronized all Agent Skills into .antigravity/skills/")
        for manifest_path in manifest_paths:
            manifest_path.write_text(agents_json_content, encoding="utf-8")
        print("[OK] Synchronized agents.json registration manifests")

        # Sync generated outputs to global CLI locations without deleting any
        # existing directories or unowned files.
        global_dirs = [
            Path.home() / ".gemini" / "config" / "agents",
            Path.home() / ".agy-account-1" / ".gemini" / "config" / "agents"
        ]
        for g_dir in global_dirs:
            g_dir.mkdir(parents=True, exist_ok=True)
            for name, data in agents.items():
                global_role_dir = g_dir / name
                global_role_dir.mkdir(parents=True, exist_ok=True)
                (global_role_dir / "agent.md").write_text(build_agent_md(data), encoding="utf-8")
                (global_role_dir / "agent.json").write_text(build_agent_json(data), encoding="utf-8")
                (g_dir / f"{name}.md").write_text(build_agent_md(data), encoding="utf-8")
                (g_dir / f"{name}.json").write_text(build_agent_json(data), encoding="utf-8")
            (g_dir / "agents.json").write_text(agents_json_content, encoding="utf-8")
        print("[OK] Synchronized agent definitions to Global CLI config locations (~/.gemini/config/agents)")

    if check_only:
        if mismatches == 0:
            print("[OK] All Antigravity Agent & Skill definitions are 100% synchronized and within context budget!")
            return True
        else:
            print(f"[ERROR] Found {mismatches} agent / skill synchronization issues.")
            return False
    else:
        print("[OK] Successfully synchronized all Antigravity agent & skill definitions!")
        return True


def main(argv: list[str] | None = None) -> int:
    """Run the canonical Python synchronizer for every advertised CLI action."""
    parser = argparse.ArgumentParser(description="Antigravity CLI Agent Synchronizer")
    parser.add_argument("--sync", action="store_true", help="Perform synchronization")
    parser.add_argument("--check", action="store_true", help="Check synchronization status without writing")
    parser.add_argument("--list", action="store_true", help="List all canonical agents")
    parser.add_argument(
        "--use-python",
        action="store_true",
        help="Compatibility no-op; Python is always the canonical implementation",
    )
    args = parser.parse_args(argv)

    if not args.sync and not args.check and not args.list:
        args.sync = True

    success = sync_all_agents(check_only=args.check, list_only=args.list)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
