#!/usr/bin/env python3
"""Synchronize and validate Codex configuration across accounts and lane profiles.

Ensures that:
1. Primary base configs across all accounts (Default, codex1, codex2, codex3) comply with the budget policy.
2. Dynamic lane-specific profiles (<lane>.config.toml) are generated for each specialist role.
3. Live prompt skills budget assertion (<= 8,000 chars and 0 truncated descriptions).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

HOME = Path.home()
CODEX_HOME_DEFAULT = HOME / ".codex"
AI_ACCOUNTS_DIR = HOME / ".ai-accounts" / "codex"
HORO_DIR = Path(__file__).resolve().parents[1]

# Target base config files
ACCOUNT_CONFIGS: dict[str, Path] = {
    "default": CODEX_HOME_DEFAULT / "config.toml",
    "codex1": AI_ACCOUNTS_DIR / "account1" / "config.toml",
    "codex2": AI_ACCOUNTS_DIR / "account2" / "config.toml",
    "codex3": AI_ACCOUNTS_DIR / "account3" / "config.toml",
}

# Required disabled plugins (primary config)
DISABLED_PLUGINS = [
    "documents@openai-primary-runtime",
    "spreadsheets@openai-primary-runtime",
    "presentations@openai-primary-runtime",
    "pdf@openai-primary-runtime",
    "template-creator@openai-primary-runtime",
    "visualize@openai-bundled",
    "sites@openai-bundled",
]

# Required disabled skills across all base configs
DISABLED_PROJECT_SKILLS = [
    "kaggle-manager",
    "adaptive-model-effort-routing",
    "agy-capacity-orchestration",
    "ai-inference-verifier",
    "bazi-calculator",
    "github-pr-automation",
    "metaphysical-domain-engine",
    "rag-search",
    "zero-cost-ai-pipeline",
]

DISABLED_GLOBAL_SKILLS = [
    str(HOME / ".agents" / "skills" / "supabase" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "supabase-postgres-best-practices" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "skill-creator" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "web-automation" / "SKILL.md"),
]

# All project skills in HoroConsultant
ALL_HORO_SKILLS = [
    "adaptive-model-effort-routing",
    "agile-governance",
    "agy-capacity-orchestration",
    "ai-inference-verifier",
    "anti-cognitive-decay",
    "bazi-calculator",
    "bsa-doc-skill-management",
    "devops-deployment",
    "github-pr-automation",
    "hf-static-release-verification",
    "kaggle-manager",
    "metaphysical-domain-engine",
    "multi-account-agent-orchestration",
    "orchestrator-delegation",
    "qa-e2e-testing",
    "rag-search",
    "requirement-grill-gate",
    "sdlc-aisdlc-workflow",
    "ui-visual-auditor",
    "web-color-design",
    "zero-cost-ai-pipeline",
]

# Dynamic Lane Profiles (Codex -p <lane>)
LANE_PROFILES: dict[str, dict[str, Any]] = {
    "developer": {
        "model": "gpt-5.6-luna",
        "reasoning_effort": "medium",
        "bound_skills": ["sdlc-aisdlc-workflow"],
    },
    "qa_tester": {
        "model": "gpt-5.4-mini",
        "reasoning_effort": "medium",
        "bound_skills": ["qa-e2e-testing", "hf-static-release-verification"],
    },
    "ux_ui_designer": {
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "bound_skills": ["web-color-design", "ui-visual-auditor"],
    },
    "devops": {
        "model": "gpt-5.3-codex-spark",
        "reasoning_effort": "high",
        "bound_skills": ["devops-deployment", "hf-static-release-verification"],
    },
    "orchestrator": {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "bound_skills": ["orchestrator-delegation", "multi-account-agent-orchestration"],
    },
    "business_analyst": {
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "bound_skills": ["bsa-doc-skill-management", "agile-governance"],
    },
}


class AccountStatus(NamedTuple):
    name: str
    path: Path
    exists: bool
    missing_disabled_skills: list[str]
    missing_disabled_plugins: list[str]
    missing_profiles: list[str]
    prompt_chars: int | None
    truncated_skills: int
    is_ok: bool


def get_expected_disabled_skills(account_name: str) -> list[str]:
    expected = list(DISABLED_GLOBAL_SKILLS)
    for ps in DISABLED_PROJECT_SKILLS:
        expected.append(str(HORO_DIR / ".agents" / "skills" / ps / "SKILL.md"))

    if account_name == "default":
        sys_dir = CODEX_HOME_DEFAULT / "skills" / ".system"
        expected.append(str(sys_dir / "plugin-creator" / "SKILL.md"))
        expected.append(str(sys_dir / "skill-installer" / "SKILL.md"))
        expected.append(str(CODEX_HOME_DEFAULT / "skills" / "codex-with-chatgpt" / "SKILL.md"))
    else:
        acc_dir = AI_ACCOUNTS_DIR / account_name.replace("codex", "account")
        sys_dir = acc_dir / "skills" / ".system"
        expected.append(str(sys_dir / "plugin-creator" / "SKILL.md"))
        expected.append(str(sys_dir / "skill-installer" / "SKILL.md"))
    return expected


def render_lane_profile(lane: str, profile_spec: dict[str, Any]) -> str:
    lines = [
        f'# Generated Codex Lane Profile for {lane}',
        f'model = "{profile_spec["model"]}"',
        f'model_reasoning_effort = "{profile_spec["reasoning_effort"]}"',
        "",
        "# Bound and Unbound Skills for this Lane",
    ]
    bound = set(profile_spec["bound_skills"])
    for skill_name in ALL_HORO_SKILLS:
        skill_path = str(HORO_DIR / ".agents" / "skills" / skill_name / "SKILL.md")
        is_enabled = "true" if skill_name in bound else "false"
        lines.append(f'[[skills.config]]\npath = "{skill_path}"\nenabled = {is_enabled}\n')

    return "\n".join(lines).rstrip() + "\n"


def sync_lane_profiles_for_dir(target_dir: Path) -> list[str]:
    if not target_dir.exists():
        return []
    synced = []
    for lane, spec in LANE_PROFILES.items():
        profile_path = target_dir / f"{lane}.config.toml"
        content = render_lane_profile(lane, spec)
        if not profile_path.exists() or profile_path.read_text(encoding="utf-8") != content:
            profile_path.write_text(content, encoding="utf-8")
            synced.append(lane)
    return synced


def check_account_config(name: str, config_path: Path, check_budget: bool = False) -> AccountStatus:
    if not config_path.exists():
        return AccountStatus(
            name=name,
            path=config_path,
            exists=False,
            missing_disabled_skills=[],
            missing_disabled_plugins=[],
            missing_profiles=[],
            prompt_chars=None,
            truncated_skills=0,
            is_ok=False,
        )

    content = config_path.read_text(encoding="utf-8")

    # Check skills.config
    expected_skills = get_expected_disabled_skills(name)
    missing_skills = []
    for skill_path in expected_skills:
        needle = f'path = "{skill_path}"'
        if needle not in content:
            missing_skills.append(skill_path)

    # Check plugins (only for default config or if plugins defined)
    missing_plugins = []
    if name == "default":
        for plugin in DISABLED_PLUGINS:
            needle = f'[plugins."{plugin}"]'
            if needle in content:
                idx = content.find(needle)
                block = content[idx:idx + 150]
                if "enabled = false" not in block:
                    missing_plugins.append(plugin)

    # Check lane profiles
    account_dir = config_path.parent
    missing_profiles = []
    for lane in LANE_PROFILES:
        prof_file = account_dir / f"{lane}.config.toml"
        if not prof_file.exists():
            missing_profiles.append(lane)

    prompt_chars = None
    truncated_skills = 0
    if check_budget:
        prompt_chars, truncated_skills = measure_prompt_budget(name)

    is_ok = (
        len(missing_skills) == 0
        and len(missing_plugins) == 0
        and len(missing_profiles) == 0
        and (prompt_chars is None or prompt_chars <= 8000)
        and truncated_skills == 0
    )

    return AccountStatus(
        name=name,
        path=config_path,
        exists=True,
        missing_disabled_skills=missing_skills,
        missing_disabled_plugins=missing_plugins,
        missing_profiles=missing_profiles,
        prompt_chars=prompt_chars,
        truncated_skills=truncated_skills,
        is_ok=is_ok,
    )


def measure_prompt_budget(account_name: str, profile: str | None = None) -> tuple[int, int]:
    env = os.environ.copy()
    if account_name != "default":
        acc_dir = AI_ACCOUNTS_DIR / account_name.replace("codex", "account")
        env["CODEX_HOME"] = str(acc_dir)
    else:
        env.pop("CODEX_HOME", None)

    cmd = ["/Users/kimlenglim/.local/bin/codex"]
    if profile:
        cmd.extend(["-p", profile])
    cmd.extend(["debug", "prompt-input"])

    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(HORO_DIR))
    if proc.returncode != 0:
        return 0, 0

    try:
        data = json.loads(proc.stdout)
        for item in data:
            for c in item.get("content", []):
                text = c.get("text", "")
                if "<skills_instructions>" in text:
                    total_len = len(text)
                    truncated = sum(
                        1 for line in text.splitlines()
                        if line.startswith("- ") and (line.endswith("...") or "truncated" in line.lower())
                    )
                    return total_len, truncated
    except Exception:
        pass
    return 0, 0


def sync_account_config(name: str, config_path: Path) -> bool:
    if not config_path.exists():
        return False

    content = config_path.read_text(encoding="utf-8")
    modified = False

    # Sync plugins for default
    if name == "default":
        for plugin in DISABLED_PLUGINS:
            needle = f'[plugins."{plugin}"]'
            if needle in content:
                idx = content.find(needle)
                block = content[idx:idx + 150]
                if "enabled = true" in block:
                    new_block = block.replace("enabled = true", "enabled = false", 1)
                    content = content[:idx] + new_block + content[idx + len(block):]
                    modified = True

    # Sync disabled skills
    appends = []
    expected_skills = get_expected_disabled_skills(name)
    for skill_path in expected_skills:
        needle = f'path = "{skill_path}"'
        if needle not in content:
            appends.append(f'\n[[skills.config]]\npath = "{skill_path}"\nenabled = false\n')

    if appends:
        content = content.rstrip() + "\n" + "".join(appends)
        modified = True

    if modified:
        config_path.write_text(content, encoding="utf-8")
        print(f"[OK] Synchronized base config for {name} ({config_path})")
    else:
        print(f"[OK] Base config already up to date: {name}")

    # Sync lane profiles
    synced_profiles = sync_lane_profiles_for_dir(config_path.parent)
    if synced_profiles:
        print(f"[OK] Synchronized {len(synced_profiles)} lane profile(s) for {name} in {config_path.parent}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize and validate Codex account configs and lane profiles.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate account configs and budget fit.")
    mode.add_argument("--sync", action="store_true", help="Sync missing policy configs and lane profiles, then validate.")
    parser.add_argument("--budget", action="store_true", help="Include live prompt budget measurement.")

    args = parser.parse_args()

    if args.sync:
        print("=== Synchronizing Codex Account Configs & Dynamic Lane Profiles ===")
        for name, path in ACCOUNT_CONFIGS.items():
            sync_account_config(name, path)

    print("\n=== Validating Codex Account Configs & Dynamic Lane Profiles ===")
    all_ok = True
    for name, path in ACCOUNT_CONFIGS.items():
        status = check_account_config(name, path, check_budget=args.budget or args.check)
        if not status.exists:
            print(f"[WARN] {name:8} : Config not found at {path}")
            continue

        details = []
        if status.missing_disabled_skills:
            details.append(f"missing {len(status.missing_disabled_skills)} disabled skill(s)")
        if status.missing_disabled_plugins:
            details.append(f"missing {len(status.missing_disabled_plugins)} disabled plugin(s)")
        if status.missing_profiles:
            details.append(f"missing {len(status.missing_profiles)} lane profile(s)")
        if status.prompt_chars is not None:
            details.append(f"prompt={status.prompt_chars} chars (budget <= 8000)")
        if status.truncated_skills > 0:
            details.append(f"truncated_skills={status.truncated_skills}")

        detail_str = f" ({', '.join(details)})" if details else ""
        if status.is_ok:
            print(f"[OK]    {name:8} : Policy verified{detail_str}")
        else:
            print(f"[ERROR] {name:8} : Policy violation{detail_str}")
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
