#!/usr/bin/env python3
"""Apply an idempotent Codex skill-budget policy across local account homes."""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
import tomllib
from pathlib import Path


PROJECT_DISABLED_SKILLS = (
    "adaptive-model-effort-routing",
    "agy-capacity-orchestration",
    "ai-inference-verifier",
    "bazi-calculator",
    "github-pr-automation",
    "kaggle-manager",
    "metaphysical-domain-engine",
    "rag-search",
    "zero-cost-ai-pipeline",
)
GLOBAL_DISABLED_SKILLS = (
    "skill-creator",
    "supabase",
    "supabase-postgres-best-practices",
    "web-automation",
)
SYSTEM_DISABLED_SKILLS = (
    "imagegen",
    "openai-docs",
    "plugin-creator",
    "skill-creator",
    "skill-installer",
)


def configured_skill_states(config_text: str) -> dict[str, bool]:
    parsed = tomllib.loads(config_text)
    states: dict[str, bool] = {}
    for item in parsed.get("skills", {}).get("config", []):
        path = item.get("path")
        if isinstance(path, str):
            states[path] = bool(item.get("enabled", True))
    return states


def _skill_blocks(lines: list[str]) -> list[tuple[int, int]]:
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == "[[skills.config]]"
    ]
    blocks: list[tuple[int, int]] = []
    for start in starts:
        end = len(lines)
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                end = index
                break
        blocks.append((start, end))
    return blocks


def apply_skill_policy(config_text: str, disabled_paths: list[str]) -> str:
    """Disable exact skill paths while preserving unrelated TOML text."""
    configured_skill_states(config_text)  # Fail before modifying invalid TOML.
    lines = config_text.splitlines(keepends=True)
    found: set[str] = set()

    # Work from the end so inserting a missing `enabled` key cannot shift a
    # block that still needs to be inspected.
    for start, end in reversed(_skill_blocks(lines)):
        block = "".join(lines[start:end])
        try:
            item = tomllib.loads(block).get("skills", {}).get("config", [])[0]
        except (tomllib.TOMLDecodeError, IndexError, TypeError):
            continue
        path = item.get("path")
        if path not in disabled_paths:
            continue
        found.add(path)
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
            prefix = lines[enabled_line][: len(lines[enabled_line]) - len(lines[enabled_line].lstrip())]
            lines[enabled_line] = f"{prefix}enabled = false\n"

    missing = [path for path in disabled_paths if path not in found]
    if not missing:
        return "".join(lines)

    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if lines and lines[-1].strip():
        lines.append("\n")
    lines.append("# HoroConsultant skill-context budget policy\n")
    for path in missing:
        lines.extend(
            (
                "[[skills.config]]\n",
                f'path = "{path}"\n',
                "enabled = false\n",
                "\n",
            )
        )
    return "".join(lines)


def account_homes(
    *, default_home: Path | None = None, account_root: Path | None = None
) -> list[tuple[str, Path]]:
    user_home = Path.home()
    default_home = default_home or user_home / ".codex"
    account_root = account_root or user_home / ".ai-accounts/codex"
    discovered = [("default", default_home)]
    aliases: list[tuple[int, Path]] = []
    for config in account_root.glob("account*/config.toml"):
        suffix = config.parent.name.removeprefix("account")
        if suffix.isdigit():
            aliases.append((int(suffix), config.parent))
    discovered.extend(
        (f"codex{number}", home) for number, home in sorted(aliases)
    )
    return discovered


def policy_paths(account_home: Path, project_root: Path) -> list[str]:
    user_home = Path.home()
    paths = [
        *(project_root / ".agents/skills" / name / "SKILL.md" for name in PROJECT_DISABLED_SKILLS),
        *(user_home / ".agents/skills" / name / "SKILL.md" for name in GLOBAL_DISABLED_SKILLS),
        *(account_home / "skills/.system" / name / "SKILL.md" for name in SYSTEM_DISABLED_SKILLS),
    ]
    optional = account_home / "skills/codex-with-chatgpt/SKILL.md"
    if optional.exists():
        paths.append(optional)
    return [str(path) for path in paths]


def _atomic_write(path: Path, content: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--sync", action="store_true")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    failures = 0
    for name, home in account_homes():
        config = home / "config.toml"
        if not config.is_file():
            print(f"[ERROR] {name}: missing {config}")
            failures += 1
            continue
        original = config.read_text(encoding="utf-8")
        expected = policy_paths(home, args.project_root.resolve())
        updated = apply_skill_policy(original, expected)
        if updated != original:
            if args.check:
                print(f"[ERROR] {name}: skill-budget policy drift")
                failures += 1
            else:
                _atomic_write(config, updated)
                print(f"[OK] {name}: skill-budget policy synchronized")
        else:
            print(f"[OK] {name}: skill-budget policy current")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
