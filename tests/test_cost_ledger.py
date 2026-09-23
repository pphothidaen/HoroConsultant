"""TDD contract tests for scripts/cost_ledger.py (KAN-101).

These tests freeze the cost-ledger behavior BEFORE implementation exists:
- record: append a JSONL session entry
- report: read entries back, compute PR lead time, aggregate by interface
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "cost_ledger.py"


def _run(args, ledger_path, monkeypatch=None, gh_stub=None):
    """Run cost_ledger.py with an isolated ledger path and optional gh stub."""
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": "/tmp"}
    if gh_stub is not None:
        env["PATH"] = f"{gh_stub}:{env['PATH']}"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    return proc


def _write_ledger(tmp_path, entries):
    ledger = tmp_path / "sessions.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")
    return ledger


# ---------------------------------------------------------------------------
# record: writes a valid JSONL entry
# ---------------------------------------------------------------------------


def test_record_appends_valid_jsonl_entry(tmp_path):
    ledger = tmp_path / "cost-ledger" / "sessions.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "record",
            "--ledger",
            str(ledger),
            "--date",
            "2026-09-23",
            "--pr-url",
            "https://github.com/pphothidaen/HoroConsultant/pull/72",
            "--kan-key",
            "KAN-73",
            "--interface",
            "cli",
            "--tool-calls",
            "10",
            "--model-tier",
            "reasoning",
            "--outcome",
            "merged",
            "--notes",
            "CLI-only session, merged successfully",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["date"] == "2026-09-23"
    assert entry["pr_url"] == "https://github.com/pphothidaen/HoroConsultant/pull/72"
    assert entry["kan_key"] == "KAN-73"
    assert entry["interface"] == "cli"
    assert entry["tool_calls"] == 10
    assert entry["model_tier"] == "reasoning"
    assert entry["outcome"] == "merged"
    assert entry["notes"] == "CLI-only session, merged successfully"


def test_record_appends_second_entry_without_clobbering(tmp_path):
    ledger = tmp_path / "cost-ledger" / "sessions.jsonl"
    base_cmd = [
        sys.executable,
        str(SCRIPT),
        "record",
        "--ledger",
        str(ledger),
        "--kan-key",
        "KAN-99",
        "--interface",
        "browser",
        "--tool-calls",
        "150",
        "--model-tier",
        "frontier-multimodal",
        "--outcome",
        "completed-config-change",
    ]
    first = subprocess.run(
        [*base_cmd, "--date", "2026-09-21", "--notes", "first"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    second = subprocess.run(
        [*base_cmd, "--date", "2026-09-22", "--notes", "second"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# report: reads entries back and prints a table
# ---------------------------------------------------------------------------


def test_report_reads_entries_back(tmp_path, tmp_path_factory):
    ledger = _write_ledger(
        tmp_path,
        [
            {
                "date": "2026-09-23",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
                "kan_key": "KAN-73",
                "interface": "cli",
                "tool_calls": 10,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
            {
                "date": "2026-09-22",
                "pr_url": "",
                "kan_key": "KAN-90",
                "interface": "browser",
                "tool_calls": 150,
                "model_tier": "frontier-multimodal",
                "outcome": "completed-config-change",
                "notes": "browser automation session",
            },
        ],
    )
    gh_stub = _make_gh_stub(tmp_path_factory)
    proc = _run(["report", "--ledger", str(ledger)], ledger, gh_stub=gh_stub)
    assert proc.returncode == 0, proc.stderr
    assert "pull/72" in proc.stdout
    assert "KAN-73" in proc.stdout
    assert "cli" in proc.stdout
    assert "browser" in proc.stdout
    assert "10" in proc.stdout
    assert "150" in proc.stdout


# ---------------------------------------------------------------------------
# report: lead time computation from gh api PR timeline
# ---------------------------------------------------------------------------


def test_report_computes_lead_time_hours(tmp_path, tmp_path_factory):
    ledger = _write_ledger(
        tmp_path,
        [
            {
                "date": "2026-09-23",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
                "kan_key": "KAN-73",
                "interface": "cli",
                "tool_calls": 10,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
        ],
    )
    # created 07:00:20Z, merged 07:32:50Z -> 0.5417 hours ~= 0.54
    gh_stub = _make_gh_stub(tmp_path_factory, created="2026-09-23T07:00:20Z", merged="2026-09-23T07:32:50Z")
    proc = _run(["report", "--ledger", str(ledger)], ledger, gh_stub=gh_stub)
    assert proc.returncode == 0, proc.stderr
    assert "0.54" in proc.stdout


# ---------------------------------------------------------------------------
# report: aggregate by interface
# ---------------------------------------------------------------------------


def test_report_aggregates_by_interface(tmp_path, tmp_path_factory):
    ledger = _write_ledger(
        tmp_path,
        [
            {
                "date": "2026-09-20",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/71",
                "kan_key": "KAN-71",
                "interface": "cli",
                "tool_calls": 8,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
            {
                "date": "2026-09-23",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
                "kan_key": "KAN-73",
                "interface": "cli",
                "tool_calls": 12,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
            {
                "date": "2026-09-22",
                "pr_url": "",
                "kan_key": "KAN-90",
                "interface": "browser",
                "tool_calls": 150,
                "model_tier": "frontier-multimodal",
                "outcome": "completed-config-change",
                "notes": "",
            },
        ],
    )
    gh_stub = _make_gh_stub(tmp_path_factory, created="2026-09-23T07:00:20Z", merged="2026-09-23T07:32:50Z")
    proc = _run(["report", "--ledger", str(ledger)], ledger, gh_stub=gh_stub)
    assert proc.returncode == 0, proc.stderr
    # cli merged average: (8 + 12) / 2 = 10.0
    assert "10.0" in proc.stdout
    # browser has no merged PRs -> 0 merged count or no average line
    assert "browser" in proc.stdout


def test_report_since_filter(tmp_path, tmp_path_factory):
    ledger = _write_ledger(
        tmp_path,
        [
            {
                "date": "2026-09-01",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/70",
                "kan_key": "KAN-70",
                "interface": "cli",
                "tool_calls": 5,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
            {
                "date": "2026-09-23",
                "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
                "kan_key": "KAN-73",
                "interface": "cli",
                "tool_calls": 10,
                "model_tier": "reasoning",
                "outcome": "merged",
                "notes": "",
            },
        ],
    )
    gh_stub = _make_gh_stub(tmp_path_factory, created="2026-09-23T07:00:20Z", merged="2026-09-23T07:32:50Z")
    proc = _run(
        ["report", "--ledger", str(ledger), "--since", "2026-09-15"],
        ledger,
        gh_stub=gh_stub,
    )
    assert proc.returncode == 0, proc.stderr
    assert "KAN-73" in proc.stdout
    assert "KAN-70" not in proc.stdout


# ---------------------------------------------------------------------------
# gh stub
# ---------------------------------------------------------------------------


def _make_gh_stub(tmp_path_factory, created="2026-09-23T07:00:20Z", merged="2026-09-23T07:32:50Z"):
    """Create a fake `gh` executable returning fixed PR timeline JSON."""
    stub_dir = tmp_path_factory.mktemp("gh_stub")
    stub = stub_dir / "gh"
    payload = json.dumps(
        {
            "createdAt": created,
            "mergedAt": merged,
            "state": "MERGED",
        }
    )
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "api" ] && [ "$2" = "repos/{owner}/{repo}/pulls/72" ]; then\n'
        f"  echo '{payload}'\n"
        "  exit 0\n"
        "fi\n"
        'echo "{}"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return str(stub_dir)
