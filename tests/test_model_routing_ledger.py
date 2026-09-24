#!/usr/bin/env python3
"""TDD contract tests for scripts/model_routing_ledger.py (KAN-101).

Tests freeze the model-routing ledger CLI contract:
- record: append a JSONL session entry (calls, tier, tokens, success)
- report: print Token/PR summary table + aggregate by interface/tier
- golden: load and summarize golden task set
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "model_routing_ledger.py"


def _run(args, ledger_path=None, env_extra=None):
    cmd = [sys.executable, str(SCRIPT)]
    cmd.extend(args)
    if ledger_path is not None:
        cmd.extend(["--ledger", str(ledger_path)])
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        cwd=str(REPO_ROOT))
    return proc


def test_record_appends_valid_jsonl_entry(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    proc = _run([
        "record",
        "--date", "2026-09-23",
        "--pr-url", "https://github.com/pphothidaen/HoroConsultant/pull/72",
        "--kan-key", "KAN-73",
        "--interface", "cli",
        "--tool-calls", "10",
        "--model-tier", "reasoning",
        "--tokens", "15000",
        "--outcome", "merged",
        "--success", "1",
        "--notes", "secret guard contract",
    ], ledger)
    assert proc.returncode == 0, proc.stderr
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["kan_key"] == "KAN-73"
    assert entry["tool_calls"] == 10
    assert entry["model_tier"] == "reasoning"
    assert entry["tokens"] == 15000
    assert entry["success"] == 1
    assert entry["outcome"] == "merged"


def test_record_appends_multiple_without_clobbering(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    for i, kan in enumerate(["KAN-70", "KAN-71", "KAN-72"]):
        proc = _run([
            "record",
            "--date", f"2026-09-{20 + i}",
            "--pr-url", f"https://github.com/pphothidaen/HoroConsultant/pull/{70 + i}",
            "--kan-key", kan,
            "--interface", "cli",
            "--tool-calls", str(8 + i),
            "--model-tier", "reasoning",
            "--tokens", str(12000 + i * 1000),
            "--outcome", "merged",
            "--success", "1",
        ], ledger)
        assert proc.returncode == 0, proc.stderr
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 3


def test_record_rejects_invalid_interface(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    proc = _run([
        "record",
        "--date", "2026-09-23",
        "--kan-key", "KAN-1",
        "--interface", "telepathy",
        "--tool-calls", "5",
        "--tokens", "5000",
    ], ledger)
    assert proc.returncode != 0


def test_record_rejects_invalid_outcome(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    proc = _run([
        "record",
        "--date", "2026-09-23",
        "--kan-key", "KAN-1",
        "--interface", "cli",
        "--tool-calls", "5",
        "--tokens", "5000",
        "--outcome", "banana",
    ], ledger)
    assert proc.returncode != 0


def test_report_prints_token_per_pr_summary(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    entries = [
        {"date": "2026-09-23", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
         "kan_key": "KAN-73", "interface": "cli", "tool_calls": 10,
         "model_tier": "reasoning", "tokens": 15000, "outcome": "merged", "success": 1, "notes": ""},
        {"date": "2026-09-22", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/70",
         "kan_key": "KAN-70", "interface": "browser", "tool_calls": 150,
         "model_tier": "frontier-multimodal", "tokens": 225000, "outcome": "merged", "success": 1, "notes": ""},
        {"date": "2026-09-21", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/67",
         "kan_key": "KAN-67", "interface": "cli", "tool_calls": 12,
         "model_tier": "reasoning", "tokens": 18000, "outcome": "merged", "success": 1, "notes": ""},
    ]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

    proc = _run(["report"], ledger)
    assert proc.returncode == 0, proc.stderr
    assert "Token/PR Summary" in proc.stdout
    assert "KAN-73" in proc.stdout
    assert "15000" in proc.stdout
    assert "225000" in proc.stdout
    assert "prs:" in proc.stdout
    assert "total_tokens:" in proc.stdout
    assert "avg_tokens/pr:" in proc.stdout


def test_report_aggregates_by_interface(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    entries = [
        {"date": "2026-09-23", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
         "kan_key": "KAN-73", "interface": "cli", "tool_calls": 10,
         "model_tier": "reasoning", "tokens": 15000, "outcome": "merged", "success": 1, "notes": ""},
        {"date": "2026-09-22", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/70",
         "kan_key": "KAN-70", "interface": "browser", "tool_calls": 150,
         "model_tier": "frontier-multimodal", "tokens": 225000, "outcome": "merged", "success": 1, "notes": ""},
    ]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

    proc = _run(["report"], ledger)
    assert proc.returncode == 0, proc.stderr
    assert "Aggregate by interface" in proc.stdout
    assert "cli" in proc.stdout
    assert "browser" in proc.stdout


def test_report_aggregates_by_model_tier(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    entries = [
        {"date": "2026-09-23", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
         "kan_key": "KAN-73", "interface": "cli", "tool_calls": 10,
         "model_tier": "reasoning", "tokens": 15000, "outcome": "merged", "success": 1, "notes": ""},
        {"date": "2026-09-22", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/70",
         "kan_key": "KAN-70", "interface": "browser", "tool_calls": 150,
         "model_tier": "frontier-multimodal", "tokens": 225000, "outcome": "merged", "success": 1, "notes": ""},
    ]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

    proc = _run(["report"], ledger)
    assert proc.returncode == 0, proc.stderr
    assert "Aggregate by model tier" in proc.stdout
    assert "reasoning" in proc.stdout
    assert "frontier-multimodal" in proc.stdout


def test_report_since_filter(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    entries = [
        {"date": "2026-09-01", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/50",
         "kan_key": "KAN-50", "interface": "cli", "tool_calls": 5,
         "model_tier": "reasoning", "tokens": 7500, "outcome": "merged", "success": 1, "notes": ""},
        {"date": "2026-09-23", "pr_url": "https://github.com/pphothidaen/HoroConsultant/pull/72",
         "kan_key": "KAN-73", "interface": "cli", "tool_calls": 10,
         "model_tier": "reasoning", "tokens": 15000, "outcome": "merged", "success": 1, "notes": ""},
    ]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

    proc = _run(["report", "--since", "2026-09-15"], ledger)
    assert proc.returncode == 0, proc.stderr
    assert "KAN-73" in proc.stdout
    assert "KAN-50" not in proc.stdout


def test_report_empty_ledger(tmp_path):
    ledger = tmp_path / "sessions.jsonl"
    proc = _run(["report"], ledger)
    assert proc.returncode == 0, proc.stderr
    assert "no ledger entries" in proc.stdout


def test_golden_command_prints_summary(tmp_path):
    proc = _run(["golden"])
    assert proc.returncode == 0, proc.stderr
    assert "Golden Task Set Summary" in proc.stdout
    assert "total tasks" in proc.stdout
    assert "qa_tester" in proc.stdout
    assert "devops" in proc.stdout
    assert "code_reviewer" in proc.stdout
    assert "orchestrator" in proc.stdout


def test_golden_command_prints_estimated_token_range(tmp_path):
    proc = _run(["golden"])
    assert proc.returncode == 0, proc.stderr
    assert "Estimated token range" in proc.stdout
    assert "qa-01" in proc.stdout
    assert "orc-05" in proc.stdout
