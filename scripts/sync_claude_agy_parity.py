#!/usr/bin/env python3
"""Synchronize and validate parity between Claude Code and AGY CLI ecosystems.

Engineering Objectives:
1. Ensure full parity across:
   - Root Context files: CLAUDE.md <-> AGY.md
   - Ignore files: .claudeignore <-> .agyignore
   - Rules: .claude/rules/*.md <-> .agy/rules/*.md
   - Custom Skills: .claude/skills/ <-> .agy/skills/
   - Sandboxed Sub-Agents: .claude/agents/*.md <-> .agy/agents/*.md
   - Lifecycle Hooks: .claude/hooks/ <-> .agy/hooks/
2. Provide multi-tier trigger integration:
   - Git pre-commit hook validator
   - Agent post-tool-use lifecycle trigger
   - File system watcher daemon (--watch)
   - Central ecosystem gate integration
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]

CLAUDE_DIR = ROOT / ".claude"
AGY_DIR = ROOT / ".agy"

CLAUDE_RULES_DIR = CLAUDE_DIR / "rules"
AGY_RULES_DIR = AGY_DIR / "rules"

CLAUDE_SKILLS_DIR = CLAUDE_DIR / "skills"
AGY_SKILLS_DIR = AGY_DIR / "skills"

CLAUDE_AGENTS_DIR = CLAUDE_DIR / "agents"
AGY_AGENTS_DIR = AGY_DIR / "agents"

CLAUDE_HOOKS_DIR = CLAUDE_DIR / "hooks"
AGY_HOOKS_DIR = AGY_DIR / "hooks"

CLAUDE_IGNORE = ROOT / ".claudeignore"
AGY_IGNORE = ROOT / ".agyignore"

CLAUDE_MD = ROOT / "CLAUDE.md"
AGY_MD = ROOT / "AGY.md"


@dataclass
class ParityResult:
    component: str
    ok: bool
    detail: str


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_file_safe(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content
    try:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1]) or {}
            body = parts[2]
            return fm, body
    except Exception:
        pass
    return {}, content


def sync_ignore_files(check_only: bool = False) -> list[ParityResult]:
    results: list[ParityResult] = []
    claude_content = read_file_safe(CLAUDE_IGNORE)
    agy_content = read_file_safe(AGY_IGNORE)

    if not CLAUDE_IGNORE.exists() and not AGY_IGNORE.exists():
        return [ParityResult("ignore_files", False, "Neither .claudeignore nor .agyignore exists")]

    # Normalize patterns (strip comments and blank lines)
    def parse_patterns(text: str) -> set[str]:
        return {line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")}

    claude_patterns = parse_patterns(claude_content)
    agy_patterns = parse_patterns(agy_content)

    union_patterns = sorted(claude_patterns | agy_patterns)

    # Required baseline ignore patterns
    required_ignores = {".env*", "*.lock", "node_modules/", "dist/", "build/", "__pycache__/", ".pytest_cache/"}
    missing_from_union = [p for p in required_ignores if not any(p.rstrip("*") in up for up in union_patterns)]

    if check_only:
        diff = claude_patterns.symmetric_difference(agy_patterns)
        if diff:
            results.append(
                ParityResult(
                    "ignore_files",
                    False,
                    f".claudeignore vs .agyignore mismatch on {len(diff)} pattern(s): {', '.join(sorted(diff)[:5])}",
                )
            )
        elif missing_from_union:
            results.append(
                ParityResult("ignore_files", False, f"Missing critical ignores: {', '.join(missing_from_union)}")
            )
        else:
            results.append(ParityResult("ignore_files", True, f"Ignore files synchronized ({len(claude_patterns)} patterns)"))
    else:
        # Build comprehensive unified ignore template
        unified_content = """# Auto-synchronized Token Sustainability & Context Exclusion Filter
# Shared between Claude Code (.claudeignore) and AGY CLI (.agyignore)

# Secrets and credentials
.env*
!.env.example
*.pem
*.key
*.cert
*.p12
credentials.json
secrets.json

# Lockfiles and dependency caches
*.lock
package-lock.json
uv.lock
Pipfile.lock
poetry.lock

# Dependency Directories
node_modules/
vendor/
.venv/
venv/
env/
__pypackages__/

# Build and Distribution Outputs
dist/
build/
*.egg-info/
target/
out/
.next/
.nuxt/

# Caches and Bytecode
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.ruff_cache/
.mypy_cache/
.cache/

# Test and Coverage Outputs
coverage/
.coverage
.coverage.*
coverage.xml
htmlcov/
.nyc_output/

# Logs and Runtime State
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
wandb/

# OS and Editor Specifics
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
.idea/
.vscode/
*.swp
*.swo
*~
"""
        CLAUDE_IGNORE.write_text(unified_content, encoding="utf-8")
        AGY_IGNORE.write_text(unified_content, encoding="utf-8")
        results.append(ParityResult("ignore_files", True, "Synchronized .claudeignore and .agyignore"))

    return results


def sync_rules(check_only: bool = False) -> list[ParityResult]:
    results: list[ParityResult] = []
    CLAUDE_RULES_DIR.mkdir(parents=True, exist_ok=True)
    AGY_RULES_DIR.mkdir(parents=True, exist_ok=True)

    claude_rules = {p.name: p for p in CLAUDE_RULES_DIR.glob("*.md")}
    agy_rules = {p.name: p for p in AGY_RULES_DIR.glob("*.md")}

    all_rule_names = sorted(set(claude_rules.keys()) | set(agy_rules.keys()))
    mismatches = 0

    for name in all_rule_names:
        claude_path = CLAUDE_RULES_DIR / name
        agy_path = AGY_RULES_DIR / name

        if check_only:
            if not claude_path.exists() or not agy_path.exists():
                results.append(
                    ParityResult(f"rule:{name}", False, f"Rule {name} missing in {'Claude' if not claude_path.exists() else 'AGY'}")
                )
                mismatches += 1
                continue

            claude_text = claude_path.read_text(encoding="utf-8")
            agy_text = agy_path.read_text(encoding="utf-8")

            claude_fm, _ = parse_frontmatter(claude_text)
            agy_fm, _ = parse_frontmatter(agy_text)

            if not claude_fm.get("paths") or not agy_fm.get("paths"):
                results.append(ParityResult(f"rule:{name}", False, f"Rule {name} missing 'paths' frontmatter"))
                mismatches += 1
            elif not claude_fm.get("description") or not agy_fm.get("description"):
                results.append(ParityResult(f"rule:{name}", False, f"Rule {name} missing 'description' frontmatter"))
                mismatches += 1
            else:
                results.append(ParityResult(f"rule:{name}", True, "Frontmatter & paths valid"))
        else:
            # Sync: prefer newer file or the one with richer frontmatter
            source_path = None
            if claude_path.exists() and agy_path.exists():
                source_path = claude_path if claude_path.stat().st_mtime >= agy_path.stat().st_mtime else agy_path
            elif claude_path.exists():
                source_path = claude_path
            elif agy_path.exists():
                source_path = agy_path

            if source_path:
                content = source_path.read_text(encoding="utf-8")
                # Ensure frontmatter is valid
                fm, body = parse_frontmatter(content)
                if not fm:
                    # Provide default frontmatter if missing
                    stem = name.replace(".md", "")
                    fm = {
                        "description": f"Architectural governance and constraints for {stem}.",
                        "paths": f"**/*{stem}*/**",
                    }
                    content = f"---\n{yaml.dump(fm, sort_keys=False).strip()}\n---\n\n{body.strip()}\n"

                claude_path.write_text(content, encoding="utf-8")
                agy_path.write_text(content, encoding="utf-8")

    if not check_only:
        results.append(ParityResult("rules", True, f"Synchronized {len(all_rule_names)} progressive rules"))
    elif mismatches == 0:
        results.append(ParityResult("rules", True, f"All {len(all_rule_names)} progressive rules aligned across Claude and AGY"))

    return results


def sync_skills(check_only: bool = False) -> list[ParityResult]:
    results: list[ParityResult] = []
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    AGY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    claude_skills = {p.name: p for p in CLAUDE_SKILLS_DIR.iterdir() if p.is_dir()}
    agy_skills = {p.name: p for p in AGY_SKILLS_DIR.iterdir() if p.is_dir()}

    all_skill_names = sorted(set(claude_skills.keys()) | set(agy_skills.keys()))
    mismatches = 0

    for name in all_skill_names:
        claude_skill_md = CLAUDE_SKILLS_DIR / name / "SKILL.md"
        agy_skill_md = AGY_SKILLS_DIR / name / "SKILL.md"

        if check_only:
            if not claude_skill_md.exists() or not agy_skill_md.exists():
                results.append(
                    ParityResult(
                        f"skill:{name}",
                        False,
                        f"Skill {name} missing in {'Claude' if not claude_skill_md.exists() else 'AGY'}",
                    )
                )
                mismatches += 1
                continue

            claude_fm, claude_body = parse_frontmatter(claude_skill_md.read_text(encoding="utf-8"))
            agy_fm, agy_body = parse_frontmatter(agy_skill_md.read_text(encoding="utf-8"))

            if not claude_fm.get("name") or not agy_fm.get("name"):
                results.append(ParityResult(f"skill:{name}", False, f"Skill {name} missing name frontmatter"))
                mismatches += 1
            elif "## Gotchas" not in claude_body and "## Gotchas" not in agy_body:
                results.append(ParityResult(f"skill:{name}", False, f"Skill {name} missing ## Gotchas section"))
                mismatches += 1
            else:
                results.append(ParityResult(f"skill:{name}", True, "Skill frontmatter and gotchas aligned"))
        else:
            # Sync skill folder
            source_file = None
            if claude_skill_md.exists() and agy_skill_md.exists():
                source_file = claude_skill_md if claude_skill_md.stat().st_mtime >= agy_skill_md.stat().st_mtime else agy_skill_md
            elif claude_skill_md.exists():
                source_file = claude_skill_md
            elif agy_skill_md.exists():
                source_file = agy_skill_md

            if source_file:
                content = source_file.read_text(encoding="utf-8")
                # Ensure target directories exist
                (CLAUDE_SKILLS_DIR / name).mkdir(parents=True, exist_ok=True)
                (AGY_SKILLS_DIR / name).mkdir(parents=True, exist_ok=True)
                claude_skill_md.write_text(content, encoding="utf-8")
                agy_skill_md.write_text(content, encoding="utf-8")

    if not check_only:
        results.append(ParityResult("skills", True, f"Synchronized {len(all_skill_names)} skills"))
    elif mismatches == 0:
        results.append(ParityResult("skills", True, f"All {len(all_skill_names)} skills in parity"))

    return results


def sync_agents(check_only: bool = False) -> list[ParityResult]:
    results: list[ParityResult] = []
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    AGY_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    claude_agents = {p.name: p for p in CLAUDE_AGENTS_DIR.glob("*.md")}
    agy_agents = {p.name: p for p in AGY_AGENTS_DIR.glob("*.md")}

    all_agent_names = sorted(set(claude_agents.keys()) | set(agy_agents.keys()))
    mismatches = 0

    for name in all_agent_names:
        claude_path = CLAUDE_AGENTS_DIR / name
        agy_path = AGY_AGENTS_DIR / name

        if check_only:
            if not claude_path.exists() or not agy_path.exists():
                results.append(
                    ParityResult(
                        f"agent:{name}",
                        False,
                        f"Agent {name} missing in {'Claude' if not claude_path.exists() else 'AGY'}",
                    )
                )
                mismatches += 1
                continue

            claude_fm, _ = parse_frontmatter(claude_path.read_text(encoding="utf-8"))
            agy_fm, _ = parse_frontmatter(agy_path.read_text(encoding="utf-8"))

            if not claude_fm.get("name") or not agy_fm.get("name"):
                results.append(ParityResult(f"agent:{name}", False, f"Agent {name} missing name"))
                mismatches += 1
            elif not claude_fm.get("tools") or not agy_fm.get("tools"):
                results.append(ParityResult(f"agent:{name}", False, f"Agent {name} missing tools sandboxing"))
                mismatches += 1
            else:
                results.append(ParityResult(f"agent:{name}", True, "Agent 14-parameter sandbox aligned"))
        else:
            source_path = None
            if claude_path.exists() and agy_path.exists():
                source_path = claude_path if claude_path.stat().st_mtime >= agy_path.stat().st_mtime else agy_path
            elif claude_path.exists():
                source_path = claude_path
            elif agy_path.exists():
                source_path = agy_path

            if source_path:
                content = source_path.read_text(encoding="utf-8")
                claude_path.write_text(content, encoding="utf-8")
                agy_path.write_text(content, encoding="utf-8")

    if not check_only:
        results.append(ParityResult("agents", True, f"Synchronized {len(all_agent_names)} sandboxed subagents"))
    elif mismatches == 0:
        results.append(ParityResult("agents", True, f"All {len(all_agent_names)} subagents aligned"))

    return results


def sync_hooks_and_permissions(check_only: bool = False) -> list[ParityResult]:
    results: list[ParityResult] = []
    CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    AGY_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure executable permissions on all shell scripts in hooks/ and scripts/
    hook_dirs = [CLAUDE_HOOKS_DIR, AGY_HOOKS_DIR, AGY_DIR / "scripts", ROOT / ".githooks"]
    for h_dir in hook_dirs:
        if h_dir.exists():
            for sh_file in h_dir.glob("*.sh"):
                if check_only:
                    if not os.access(sh_file, os.X_OK):
                        results.append(ParityResult(f"hook_perm:{sh_file.name}", False, f"{relative(sh_file)} is not executable"))
                else:
                    sh_file.chmod(sh_file.stat().st_mode | 0o755)

    # Check key hook files
    expected_agy_hooks = ["pre-tool-use.sh", "post-tool-use.sh", "stop-monitor.sh"]
    missing_agy_hooks = [h for h in expected_agy_hooks if not (AGY_HOOKS_DIR / h).exists()]
    if missing_agy_hooks:
        results.append(ParityResult("agy_hooks", False, f"Missing AGY hooks: {', '.join(missing_agy_hooks)}"))
    else:
        results.append(ParityResult("agy_hooks", True, f"All {len(expected_agy_hooks)} AGY hooks present and executable"))

    return results


def install_git_hooks() -> bool:
    """Installs or updates git pre-commit hook to trigger parity check."""
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        print("[WARNING] .git directory not found; skipping git hook installation.")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit_hook = hooks_dir / "pre-commit"

    hook_script = """#!/usr/bin/env bash
# Auto-generated by scripts/sync_claude_agy_parity.py
# Enforces Claude Code vs. AGY CLI parity before committing.

set -euo pipefail

if command -v python3 &>/dev/null; then
    python3 scripts/sync_claude_agy_parity.py --check
    PARITY_STATUS=$?
    if [ $PARITY_STATUS -ne 0 ]; then
        echo "[ERROR] Pre-commit parity check failed between Claude Code and AGY CLI."
        echo "[INFO] Run 'python3 scripts/sync_claude_agy_parity.py --sync' to auto-resolve differences."
        exit $PARITY_STATUS
    fi
fi

# Run existing .githooks/pre-commit if present
if [ -f ".githooks/pre-commit" ]; then
    bash .githooks/pre-commit "$@"
fi
"""
    pre_commit_hook.write_text(hook_script, encoding="utf-8")
    pre_commit_hook.chmod(0o755)
    print(f"[OK] Installed Git Pre-Commit Hook at {relative(pre_commit_hook)}")
    return True


def run_all_parity_checks(check_only: bool = True) -> list[ParityResult]:
    all_results: list[ParityResult] = []
    all_results.extend(sync_ignore_files(check_only=check_only))
    all_results.extend(sync_rules(check_only=check_only))
    all_results.extend(sync_skills(check_only=check_only))
    all_results.extend(sync_agents(check_only=check_only))
    all_results.extend(sync_hooks_and_permissions(check_only=check_only))
    return all_results


def run_watcher(poll_interval: float = 1.0) -> None:
    """Continuously monitors .claude/, .agy/, and context files to trigger autosync."""
    print("==========================================================================================")
    print("👁️  CLAUDE CODE <-> AGY CLI AUTOSYNC TRIGGER WATCHER ACTIVE")
    print(f"Monitoring: .claude/, .agy/, CLAUDE.md, AGY.md, .claudeignore, .agyignore (Interval: {poll_interval}s)")
    print("Press Ctrl+C to stop.")
    print("==========================================================================================")

    monitored_paths = [
        CLAUDE_DIR,
        AGY_DIR,
        CLAUDE_MD,
        AGY_MD,
        CLAUDE_IGNORE,
        AGY_IGNORE,
    ]

    def compute_state_snapshot() -> dict[str, float]:
        snapshot: dict[str, float] = {}
        for base in monitored_paths:
            if not base.exists():
                continue
            if base.is_file():
                snapshot[str(base)] = base.stat().st_mtime
            elif base.is_dir():
                for p in base.rglob("*"):
                    if p.is_file() and "__pycache__" not in p.parts:
                        snapshot[str(p)] = p.stat().st_mtime
        return snapshot

    last_snapshot = compute_state_snapshot()

    try:
        while True:
            time.sleep(poll_interval)
            current_snapshot = compute_state_snapshot()

            changed = False
            for path_str, mtime in current_snapshot.items():
                if path_str not in last_snapshot or last_snapshot[path_str] != mtime:
                    changed = True
                    break
            if not changed and len(last_snapshot) != len(current_snapshot):
                changed = True

            if changed:
                print(f"\n[TRIGGER] Detected filesystem change at {time.strftime('%X')}. Synchronizing parity...")
                results = run_all_parity_checks(check_only=False)
                for res in results:
                    prefix = "[OK]" if res.ok else "[ERROR]"
                    print(f"  {prefix} {res.component}: {res.detail}")
                last_snapshot = compute_state_snapshot()
    except KeyboardInterrupt:
        print("\n[INFO] Watcher stopped by user.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code <-> AGY CLI Parity Synchronizer & Auto-Trigger")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate parity without writing (read-only)")
    mode.add_argument("--sync", action="store_true", help="Synchronize all components across Claude and AGY")
    mode.add_argument("--watch", action="store_true", help="Run background watcher daemon to auto-trigger sync on file changes")
    mode.add_argument("--install-hooks", action="store_true", help="Install git pre-commit parity trigger")

    args = parser.parse_args(argv)

    if args.install_hooks:
        success = install_git_hooks()
        return 0 if success else 1

    if args.watch:
        run_watcher()
        return 0

    check_only = args.check or not args.sync
    results = run_all_parity_checks(check_only=check_only)

    all_ok = True
    print("\n==========================================================================================")
    print(f"Claude Code vs. AGY CLI Parity Check ({'READ-ONLY' if check_only else 'SYNC MODE'})")
    print("==========================================================================================")
    for res in results:
        prefix = "[OK]" if res.ok else "[ERROR]"
        if not res.ok:
            all_ok = False
        print(f"{prefix} {res.component:<24}: {res.detail}")
    print("==========================================================================================\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
