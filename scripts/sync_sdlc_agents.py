#!/usr/bin/env python3
"""
scripts/sync_sdlc_agents.py
============================
Universal Development & SDLC Agent Sync Script.

Synchronizes agent definitions across:
  - .agents/agents/*/agent.md (Canonical Markdown frontmatter)
  - .antigravity/agents/*.agent (Google Antigravity YAML agent format)
  - .claude/agents/*.json (Anthropic Claude Code JSON agent format)

Usage:
  python3 scripts/sync_sdlc_agents.py --sync
  python3 scripts/sync_sdlc_agents.py --check
"""

from __future__ import annotations

import os
import sys
import json
import yaml
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".agents" / "agents"
ANTIGRAVITY_DIR = ROOT / ".antigravity" / "agents"
CLAUDE_AGENTS_DIR = ROOT / ".claude" / "agents"


def parse_agent_md(filepath: Path) -> dict:
    """Parses frontmatter and content from an agent.md file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        raise ValueError(f"File {filepath} missing YAML frontmatter start ('---')")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter format in {filepath}")

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    frontmatter["body"] = body
    return frontmatter


def build_antigravity_yaml(agent_data: dict) -> str:
    """Converts canonical agent dict to Antigravity .agent YAML format."""
    name = agent_data.get("name", "agent")
    display_name = agent_data.get("display_name", agent_data.get("role", name))
    model = agent_data.get("model", "Gemini 3.6 Flash")
    thinking = "High" in str(agent_data.get("thinking_effort", "")) or agent_data.get("thinking", False)

    tools = agent_data.get("tools", [
        "bazi-calculator",
        "rag-search",
        "bsa-doc-skill-management",
        "qa-e2e-testing",
        "devops-deployment",
        "sdlc-aisdlc-workflow",
        "kaggle-manager"
    ])

    description = agent_data.get("description", f"Role: {agent_data.get('role', name)}. {agent_data.get('body', '')[:120]}...")

    ag_dict = {
        "name": name,
        "display_name": display_name if isinstance(display_name, str) else name,
        "description": description,
        "model": model,
        "effort": "high" if thinking else "standard",
        "thinking": bool(thinking),
        "system_prompt": f"You are the {name} agent for HoroConsultant.\n\nRole: {agent_data.get('role', '')}\n\n{agent_data.get('body', '')}",
        "tools": tools,
        "fallback_agent": "orchestrator" if name != "orchestrator" else "default"
    }

    return yaml.dump(ag_dict, sort_keys=False, allow_unicode=True)


def build_claude_json(agent_data: dict) -> dict:
    """Converts canonical agent dict to Claude Code JSON format."""
    name = agent_data.get("name", "agent")
    return {
        "name": name,
        "role": agent_data.get("role", ""),
        "model": agent_data.get("model", "claude-3-5-sonnet"),
        "thinking_effort": agent_data.get("thinking_effort", "Standard"),
        "description": agent_data.get("description", agent_data.get("body", "")[:200]),
        "tools": agent_data.get("tools", []),
        "system_prompt": agent_data.get("body", "")
    }


def sync_all_agents(check_only: bool = False) -> bool:
    """Syncs or checks agent definitions across all SDLC frameworks."""
    ANTIGRAVITY_DIR.mkdir(parents=True, exist_ok=True)
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    agent_subdirs = [d for d in AGENTS_DIR.iterdir() if d.is_dir()]
    print(f"🔄 Scanning {len(agent_subdirs)} agent directories in .agents/agents/...")

    mismatches = 0

    for agent_dir in agent_subdirs:
        agent_md = agent_dir / "agent.md"
        if not agent_md.exists():
            print(f"⚠️  Missing agent.md in {agent_dir.name}")
            mismatches += 1
            continue

        data = parse_agent_md(agent_md)
        agent_name = data.get("name", agent_dir.name)

        # 1. Antigravity YAML target (generate both underscore and hyphen filenames)
        ag_filename_hyphen = agent_name.replace("_", "-") + ".agent"
        ag_filename_underscore = agent_name.replace("-", "_") + ".agent"
        ag_target_hyphen = ANTIGRAVITY_DIR / ag_filename_hyphen
        ag_target_underscore = ANTIGRAVITY_DIR / ag_filename_underscore
        ag_yaml_content = build_antigravity_yaml(data)

        # 2. Claude Code JSON target
        claude_filename = agent_name + ".json"
        claude_target = CLAUDE_AGENTS_DIR / claude_filename
        claude_json_content = json.dumps(build_claude_json(data), indent=2, ensure_ascii=False)

        if check_only:
            if not ag_target_hyphen.exists() or not ag_target_underscore.exists():
                print(f"❌ Missing Antigravity agent file for {agent_name}")
                mismatches += 1
            if not claude_target.exists():
                print(f"❌ Missing Claude Code agent file: {claude_filename}")
                mismatches += 1
        else:
            with open(ag_target_hyphen, "w", encoding="utf-8") as f:
                f.write(ag_yaml_content)
            with open(ag_target_underscore, "w", encoding="utf-8") as f:
                f.write(ag_yaml_content)
            with open(claude_target, "w", encoding="utf-8") as f:
                f.write(claude_json_content)
            print(f"✅ Synced: {agent_name} -> {ag_filename_hyphen}, {ag_filename_underscore} & {claude_filename}")

    if check_only:
        if mismatches == 0:
            print("✨ All SDLC Agent definitions are 100% synchronized across Antigravity and Claude Code!")
            return True
        else:
            print(f"⚠️ Found {mismatches} synchronization issues.")
            return False
    else:
        print("🎉 Successfully synchronized all SDLC agent definitions!")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal SDLC Agent Synchronizer")
    parser.add_argument("--sync", action="store_true", help="Perform synchronization")
    parser.add_argument("--check", action="store_true", help="Check synchronization status without writing")
    args = parser.parse_args()

    if not args.sync and not args.check:
        args.sync = True

    success = sync_all_agents(check_only=args.check)
    sys.exit(0 if success else 1)
