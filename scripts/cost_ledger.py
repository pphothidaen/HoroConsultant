#!/usr/bin/env python3
"""Cost ledger: record and report agent session cost metrics (KAN-101).

Turns token/tool-call cost-value claims from narrative into measurable
numbers. Stdlib-only, ASCII-only output (per scripts/AGENTS.md).

Subcommands:
  record  Append a session entry to plans/evidence/cost-ledger/sessions.jsonl
  report  Read the ledger + gh api PR timeline, print a summary table
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
DEFAULT_LEDGER = REPO_ROOT / "plans" / "evidence" / "cost-ledger" / "sessions.jsonl"

VALID_INTERFACES = ("cli", "browser")


def _print(msg: str) -> None:
    """ASCII-safe stdout."""
    sys.stdout.write(msg.encode("ascii", "replace").decode("ascii") + "\n")


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
        "outcome": args.outcome,
        "notes": args.notes,
    }
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    _print("[OK] recorded entry: {kan} interface={iface} tool_calls={calls}".format(
        kan=entry["kan_key"], iface=entry["interface"], calls=entry["tool_calls"]))
    return 0


def _load_entries(ledger_path: Path, since: str | None):
    if not ledger_path.exists():
        return []
    entries = []
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
    """Return (created_at, merged_at) for a PR URL via gh api, or (None, None)."""
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
    hours = delta.total_seconds() / 3600.0
    return round(hours, 2)


def cmd_report(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    entries = _load_entries(ledger, args.since)
    if not entries:
        _print("[INFO] no ledger entries found (ledger=%s since=%s)" % (ledger, args.since))
        return 0

    _print("== Cost Ledger Report ==")
    header = "{:<12} {:<10} {:<9} {:>10} {:>10} {:<26} {:<24}".format(
        "PR", "KAN", "interface", "tool_calls", "lead_h", "outcome", "model_tier")
    _print(header)
    _print("-" * len(header))
    for e in entries:
        pr_url = str(e.get("pr_url", ""))
        pr_label = pr_url.rsplit("/", 1)[-1] if "/pull/" in pr_url else "-"
        lead = _lead_time_hours(pr_url) if "/pull/" in pr_url else None
        lead_s = "{:.2f}".format(lead) if lead is not None else "-"
        _print("{:<12} {:<10} {:<9} {:>10} {:>10} {:<26} {:<24}".format(
            pr_label or "-",
            str(e.get("kan_key", "-")),
            str(e.get("interface", "-")),
            str(e.get("tool_calls", "-")),
            lead_s,
            str(e.get("outcome", "-")),
            str(e.get("model_tier", "-")),
        ))

    _print("")
    _print("== Aggregate (merged PRs only) ==")
    by_iface: dict[str, list[int]] = {}
    for e in entries:
        if str(e.get("outcome", "")) == "merged":
            by_iface.setdefault(str(e.get("interface", "-")), []).append(int(e.get("tool_calls", 0)))
    if not by_iface:
        _print("[INFO] no merged entries to aggregate")
        return 0
    _print("{:<10} {:>12} {:>18}".format("interface", "merged_prs", "avg_tool_calls"))
    for iface in sorted(by_iface):
        calls = by_iface[iface]
        _print("{:<10} {:>12} {:>18}".format(iface, len(calls), "{:.1f}".format(sum(calls) / len(calls))))
    total = [c for calls in by_iface.values() for c in calls]
    _print("{:<10} {:>12} {:>18}".format("TOTAL", len(total), "{:.1f}".format(sum(total) / len(total))))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Agent session cost ledger (KAN-101)")
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_ledger(p):
        p.add_argument("--ledger", default=str(DEFAULT_LEDGER),
                       help="Path to sessions.jsonl (default: plans/evidence/cost-ledger/sessions.jsonl)")
        return p

    p_rec = _add_ledger(sub.add_parser("record", help="Append a session entry to the ledger"))
    p_rec.add_argument("--date", required=True, help="Session date YYYY-MM-DD")
    p_rec.add_argument("--pr-url", default="", help="PR URL if a PR was opened")
    p_rec.add_argument("--kan-key", required=True, help="Jira KAN key")
    p_rec.add_argument("--interface", required=True, choices=VALID_INTERFACES,
                       help="Session interface: cli or browser")
    p_rec.add_argument("--tool-calls", required=True, help="Number of tool calls in session")
    p_rec.add_argument("--model-tier", default="", help="Model tier used")
    p_rec.add_argument("--outcome", default="open",
                       help="merged / blocked / open / completed-config-change")
    p_rec.add_argument("--notes", default="", help="Free-form notes")
    p_rec.set_defaults(func=cmd_record)

    p_rep = _add_ledger(sub.add_parser("report", help="Print a summary table from the ledger"))
    p_rep.add_argument("--since", default=None, help="Only include entries dated >= YYYY-MM-DD")
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
