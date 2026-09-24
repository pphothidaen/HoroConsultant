#!/usr/bin/env python3
"""Model routing cost ledger (KAN-101).

Tracks agent sessions: tool calls, model tier, tokens per session,
success/failure, PR link. Reports token/PR totals for the last N merged PRs
and aggregate stats per interface/tier.

Stdlib-only, ASCII-only output (per scripts/AGENTS.md).

Subcommands:
  record  Append a session entry to plans/evidence/model-routing/sessions.jsonl
  report  Print ledger report showing token/PR for last 5+ PRs
  golden  Print a summary of the golden task set (20 tasks x 4 roles)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = REPO_ROOT / "plans" / "evidence" / "model-routing" / "sessions.jsonl"

VALID_INTERFACES = ("cli", "browser")
VALID_MODEL_TIERS = ("reasoning", "frontier-multimodal", "flash-lite")
VALID_OUTCOMES = ("merged", "blocked", "open", "completed-config-change")


def _ascii(msg: str) -> str:
    return msg.encode("ascii", "replace").decode("ascii")


def _print(msg: str) -> None:
    sys.stdout.write(_ascii(msg) + "\n")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cmd_record(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": args.date,
        "pr_url": args.pr_url,
        "kan_key": args.kan_key,
        "interface": args.interface,
        "tool_calls": int(args.tool_calls),
        "model_tier": args.model_tier,
        "tokens": int(args.tokens),
        "outcome": args.outcome,
        "success": int(args.success),
        "notes": args.notes,
    }
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    _print("[OK] recorded: {kan} interface={iface} calls={c} tokens={t} success={s}".format(
        kan=entry["kan_key"], iface=entry["interface"], c=entry["tool_calls"],
        t=entry["tokens"], s=entry["success"]))
    return 0


def _load_entries(ledger_path: Path, since: str | None) -> list[dict]:
    if not ledger_path.exists():
        return []
    entries: list[dict] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            _print("[WARN] skipping malformed ledger line")
    if since:
        entries = [e for e in entries if str(e.get("date", "")) >= since]
    return entries


def _gh_pr_timeline(pr_url: str):
    number = pr_url.rstrip("/").rsplit("/", 1)[-1]
    if not number.isdigit():
        return None, None
    gh = shutil.which("gh")
    if gh is None:
        return None, None
    endpoint = "repos/pphothidaen/HoroConsultant/pulls/{n}".format(n=number)
    try:
        proc = subprocess.run(
            [gh, "api", endpoint],
            capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return None, None
    if proc.returncode != 0:
        return None, None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, None
    return data.get("created_at") or data.get("createdAt"), data.get("merged_at") or data.get("mergedAt")


def _lead_time_hours(pr_url: str):
    created, merged = _gh_pr_timeline(pr_url)
    if not created or not merged:
        return None
    try:
        delta = _parse_iso(merged) - _parse_iso(created)
    except ValueError:
        return None
    return round(delta.total_seconds() / 3600.0, 2)


def cmd_report(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    entries = _load_entries(ledger, args.since)
    if not entries:
        _print("[INFO] no ledger entries found (ledger={l} since={s})".format(
            l=ledger, s=args.since))
        return 0

    _print("== Model Routing Cost Ledger ==")
    header = "{:<8} {:<10} {:<9} {:<18} {:>8} {:>10} {:>7} {:<12}".format(
        "PR", "KAN", "iface", "model_tier", "calls", "tokens", "success", "outcome")
    _print(header)
    _print("-" * len(header))

    total_tokens = 0
    total_calls = 0
    merged_count = 0
    success_count = 0
    n_prs = 0

    for e in entries:
        pr_url = str(e.get("pr_url", ""))
        pr_label = pr_url.rsplit("/", 1)[-1] if "/pull/" in pr_url else "-"
        iface = str(e.get("interface", "-"))
        tier = str(e.get("model_tier", "-"))
        calls = int(e.get("tool_calls", 0))
        tokens = int(e.get("tokens", 0))
        success = int(e.get("success", 0))
        outcome = str(e.get("outcome", "-"))

        _print("{:<8} {:<10} {:<9} {:<18} {:>8} {:>10} {:>7} {:<12}".format(
            pr_label, str(e.get("kan_key", "-")), iface, tier,
            calls, tokens, success, outcome))

        if "/pull/" in pr_url:
            n_prs += 1
            total_tokens += tokens
            total_calls += calls
            success_count += success
            if outcome == "merged":
                merged_count += 1

    _print("")
    _print("== Token/PR Summary ==")
    _print("entries:        {n}".format(n=len(entries)))
    _print("prs:            {n}".format(n=n_prs))
    _print("merged:         {n}".format(n=merged_count))
    _print("successes:      {n}".format(n=success_count))
    _print("total_tokens:   {t}".format(t=total_tokens))
    _print("total_calls:    {c}".format(c=total_calls))

    if n_prs > 0:
        _print("avg_tokens/pr:  {t:.0f}".format(t=total_tokens / n_prs))
        _print("avg_calls/pr:   {c:.1f}".format(c=total_calls / n_prs))

    # Aggregate by interface
    _print("")
    _print("== Aggregate by interface (merged only) ==")
    by_iface: dict[str, dict[str, int]] = {}
    for e in entries:
        if str(e.get("outcome", "")) == "merged":
            iface = str(e.get("interface", "-"))
            rec = by_iface.setdefault(iface, {"prs": 0, "tokens": 0, "calls": 0, "success": 0})
            rec["prs"] += 1
            rec["tokens"] += int(e.get("tokens", 0))
            rec["calls"] += int(e.get("tool_calls", 0))
            rec["success"] += int(e.get("success", 0))

    _print("{:<9} {:>6} {:>12} {:>14} {:>8}".format(
        "iface", "prs", "avg_tokens", "avg_calls", "success"))
    for iface in sorted(by_iface):
        rec = by_iface[iface]
        avg_t = rec["tokens"] / rec["prs"] if rec["prs"] else 0
        avg_c = rec["calls"] / rec["prs"] if rec["prs"] else 0
        _print("{:<9} {:>6} {:>12.0f} {:>14.1f} {:>8}".format(
            iface, rec["prs"], avg_t, avg_c, rec["success"]))

    # Aggregate by model tier
    _print("")
    _print("== Aggregate by model tier (merged only) ==")
    by_tier: dict[str, dict[str, int]] = {}
    for e in entries:
        if str(e.get("outcome", "")) == "merged":
            tier = str(e.get("model_tier", "-"))
            rec = by_tier.setdefault(tier, {"prs": 0, "tokens": 0, "calls": 0, "success": 0})
            rec["prs"] += 1
            rec["tokens"] += int(e.get("tokens", 0))
            rec["calls"] += int(e.get("tool_calls", 0))
            rec["success"] += int(e.get("success", 0))

    _print("{:<20} {:>6} {:>12} {:>14} {:>8}".format(
        "tier", "prs", "avg_tokens", "avg_calls", "success"))
    for tier in sorted(by_tier):
        rec = by_tier[tier]
        avg_t = rec["tokens"] / rec["prs"] if rec["prs"] else 0
        avg_c = rec["calls"] / rec["prs"] if rec["prs"] else 0
        _print("{:<20} {:>6} {:>12.0f} {:>14.1f} {:>8}".format(
            tier, rec["prs"], avg_t, avg_c, rec["success"]))

    return 0


def cmd_golden(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from tests.golden_tasks import load_all_tasks, validate_all, summary
    except Exception as e:
        _print("[ERROR] cannot import golden_tasks: {e}".format(e=e))
        return 1

    total, valid, errors = validate_all()
    s = summary()

    _print("== Golden Task Set Summary ==")
    _print("total tasks:    {n}".format(n=total))
    _print("valid:          {n}".format(n=valid))
    if errors:
        _print("errors:")
        for err in errors:
            _print("  - " + err)
    _print("")
    _print("by role:")
    for role in sorted(s["by_role"]):
        _print("  {role:<20} {n}".format(role=role, n=s["by_role"][role]))
    _print("interfaces:     {v}".format(v=", ".join(s["interfaces"])))
    _print("model tiers:    {v}".format(v=", ".join(s["model_tiers"])))

    # Token cost estimation table
    tasks = load_all_tasks()
    _print("")
    _print("== Estimated token range per task ==")
    _print("{:<10} {:<20} {:<9} {:<18} {:>12} {:>12}".format(
        "id", "role", "iface", "tier", "min_tokens", "max_tokens"))
    total_min = 0
    total_max = 0
    for t in tasks:
        role = t["role"]
        iface = t["interface"]
        tier = t["model_tier"]
        tmin = int(t["tool_calls_min"]) * 1500
        tmax = int(t["tool_calls_max"]) * 1500
        total_min += tmin
        total_max += tmax
        _print("{:<10} {:<20} {:<9} {:<18} {:>12} {:>12}".format(
            t["id"][:9], role[:19], iface, tier[:17], tmin, tmax))
    _print("")
    _print("total estimated token range: {mn} - {mx}".format(mn=total_min, mx=total_max))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Model routing cost ledger (KAN-101)")
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_ledger(p):
        p.add_argument("--ledger", default=str(DEFAULT_LEDGER),
                       help="Path to sessions.jsonl")
        return p

    p_rec = _add_ledger(sub.add_parser("record", help="Append a session entry"))
    p_rec.add_argument("--date", required=True, help="Session date YYYY-MM-DD")
    p_rec.add_argument("--pr-url", default="", help="PR URL")
    p_rec.add_argument("--kan-key", required=True, help="Jira KAN key")
    p_rec.add_argument("--interface", required=True, choices=VALID_INTERFACES)
    p_rec.add_argument("--tool-calls", required=True, help="Number of tool calls")
    p_rec.add_argument("--model-tier", default="", choices=VALID_MODEL_TIERS,
                       help="Model tier used")
    p_rec.add_argument("--tokens", default="0", help="Total token count for session")
    p_rec.add_argument("--outcome", default="open", choices=VALID_OUTCOMES)
    p_rec.add_argument("--success", default="1", help="1 if session achieved goal, 0 otherwise")
    p_rec.add_argument("--notes", default="", help="Free-form notes")
    p_rec.set_defaults(func=cmd_record)

    p_rep = _add_ledger(sub.add_parser("report", help="Print ledger report"))
    p_rep.add_argument("--since", default=None, help="Only entries >= YYYY-MM-DD")
    p_rep.set_defaults(func=cmd_report)

    p_gld = sub.add_parser("golden", help="Print golden task set summary")
    p_gld.set_defaults(func=cmd_golden)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
