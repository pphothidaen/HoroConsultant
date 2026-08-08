#!/usr/bin/env python3
"""
scripts/sync_sdlc_agents.py
============================
Antigravity CLI Agent & Skill Synchronizer.

Primary Specification Source:
  - .antigravity/agents/*.agent (Native Antigravity YAML agent format)

Downstream & Global Targets:
  - .agents/agents/*/agent.md & agent.json (Workspace Customization Engine)
  - ~/.gemini/config/agents/ & ~/.agy-account-1/.gemini/config/agents/ (Global CLI Customization Engine)

Usage:
  python3 scripts/sync_sdlc_agents.py --sync
  python3 scripts/sync_sdlc_agents.py --check
  python3 scripts/sync_sdlc_agents.py --list
"""

from __future__ import annotations

import os
import sys
import json
import yaml
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
ANTIGRAVITY_DIR = ROOT / ".antigravity" / "agents"
AGENTS_DIR = ROOT / ".agents" / "agents"


def normalize_agent_name(raw_name: str) -> str:
    """Normalizes agent name to standard underscore format."""
    return raw_name.strip().replace("-", "_")


def parse_antigravity_agent(filepath: Path) -> Dict[str, Any]:
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


def build_antigravity_yaml(agent_data: Dict[str, Any], override_name: str | None = None) -> str:
    """Converts canonical agent dict to Antigravity .agent YAML format."""
    name = override_name or agent_data["name"]
    display_name = agent_data.get("display_name", agent_data.get("role", name))
    model = agent_data.get("model", "Gemini 3.6 Flash")
    thinking = agent_data.get("thinking", False) or "High" in str(agent_data.get("thinking_effort", ""))

    ag_dict = {
        "name": name,
        "display_name": display_name if isinstance(display_name, str) else name,
        "description": agent_data.get("description", ""),
        "model": model,
        "effort": "high" if thinking else "standard",
        "thinking": bool(thinking),
        "system_prompt": agent_data.get("system_prompt", ""),
        "tools": agent_data.get("tools", []),
        "fallback_agent": agent_data.get("fallback_agent", "orchestrator" if name != "orchestrator" else "default")
    }

    return yaml.dump(ag_dict, sort_keys=False, allow_unicode=True)


def build_agent_json(agent_data: Dict[str, Any]) -> str:
    """Converts agent dict to JSON spec format for Antigravity CLI."""
    name = agent_data["name"]
    role = agent_data.get("display_name", name)
    thinking_effort = "High" if agent_data.get("thinking") else "Standard"

    json_dict = {
        "name": name,
        "role": role,
        "model": agent_data.get("model", "Gemini 3.6 Flash"),
        "thinking_effort": thinking_effort,
        "description": agent_data.get("description", ""),
        "tools": agent_data.get("tools", []),
        "system_prompt": agent_data.get("system_prompt", "")
    }
    return json.dumps(json_dict, indent=2, ensure_ascii=False)


def build_agent_md(agent_data: Dict[str, Any]) -> str:
    """Converts canonical agent dict to Markdown agent.md with YAML frontmatter."""
    name = agent_data["name"]
    role = agent_data.get("display_name", name)

    frontmatter = {
        "name": name,
        "display_name": role,
        "description": agent_data.get("description", ""),
        "role": role,
        "model": agent_data.get("model", "Gemini 3.6 Flash"),
        "thinking_effort": "High" if agent_data.get("thinking") else "Standard",
        "tools": agent_data.get("tools", [])
    }

    yaml_header = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    body = agent_data.get("system_prompt", f"System Prompt for {name} agent.")
    return f"---\n{yaml_header}\n---\n\n{body}\n"


def load_all_primary_agents() -> Dict[str, Dict[str, Any]]:
    """Loads all primary Antigravity agent specifications from .antigravity/agents/."""
    agents: Dict[str, Dict[str, Any]] = {}

    if ANTIGRAVITY_DIR.exists():
        for f in ANTIGRAVITY_DIR.glob("*.agent"):
            try:
                ag_data = parse_antigravity_agent(f)
                name = ag_data["name"]
                if name not in agents or len(ag_data.get("system_prompt", "")) > len(agents[name].get("system_prompt", "")):
                    agents[name] = ag_data
            except Exception as e:
                print(f"[WARNING] Error reading {f}: {e}")

    return agents


def sync_skills() -> None:
    """Synchronizes agent skills from .agents/skills/ into .antigravity/skills/."""
    AGENTS_SKILLS_DIR = ROOT / ".agents" / "skills"
    ANTIGRAVITY_SKILLS_DIR = ROOT / ".antigravity" / "skills"

    ANTIGRAVITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    if AGENTS_SKILLS_DIR.exists():
        for skill_dir in AGENTS_SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    target_dir = ANTIGRAVITY_SKILLS_DIR / skill_dir.name
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_md = target_dir / "SKILL.md"
                    with open(skill_md, "r", encoding="utf-8") as f_in:
                        content = f_in.read()
                    with open(target_md, "w", encoding="utf-8") as f_out:
                        f_out.write(content)


def sync_all_agents(check_only: bool = False, list_only: bool = False) -> bool:
    """Syncs, checks, or lists agent definitions for Antigravity CLI."""
    ANTIGRAVITY_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    agents = load_all_primary_agents()
    print(f"[INFO] Discovered {len(agents)} Antigravity Agent specifications in .antigravity/agents/")

    if list_only:
        print("\n==========================================================================================")
        print(f"{'AGENT NAME':<24} | {'ROLE / DISPLAY NAME':<40} | {'MODEL':<20}")
        print("==========================================================================================")
        for name, data in sorted(agents.items()):
            role = data.get("display_name") or name
            model = data.get("model", "Gemini 3.6 Flash")
            print(f"{name:<24} | {role:<40} | {model:<20}")
        print("==========================================================================================\n")
        return True

    mismatches = 0

    if not check_only:
        # Clean loose files directly in .agents/agents/
        for f in AGENTS_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass

    for name, data in sorted(agents.items()):
        ag_filename_underscore = ANTIGRAVITY_DIR / f"{name}.agent"
        ag_filename_hyphen = ANTIGRAVITY_DIR / f"{name.replace('_', '-')}.agent"
        agent_md_dir = AGENTS_DIR / name
        agent_md_file = agent_md_dir / "agent.md"
        top_level_agent_md = AGENTS_DIR / f"{name}.md"

        if check_only:
            if not ag_filename_underscore.exists() and not ag_filename_hyphen.exists():
                print(f"[ERROR] Missing Antigravity agent file for '{name}' in .antigravity/agents/")
                mismatches += 1
            if not agent_md_file.exists() and not top_level_agent_md.exists():
                print(f"[ERROR] Missing downstream markdown agent file for '{name}' in .agents/agents/")
                mismatches += 1
        else:
            # Generate Antigravity YAML content (both underscore & hyphenated versions)
            ag_yaml = build_antigravity_yaml(data, override_name=name)
            with open(ag_filename_underscore, "w", encoding="utf-8") as f:
                f.write(ag_yaml)
            with open(ag_filename_hyphen, "w", encoding="utf-8") as f:
                f.write(ag_yaml)

            # Generate Downstream Markdown & JSON inside dedicated folder & top-level
            agent_md_dir.mkdir(parents=True, exist_ok=True)
            agent_md_content = build_agent_md(data)
            agent_json_content = build_agent_json(data)

            with open(agent_md_file, "w", encoding="utf-8") as f:
                f.write(agent_md_content)
            with open(top_level_agent_md, "w", encoding="utf-8") as f:
                f.write(agent_md_content)

            with open(agent_md_dir / "agent.json", "w", encoding="utf-8") as f:
                f.write(agent_json_content)
            with open(AGENTS_DIR / f"{name}.json", "w", encoding="utf-8") as f:
                f.write(agent_json_content)

            print(f"[OK] Synced Antigravity agent '{name}' -> .antigravity & .agents")

    if not check_only:
        sync_skills()
        print("[OK] Synchronized all Agent Skills into .antigravity/skills/")

        # Generate agents.json registration manifest
        agents_entries = [{"name": name, "path": f"{name}/agent.md"} for name in sorted(agents.keys())]
        agents_json_content = json.dumps({"entries": agents_entries}, indent=2, ensure_ascii=False)

        with open(ROOT / ".agents" / "agents.json", "w", encoding="utf-8") as f:
            f.write(agents_json_content)
        with open(ROOT / ".agents" / "agents" / "agents.json", "w", encoding="utf-8") as f:
            f.write(agents_json_content)
        print("[OK] Synchronized agents.json registration manifests")

        # Sync to Global CLI config directories
        global_dirs = [
            Path.home() / ".gemini" / "config" / "agents",
            Path.home() / ".agy-account-1" / ".gemini" / "config" / "agents"
        ]
        for g_dir in global_dirs:
            g_dir.mkdir(parents=True, exist_ok=True)
            for item in (ROOT / ".agents" / "agents").iterdir():
                dst = g_dir / item.name
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
        print("[OK] Synchronized agent definitions to Global CLI config locations (~/.gemini/config/agents)")

    if check_only:
        if mismatches == 0:
            print("[OK] All Antigravity Agent definitions are 100% synchronized!")
            return True
        else:
            print(f"[ERROR] Found {mismatches} agent synchronization issues.")
            return False
    else:
        print("[OK] Successfully synchronized all Antigravity agent definitions!")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity CLI Agent Synchronizer")
    parser.add_argument("--sync", action="store_true", help="Perform synchronization")
    parser.add_argument("--check", action="store_true", help="Check synchronization status without writing")
    parser.add_argument("--list", action="store_true", help="List all canonical agents")
    args = parser.parse_args()

    if not args.sync and not args.check and not args.list:
        args.sync = True

    success = sync_all_agents(check_only=args.check, list_only=args.list)
    sys.exit(0 if success else 1)
