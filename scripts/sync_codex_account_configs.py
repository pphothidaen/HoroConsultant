#!/usr/bin/env python3
"""Synchronize and validate Codex account skill-context budget policy.

Remote-curated plugins are discovered from each account's local cache and
configuration. Profiles are inert TOML files generated from canonical
HoroConsultant agent definitions; a later new-session ``codex -p <role>``
activation is deliberately outside this script.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _resolve_ai_accounts_home() -> Path:
    current = Path.home()
    for candidate in [current] + list(current.parents):
        if (candidate / ".ai-accounts" / "codex").is_dir():
            return candidate
    for candidate in [current] + list(current.parents):
        if (candidate / ".codex" / "config.toml").is_file():
            return candidate
    for candidate in [current] + list(current.parents):
        if (candidate / ".codex").is_dir():
            return candidate
    return current


HOME = _resolve_ai_accounts_home()
CODEX_HOME_DEFAULT = HOME / ".codex"
AI_ACCOUNTS_DIR = HOME / ".ai-accounts" / "codex"
HORO_DIR = Path(__file__).resolve().parents[1]
CANONICAL_AGENTS_DIR = HORO_DIR / ".agents" / "agents"
CANONICAL_SKILLS_DIR = HORO_DIR / ".agents" / "skills"

ACCOUNT_CONFIGS: dict[str, Path] = {
    "default": CODEX_HOME_DEFAULT / "config.toml",
    "codex1": AI_ACCOUNTS_DIR / "account1" / "config.toml",
    "codex2": AI_ACCOUNTS_DIR / "account2" / "config.toml",
    "codex3": AI_ACCOUNTS_DIR / "account3" / "config.toml",
}

# These non-project sources remain outside canonical role bindings. No
# HoroConsultant skill is default-disabled by this policy.
DISABLED_GLOBAL_SKILLS = (
    str(HOME / ".agents" / "skills" / "supabase" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "supabase-postgres-best-practices" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "skill-creator" / "SKILL.md"),
    str(HOME / ".agents" / "skills" / "web-automation" / "SKILL.md"),
)
SYSTEM_DISABLED_SKILLS = ("plugin-creator", "skill-installer")

REMOTE_CURATED_SUFFIX = "@openai-curated-remote"
SUPERPOWERS_PLUGIN = "superpowers"
SHORTENED_DESCRIPTION_WARNING = (
    "Skill descriptions were shortened to fit the skills context budget"
)
PLUGIN_HEADER = re.compile(
    r'^\s*\[plugins\.(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>[A-Za-z0-9_-]+))\]\s*(?:#.*)?$'
)
CANONICAL_IDENTIFIER = re.compile(r"[a-z0-9_-]+")


@dataclass(frozen=True)
class RoleProfile:
    """A standalone profile derived from one canonical ``agent.json``."""

    name: str
    model: str | None
    reasoning_effort: str | None
    bound_skill_paths: tuple[str, ...]


@dataclass(frozen=True)
class PromptBudgetMeasurement:
    prompt_chars: int | None
    truncated_skills: int
    measurement_error: str | None = None


@dataclass(frozen=True)
class AccountStatus:
    name: str
    path: Path
    exists: bool
    missing_disabled_skills: list[str]
    missing_disabled_plugins: list[str]
    missing_profiles: list[str]
    prompt_chars: int | None
    truncated_skills: int
    measurement_error: str | None
    is_ok: bool


def _account_home(name: str, config_path: Path | None = None) -> Path:
    if config_path is not None:
        return config_path.parent
    if name == "default":
        return CODEX_HOME_DEFAULT
    return AI_ACCOUNTS_DIR / name.replace("codex", "account", 1)


def _remote_cache_roots(account_home: Path) -> list[Path]:
    """Return known cache locations without creating or modifying anything."""
    return [
        account_home / "plugins" / "cache" / "openai-curated-remote",
        account_home / "cache" / "openai-curated-remote",
    ]


def _is_remote_curated_plugin(plugin: str) -> bool:
    return plugin == SUPERPOWERS_PLUGIN or plugin.endswith(REMOTE_CURATED_SUFFIX)


def discover_remote_curated_plugins(cache_roots: list[Path], config_text: str) -> set[str]:
    """Discover remote-curated identities from cache directories and TOML."""
    parsed = tomllib.loads(config_text)  # Fail before a caller writes invalid TOML.
    discovered: set[str] = set()
    plugins = parsed.get("plugins", {})
    if isinstance(plugins, dict):
        for plugin in plugins:
            if isinstance(plugin, str) and _is_remote_curated_plugin(plugin):
                discovered.add(plugin)
    for cache_root in cache_roots:
        if not cache_root.is_dir():
            continue
        for candidate in cache_root.iterdir():
            if candidate.is_dir():
                identity = (
                    SUPERPOWERS_PLUGIN
                    if candidate.name == SUPERPOWERS_PLUGIN
                    else f"{candidate.name}{REMOTE_CURATED_SUFFIX}"
                )
                discovered.add(identity)
    return discovered


def remote_curated_plugins_to_disable(discovered_plugins: set[str]) -> set[str]:
    """Default-disable every discovered remote plugin except exact superpowers."""
    return {
        plugin
        for plugin in discovered_plugins
        if _is_remote_curated_plugin(plugin) and plugin != SUPERPOWERS_PLUGIN
    }


def _plugin_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = PLUGIN_HEADER.match(line.rstrip("\n"))
        if not match:
            continue
        if match.group("quoted") is not None:
            plugin = tomllib.loads(f'key = "{match.group("quoted")}"')["key"]
        else:
            plugin = match.group("bare")
        starts.append((index, plugin))
    blocks: list[tuple[int, int, str]] = []
    for position, (start, plugin) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        for index in range(start + 1, end):
            stripped = lines[index].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                end = index
                break
        blocks.append((start, end, plugin))
    return blocks


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def apply_remote_curated_plugin_policy(config_text: str, discovered_plugins: set[str]) -> str:
    """Disable targets while preserving non-target TOML blocks byte-for-byte."""
    tomllib.loads(config_text)
    targets = remote_curated_plugins_to_disable(discovered_plugins)
    lines = config_text.splitlines(keepends=True)
    found: set[str] = set()
    for start, end, plugin in reversed(_plugin_blocks(lines)):
        if plugin not in targets:
            continue
        found.add(plugin)
        enabled_line = next(
            (
                index
                for index in range(start + 1, end)
                if lines[index].lstrip().startswith("enabled =")
            ),
            None,
        )
        if enabled_line is None:
            lines.insert(end, "enabled = false\n")
        else:
            indent = lines[enabled_line][: len(lines[enabled_line]) - len(lines[enabled_line].lstrip())]
            lines[enabled_line] = f"{indent}enabled = false\n"
    missing = sorted(targets - found)
    if missing:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.append("# HoroConsultant remote-curated plugin budget policy\n")
        for plugin in missing:
            lines.extend(
                (f"[plugins.{_toml_string(plugin)}]\n", "enabled = false\n", "\n")
            )
    updated = "".join(lines)
    # Inline/dotted registrations cannot safely coexist with a newly appended
    # table registration. Never return (or let sync write) malformed TOML.
    tomllib.loads(updated)
    return updated


def get_expected_disabled_skills(account_name: str) -> list[str]:
    account_home = _account_home(account_name)
    return [
        *DISABLED_GLOBAL_SKILLS,
        *(
            str(account_home / "skills" / ".system" / skill / "SKILL.md")
            for skill in SYSTEM_DISABLED_SKILLS
        ),
    ]


def _is_safe_canonical_identifier(value: object) -> bool:
    """Restrict canonical role/tool identifiers before building filesystem paths."""
    return isinstance(value, str) and CANONICAL_IDENTIFIER.fullmatch(value) is not None


def _contained_path(root: Path, *parts: str) -> Path:
    """Resolve a derived path and fail when it escapes its canonical root."""
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"derived path escapes canonical root: {candidate}") from error
    return candidate


def derive_role_profiles(agents_dir: Path, skills_dir: Path) -> dict[str, RoleProfile]:
    """Derive role bindings solely from canonical JSON and ``SKILL.md`` paths."""
    if not agents_dir.is_dir():
        raise ValueError(f"canonical agents directory is unavailable: {agents_dir}")
    if not skills_dir.is_dir():
        raise ValueError(f"canonical skills directory is unavailable: {skills_dir}")
    profiles: dict[str, RoleProfile] = {}
    for agent_path in sorted(agents_dir.glob("*/agent.json")):
        try:
            if not _is_safe_canonical_identifier(agent_path.parent.name):
                raise ValueError(
                    f"unsafe canonical role directory: {agent_path.parent.name}"
                )
            agent: Any = json.loads(agent_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid canonical agent definition: {agent_path.name}") from error
        if not isinstance(agent, dict) or not _is_safe_canonical_identifier(agent.get("name")):
            raise ValueError(f"invalid canonical agent definition: {agent_path.name}")
        if agent["name"] != agent_path.parent.name:
            raise ValueError(
                f"canonical role name does not match directory: {agent['name']}"
            )
        tools = agent.get("tools")
        if not isinstance(tools, list) or not all(_is_safe_canonical_identifier(tool) for tool in tools):
            raise ValueError(f"invalid canonical tools for role {agent['name']}")
        skill_paths: list[str] = []
        for tool in tools:
            source = _contained_path(skills_dir, tool, "SKILL.md")
            if not source.is_file():
                raise ValueError(
                    f"canonical role {agent['name']} declares missing skill source: {tool}"
                )
            skill_paths.append(str(source))
        profile = RoleProfile(
            name=agent["name"],
            model=agent.get("model") if isinstance(agent.get("model"), str) else None,
            reasoning_effort=(
                agent.get("reasoning_effort")
                if isinstance(agent.get("reasoning_effort"), str)
                else agent.get("thinking_effort")
                if isinstance(agent.get("thinking_effort"), str)
                else None
            ),
            bound_skill_paths=tuple(skill_paths),
        )
        if profile.name in profiles:
            raise ValueError(f"duplicate canonical role name: {profile.name}")
        profiles[profile.name] = profile
    if not profiles:
        raise ValueError(f"canonical agents directory contains no agent definitions: {agents_dir}")
    return profiles


def render_role_profile(profile: RoleProfile) -> str:
    """Render an inert profile; activation requires a later new Codex session."""
    lines = [
        f"# Generated inert Codex profile for {profile.name}",
        "# Activate later only with a new session: codex -p <role>",
    ]
    lines.append("")
    for skill_path in profile.bound_skill_paths:
        lines.extend(("[[skills.config]]", f"path = {_toml_string(skill_path)}", "enabled = true", ""))
    return "\n".join(lines).rstrip() + "\n"


def generate_role_profiles(
    profile_dir: Path,
    agents_dir: Path = CANONICAL_AGENTS_DIR,
    skills_dir: Path = CANONICAL_SKILLS_DIR,
) -> list[Path]:
    """Write standalone profiles only; this function never invokes Codex."""
    profiles = derive_role_profiles(agents_dir, skills_dir)  # Validate all before write.
    resolved_profile_dir = profile_dir.resolve()
    generated: list[Path] = []
    for role, profile in profiles.items():
        if not _is_safe_canonical_identifier(role):
            raise ValueError(f"unsafe generated profile role: {role}")
        profile_path = _contained_path(resolved_profile_dir, f"{role}.config.toml")
        content = render_role_profile(profile)
        if not profile_path.exists() or profile_path.read_text(encoding="utf-8") != content:
            profile_path.write_text(content, encoding="utf-8")
        generated.append(profile_path)
    return generated


def _canonical_role_names() -> list[str]:
    names: list[str] = []
    for agent_path in sorted(CANONICAL_AGENTS_DIR.glob("*/agent.json")):
        try:
            agent = json.loads(agent_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(agent, dict) or not isinstance(agent.get("name"), str):
            return []
        names.append(agent["name"])
    return names


def _measurement_failure(reason: str) -> PromptBudgetMeasurement:
    return PromptBudgetMeasurement(None, 0, f"measurement failed: {reason}")


def measure_prompt_budget(account_name: str, profile: str | None = None) -> PromptBudgetMeasurement:
    """Measure the skill prompt and reject command, JSON, and warning failures."""
    env = os.environ.copy()
    if account_name != "default":
        env["CODEX_HOME"] = str(_account_home(account_name))
    else:
        env.pop("CODEX_HOME", None)
    cmd = ["/Users/kimlenglim/.local/bin/codex"]
    if profile:
        cmd.extend(["-p", profile])
    cmd.extend(["debug", "prompt-input"])
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, cwd=str(HORO_DIR)
        )
    except OSError as error:
        return _measurement_failure(f"Codex command could not start: {error}")
    combined_output = f"{proc.stdout}\n{proc.stderr}"
    if SHORTENED_DESCRIPTION_WARNING in combined_output:
        return _measurement_failure(SHORTENED_DESCRIPTION_WARNING)
    if proc.returncode != 0:
        return _measurement_failure("Codex command returned nonzero")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _measurement_failure("invalid JSON output")
    if not isinstance(data, list):
        return _measurement_failure("invalid JSON payload")
    all_texts: list[str] = []
    skill_texts: list[str] = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("content", []), list):
            continue
        for content in item["content"]:
            text = content.get("text") if isinstance(content, dict) else None
            if isinstance(text, str):
                all_texts.append(text)
                if "<skills_instructions>" in text:
                    skill_texts.append(text)
    all_text = "\n".join(all_texts)
    opening = "<skills_instructions>"
    closing = "</skills_instructions>"
    if opening not in all_text and closing not in all_text:
        return _measurement_failure("no skills instruction text")
    if opening not in all_text or closing not in all_text:
        return _measurement_failure("malformed skills instructions boundary")
    depth = 0
    boundary_pattern = re.compile(f"{re.escape(opening)}|{re.escape(closing)}")
    for boundary in boundary_pattern.findall(all_text):
        if boundary == opening:
            if depth != 0:
                return _measurement_failure("malformed skills instructions boundary")
            depth = 1
        elif depth != 1:
            return _measurement_failure("malformed skills instructions boundary")
        else:
            depth = 0
    if depth != 0 or closing not in all_text:
        return _measurement_failure("malformed skills instructions boundary")
    skill_text = "\n".join(skill_texts)
    if SHORTENED_DESCRIPTION_WARNING in skill_text:
        return _measurement_failure(SHORTENED_DESCRIPTION_WARNING)
    truncated = sum(
        1
        for line in skill_text.splitlines()
        if line.startswith("- ") and (line.endswith("...") or "truncated" in line.lower())
    )
    return PromptBudgetMeasurement(len(skill_text), truncated)


def check_account_config(name: str, config_path: Path, check_budget: bool = False) -> AccountStatus:
    if not config_path.exists():
        return AccountStatus(name, config_path, False, [], [], [], None, 0, "missing config", False)
    try:
        content = config_path.read_text(encoding="utf-8")
        discovered = discover_remote_curated_plugins(
            _remote_cache_roots(_account_home(name, config_path)), content
        )
        expected_content = apply_remote_curated_plugin_policy(content, discovered)
        profiles = derive_role_profiles(CANONICAL_AGENTS_DIR, CANONICAL_SKILLS_DIR)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        return AccountStatus(name, config_path, True, [], [], [], None, 0, f"invalid config: {error}", False)
    missing_skills = [
        skill_path
        for skill_path in get_expected_disabled_skills(name)
        if f'path = "{skill_path}"' not in content
    ]
    missing_plugins = sorted(remote_curated_plugins_to_disable(discovered)) if expected_content != content else []
    missing_profiles: list[str] = []
    for role, profile in profiles.items():
        try:
            profile_path = _contained_path(config_path.parent, f"{role}.config.toml")
        except ValueError as error:
            return AccountStatus(
                name, config_path, True, [], [], [], None, 0, str(error), False
            )
        expected_profile = render_role_profile(profile)
        try:
            actual_profile = profile_path.read_text(encoding="utf-8")
            tomllib.loads(actual_profile)
        except (OSError, tomllib.TOMLDecodeError):
            missing_profiles.append(role)
            continue
        if actual_profile != expected_profile:
            missing_profiles.append(role)
    measurement = PromptBudgetMeasurement(None, 0)
    if check_budget:
        measurement = measure_prompt_budget(name)
    prompt_is_numeric = type(measurement.prompt_chars) is int and measurement.prompt_chars >= 0
    truncated_is_numeric = (
        type(measurement.truncated_skills) is int and measurement.truncated_skills >= 0
    )
    measurement_error = measurement.measurement_error
    if check_budget and (not prompt_is_numeric or not truncated_is_numeric):
        measurement_error = measurement_error or "measurement values must be numeric integers"
    if check_budget and prompt_is_numeric and measurement.prompt_chars > 8000:
        measurement_error = measurement_error or "over budget"
    if check_budget and truncated_is_numeric and measurement.truncated_skills != 0:
        measurement_error = measurement_error or "truncated skills"
    reported_prompt_chars = measurement.prompt_chars if prompt_is_numeric else None
    reported_truncated_skills = measurement.truncated_skills if truncated_is_numeric else 0
    is_ok = (
        not missing_skills
        and not missing_plugins
        and not missing_profiles
        and (
            not check_budget
            or (
                prompt_is_numeric
                and truncated_is_numeric
                and measurement.prompt_chars <= 8000
                and measurement.truncated_skills == 0
                and measurement_error is None
            )
        )
    )
    return AccountStatus(name, config_path, True, missing_skills, missing_plugins, missing_profiles,
                         reported_prompt_chars, reported_truncated_skills, measurement_error, is_ok)


def sync_account_config(name: str, config_path: Path) -> bool:
    """Synchronize a base config and inert profiles without launching Codex."""
    if not config_path.exists():
        print(f"[ERROR] {name}: missing config at {config_path}")
        return False
    try:
        original = config_path.read_text(encoding="utf-8")
        discovered = discover_remote_curated_plugins(
            _remote_cache_roots(_account_home(name, config_path)), original
        )
        updated = apply_remote_curated_plugin_policy(original, discovered)
        derive_role_profiles(CANONICAL_AGENTS_DIR, CANONICAL_SKILLS_DIR)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"[ERROR] {name}: policy preparation failed: {error}")
        return False
    if updated != original:
        config_path.write_text(updated, encoding="utf-8")
        print(f"[OK] Synchronized base config for {name} ({config_path})")
    else:
        print(f"[OK] Base config already up to date: {name}")
    try:
        generated = generate_role_profiles(config_path.parent)
    except (OSError, ValueError) as error:
        print(f"[ERROR] {name}: profile generation failed: {error}")
        return False
    print(f"[OK] Generated {len(generated)} inert profile(s) for {name}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate all expected account configs.")
    mode.add_argument("--sync", action="store_true", help="Synchronize policy and inert profiles, then validate.")
    parser.add_argument("--budget", action="store_true", help="Measure the live prompt skill context.")
    args = parser.parse_args()
    all_ok = True
    if args.sync:
        print("=== Synchronizing Codex Account Configs and Inert Profiles ===")
        for name, path in ACCOUNT_CONFIGS.items():
            all_ok = sync_account_config(name, path) and all_ok
    print("\n=== Validating Codex Account Configs and Inert Profiles ===")
    for name, path in ACCOUNT_CONFIGS.items():
        status = check_account_config(name, path, check_budget=args.budget or args.check)
        if not status.exists:
            print(f"[ERROR] {name:8} : missing config at {path}")
            all_ok = False
            continue
        details: list[str] = []
        if status.missing_disabled_skills:
            details.append(f"missing {len(status.missing_disabled_skills)} disabled skill(s)")
        if status.missing_disabled_plugins:
            details.append(f"missing {len(status.missing_disabled_plugins)} disabled remote plugin(s)")
        if status.missing_profiles:
            details.append(f"missing {len(status.missing_profiles)} inert profile(s)")
        if status.prompt_chars is not None:
            details.append(f"prompt={status.prompt_chars} chars (budget <= 8000)")
        details.append(f"truncated_skills={status.truncated_skills}")
        if status.measurement_error:
            details.append(status.measurement_error)
        detail_str = f" ({', '.join(details)})" if details else ""
        if status.is_ok:
            print(f"[OK]    {name:8} : Policy verified{detail_str}")
        else:
            print(f"[ERROR] {name:8} : Policy violation{detail_str}")
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
