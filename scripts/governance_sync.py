#!/usr/bin/env python3
"""Governance-as-code sync for branch protection and repository rulesets.

Subcommands:
  validate  -- Compare governance/*.json against live GitHub state; exit 1 on drift.
  apply     -- Push governance/*.json to GitHub (requires --yes confirmation).
  export    -- Write live GitHub state into governance/*.json.

Design notes (KAN-97):
  * All GitHub access goes through `gh api` via subprocess (stdlib-first per
    scripts/AGENTS.md); no PyGithub dependency is added.
  * Output is ASCII-only with [OK]/[ERROR]/[WARN]/[INFO] status tags.
  * Fail-closed: any read/write error exits non-zero; `apply` refuses to run
    without --yes and refuses when live state cannot be read.
  * Volatile server metadata (urls, node ids, timestamps, per-viewer fields)
    is stripped at export time and at comparison time so only declarative
    settings are tracked.
  * Reading classic branch protection requires an administration-scoped
    token; the default GITHUB_TOKEN in Actions cannot read it. Run validate
    with an admin-capable token (e.g. GH_TOKEN secret) or it fails closed.

Governance files:
  governance/branch-protection.main.json -- classic branch protection on main.
  governance/rulesets.json              -- repository rulesets. The ruleset
     "id" is kept so apply can target the same object; it is excluded from
     the drift comparison because it is server-assigned.

Policy (docs/governance-as-code.md): every governance change goes through a
PR. `apply` is only run after the PR merges, by a maintainer, to converge
live state with the merged declaration.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

DEFAULT_REPO = "pphothidaen/HoroConsultant"
DEFAULT_BRANCH = "main"
GOVERNANCE_DIR = "governance"
BRANCH_PROTECTION_FILE = "branch-protection.main.json"
RULESETS_FILE = "rulesets.json"
GH_TIMEOUT_SECONDS = 60
REPO_SLUG_RE = re.compile(r"^[\w.-]+/[\w.-]+$")

# Classic branch-protection GET response fields that are volatile server
# metadata rather than settings an apply would write.
BRANCH_PROTECTION_VOLATILE_KEYS = ("url",)
# Ruleset fields that are server-assigned or per-viewer and must not be part
# of the declarative comparison. Export keeps "id" (apply targets it), but
# comparison strips it from both sides.
RULESET_VOLATILE_KEYS = (
    "id",
    "node_id",
    "created_at",
    "updated_at",
    "source",
    "source_type",
    "_links",
    "current_user_can_bypass",
)
RULESET_EXPORT_VOLATILE_KEYS = tuple(key for key in RULESET_VOLATILE_KEYS if key != "id")

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2

# Classic protection PUT sub-endpoints and the settings each one accepts.
# Keys mirror the GET response sections; anything else in a section is
# treated as read-only server metadata.
APPLY_BP_FIELD_SECTIONS: dict[str, tuple[str, ...]] = {
    "required_pull_request_reviews": (
        "dismiss_stale_reviews",
        "require_code_owner_reviews",
        "require_last_push_approval",
        "required_approving_review_count",
    ),
    "required_status_checks": (
        "strict",
        "contexts",
        "checks",
    ),
}
APPLY_BP_BOOLEAN_SECTIONS = (
    "enforce_admins",
    "required_signatures",
    "required_linear_history",
    "allow_force_pushes",
    "allow_deletions",
    "required_conversation_resolution",
    "lock_branch",
    "allow_fork_syncing",
    "block_creations",
)
# Ruleset fields that apply may write back to the ruleset endpoint.
RULESET_APPLY_KEYS = (
    "name",
    "target",
    "enforcement",
    "conditions",
    "rules",
    "bypass_actors",
)


class GovernanceError(RuntimeError):
    """Raised when GitHub state cannot be read or written safely."""


def _print(tag: str, message: str) -> None:
    """Print an ASCII-only, tag-prefixed log line."""
    safe = message.encode("ascii", "backslashreplace").decode("ascii")
    print(f"[{tag}] {safe}")


def _repo_slug(repo: str | None) -> str:
    if not repo:
        return DEFAULT_REPO
    if not REPO_SLUG_RE.match(repo):
        raise GovernanceError(f"invalid repository slug: {repo!r}")
    return repo


def _branch_slug(branch: str | None) -> str:
    return branch or DEFAULT_BRANCH


def _governance_dir(repo_root: str | None) -> Path:
    root = Path(repo_root or ".").resolve()
    target = root / GOVERNANCE_DIR
    if not target.is_dir():
        raise GovernanceError(f"governance directory not found under {root}")
    return target


def _gh_api(
    endpoint: str,
    *,
    method: str = "GET",
    input_json: dict[str, Any] | None = None,
) -> Any:
    """Call `gh api` and return parsed JSON; fail closed on any error."""
    if not endpoint.startswith("/"):
        raise GovernanceError(f"refusing non-absolute API endpoint: {endpoint!r}")
    args = [
        "gh",
        "api",
        "--method",
        method,
        "--header",
        "Accept: application/vnd.github+json",
    ]
    if input_json is not None:
        args.extend(["--input", "-"])
    args.append(endpoint)
    result = subprocess.run(
        args,
        input=json.dumps(input_json) if input_json is not None else None,
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "gh api failed").strip()
        raise GovernanceError(f"gh api {method} {endpoint}: {detail[:500]}")
    body = result.stdout.strip()
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise GovernanceError(f"gh api {endpoint}: non-JSON response: {exc}") from exc


def _strip_volatile(data: Any, volatile_keys: tuple[str, ...]) -> Any:
    """Recursively remove volatile keys from dicts inside the payload."""
    if isinstance(data, dict):
        return {
            key: _strip_volatile(value, volatile_keys)
            for key, value in data.items()
            if key not in volatile_keys
        }
    if isinstance(data, list):
        return [_strip_volatile(item, volatile_keys) for item in data]
    return data


def _canonical(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True)


def _load_declared(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceError(f"{path} must be a JSON object")
    return value


def _load_declared_rulesets(path: Path) -> list[dict[str, Any]]:
    doc = _load_declared(path)
    rulesets = doc.get("rulesets")
    if not isinstance(rulesets, list) or not all(isinstance(rs, dict) for rs in rulesets):
        raise GovernanceError(f"{path} must contain a 'rulesets' array of objects")
    return rulesets


def fetch_branch_protection(repo: str, branch: str) -> dict[str, Any]:
    """Fetch classic branch protection for a branch; fail closed on error."""
    endpoint = f"/repos/{repo}/branches/{quote(branch, safe='')}/protection"
    data = _gh_api(endpoint)
    if not isinstance(data, dict):
        raise GovernanceError(f"branch protection response for {repo}/{branch} is not a JSON object")
    return data


def fetch_rulesets(repo: str) -> list[dict[str, Any]]:
    """Fetch full details for every repository ruleset.

    The list endpoint only returns summaries (no ``conditions``/``rules``),
    so each ruleset is fetched individually to capture its full declaration.
    """
    summary = _gh_api(f"/repos/{repo}/rulesets")
    if not isinstance(summary, list):
        raise GovernanceError(f"rulesets response for {repo} is not a JSON array")
    details: list[dict[str, Any]] = []
    for entry in summary:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), int):
            raise GovernanceError("ruleset summary entry is missing a numeric id")
        detail = _gh_api(f"/repos/{repo}/rulesets/{entry['id']}")
        if not isinstance(detail, dict):
            raise GovernanceError(f"ruleset detail response for id {entry['id']} is not a JSON object")
        details.append(detail)
    return details


def _write_governance_file(path: Path, payload: Any) -> None:
    path.write_text(_canonical(payload) + "\n", encoding="utf-8")


def _write_step_summary(drifts: list[tuple[str, str]]) -> None:
    """Append a markdown summary for the Actions run when GITHUB_STEP_SUMMARY is set."""
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = ["## Governance Drift Detection", ""]
    if not drifts:
        lines.append("[OK] No drift - governance/*.json matches live GitHub state.")
    else:
        lines.append(f"**DRIFT DETECTED** - {len(drifts)} difference(s) between governance/*.json and live GitHub state:")
        lines.append("")
        lines.append("| Setting | Difference |")
        lines.append("| --- | --- |")
        for label, detail in drifts:
            safe_label = label.replace("|", "\\|")
            safe_detail = detail.replace("|", "\\|")
            lines.append(f"| `{safe_label}` | {safe_detail} |")
        lines.append("")
        lines.append(
            "Fix: open a PR that updates governance/*.json to the intended state, "
            "merge it, then a maintainer runs `python3 scripts/governance_sync.py apply --yes`. "
            "If the live change was intentional, run `export` in a PR instead."
        )
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        # Summary is best-effort; never mask the validate result.
        pass


def cmd_export(args: argparse.Namespace) -> int:
    repo = _repo_slug(args.repo)
    branch = _branch_slug(args.branch)
    gov_dir = _governance_dir(args.repo_root)
    _print("INFO", f"exporting live GitHub governance state for {repo} (branch {branch})")

    protection = fetch_branch_protection(repo, branch)
    bp_file = gov_dir / BRANCH_PROTECTION_FILE
    _write_governance_file(bp_file, _strip_volatile(protection, BRANCH_PROTECTION_VOLATILE_KEYS))
    _print("OK", f"wrote {bp_file}")

    rulesets = fetch_rulesets(repo)
    rulesets_file = gov_dir / RULESETS_FILE
    exported = [_strip_volatile(rs, RULESET_EXPORT_VOLATILE_KEYS) for rs in rulesets]
    _write_governance_file(rulesets_file, {"rulesets": exported})
    _print("OK", f"wrote {rulesets_file} ({len(exported)} ruleset(s))")
    _print("WARN", "exported files overwrite the declaration; commit them via a PR")
    return EXIT_OK


def _compare(label: str, declared: Any, live: Any, drifts: list[tuple[str, str]]) -> None:
    """Recursively diff declared vs live; append (label, detail) on mismatch."""
    if isinstance(declared, dict) and isinstance(live, dict):
        for key in sorted(set(declared) | set(live)):
            dv = declared.get(key)
            lv = live.get(key)
            if key not in declared:
                drifts.append((f"{label}.{key}", f"live-only key (live={lv!r})"))
            elif key not in live:
                drifts.append((f"{label}.{key}", f"declared-only key (declared={dv!r})"))
            else:
                _compare(f"{label}.{key}", dv, lv, drifts)
    elif isinstance(declared, list) and isinstance(live, list):
        if len(declared) != len(live):
            drifts.append(
                (label, f"list length differs (declared={len(declared)}, live={len(live)})")
            )
        else:
            for index, (dv, lv) in enumerate(zip(declared, live)):
                _compare(f"{label}[{index}]", dv, lv, drifts)
    else:
        if declared != live:
            drifts.append((label, f"declared={declared!r} live={live!r}"))


def _fetch_live_state(repo: str, branch: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return fetch_branch_protection(repo, branch), fetch_rulesets(repo)


def cmd_validate(args: argparse.Namespace) -> int:
    repo = _repo_slug(args.repo)
    branch = _branch_slug(args.branch)
    gov_dir = _governance_dir(args.repo_root)
    _print("INFO", f"validating governance files under {gov_dir} against {repo}")

    declared_bp = _load_declared(gov_dir / BRANCH_PROTECTION_FILE)
    declared_rulesets = _load_declared_rulesets(gov_dir / RULESETS_FILE)

    live_bp, live_rulesets = _fetch_live_state(repo, branch)

    drifts: list[tuple[str, str]] = []
    _compare(
        "branch_protection",
        _strip_volatile(declared_bp, BRANCH_PROTECTION_VOLATILE_KEYS),
        _strip_volatile(live_bp, BRANCH_PROTECTION_VOLATILE_KEYS),
        drifts,
    )
    _compare(
        "rulesets",
        [_strip_volatile(rs, RULESET_VOLATILE_KEYS) for rs in declared_rulesets],
        [_strip_volatile(rs, RULESET_VOLATILE_KEYS) for rs in live_rulesets],
        drifts,
    )

    _write_step_summary(drifts)
    if drifts:
        _print("ERROR", f"GOVERNANCE_DRIFT detected ({len(drifts)} difference(s)):")
        for label, detail in drifts:
            _print("ERROR", f"  {label}: {detail}")
        _print(
            "INFO",
            "fix by opening a PR that updates governance/*.json, or run export after an approved change",
        )
        return EXIT_DRIFT
    _print("OK", "no drift: governance files match live GitHub state")
    return EXIT_OK


def _bp_apply_payloads(declared: dict[str, Any], repo: str, branch: str) -> list[tuple[str, dict[str, Any]]]:
    """Build ordered classic-protection PUT payloads from the declaration."""
    branch_path = f"/repos/{repo}/branches/{quote(branch, safe='')}/protection"
    payloads: list[tuple[str, dict[str, Any]]] = []
    for section, allowed_keys in APPLY_BP_FIELD_SECTIONS.items():
        if section not in declared:
            continue
        section_data = declared[section]
        if not isinstance(section_data, dict):
            raise GovernanceError(f"branch protection section {section} must be an object")
        payload: dict[str, Any] = {key: section_data[key] for key in allowed_keys if key in section_data}
        if section == "required_pull_request_reviews" and "dismissal_restrictions" in section_data:
            payload["dismissal_restrictions"] = section_data["dismissal_restrictions"]
        payloads.append((f"{branch_path}/{section}", payload))
    for section in APPLY_BP_BOOLEAN_SECTIONS:
        if section not in declared:
            continue
        section_data = declared[section]
        enabled = section_data.get("enabled") if isinstance(section_data, dict) else None
        if not isinstance(enabled, bool):
            raise GovernanceError(f"branch protection section {section} must be {{'enabled': bool}}")
        payloads.append((f"{branch_path}/{section}", {"enabled": enabled}))
    return payloads


def _ruleset_apply_payload(declared: dict[str, Any]) -> dict[str, Any]:
    return {key: declared[key] for key in RULESET_APPLY_KEYS if key in declared}


def cmd_apply(args: argparse.Namespace) -> int:
    repo = _repo_slug(args.repo)
    branch = _branch_slug(args.branch)
    gov_dir = _governance_dir(args.repo_root)
    if not args.yes:
        _print("ERROR", "apply requires --yes (refusing to mutate GitHub state without confirmation)")
        return EXIT_ERROR
    _print("WARN", f"apply will overwrite live governance state for {repo} (branch {branch})")

    declared_bp = _load_declared(gov_dir / BRANCH_PROTECTION_FILE)
    declared_rulesets = _load_declared_rulesets(gov_dir / RULESETS_FILE)

    # Fail closed: read live state first so a mid-flight API failure cannot
    # leave us writing payloads built from a half-read state.
    live_bp, live_rulesets = _fetch_live_state(repo, branch)
    if not live_bp:
        raise GovernanceError("cannot apply: live branch protection state unreadable")
    if not live_rulesets:
        raise GovernanceError("cannot apply: live rulesets unreadable")

    for endpoint, payload in _bp_apply_payloads(declared_bp, repo, branch):
        _print("INFO", f"applying {endpoint}: {_canonical(payload)}")
        _gh_api(endpoint, method="PUT", input_json=payload)

    live_by_name = {rs.get("name"): rs for rs in live_rulesets if isinstance(rs.get("name"), str)}
    for declared_rs in declared_rulesets:
        name = declared_rs.get("name")
        if not isinstance(name, str) or not name:
            raise GovernanceError("each ruleset entry must have a non-empty name")
        payload = _ruleset_apply_payload(declared_rs)
        existing = live_by_name.get(name)
        if existing is not None and isinstance(existing.get("id"), int):
            _print("INFO", f"updating ruleset {name} (id {existing['id']})")
            _gh_api(f"/repos/{repo}/rulesets/{existing['id']}", method="PUT", input_json=payload)
        elif isinstance(declared_rs.get("id"), int):
            _print("INFO", f"updating ruleset {name} (declared id {declared_rs['id']})")
            _gh_api(f"/repos/{repo}/rulesets/{declared_rs['id']}", method="PUT", input_json=payload)
        else:
            _print("WARN", f"creating new ruleset {name}")
            _gh_api(f"/repos/{repo}/rulesets", method="POST", input_json=payload)

    _print("OK", "apply complete; re-validating")
    return cmd_validate(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync GitHub governance (branch protection + rulesets) with governance/*.json"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--repo", default=DEFAULT_REPO, help="owner/repo slug (default: %(default)s)")
        sub.add_argument("--branch", default=DEFAULT_BRANCH, help="branch for classic protection (default: %(default)s)")
        sub.add_argument("--repo-root", default=".", help="repository root containing governance/ (default: %(default)s)")

    validate = subparsers.add_parser("validate", help="compare governance/*.json with live GitHub state")
    add_common(validate)
    validate.set_defaults(func=cmd_validate)

    export = subparsers.add_parser("export", help="write live GitHub state into governance/*.json")
    add_common(export)
    export.set_defaults(func=cmd_export)

    apply_parser = subparsers.add_parser("apply", help="push governance/*.json to GitHub (requires --yes)")
    apply_parser.add_argument("--yes", action="store_true", help="confirm mutation of live GitHub state")
    add_common(apply_parser)
    apply_parser.set_defaults(func=cmd_apply)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    except GovernanceError as exc:
        _print("ERROR", str(exc))
        return EXIT_ERROR
    except subprocess.TimeoutExpired:
        _print("ERROR", "gh api timed out")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
