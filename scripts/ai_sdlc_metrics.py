#!/usr/bin/env python3
"""AI-SDLC Metrics Collection & Telemetry — Phase 1.5.

Collects 4 core outcome metrics:
1. Cost per Attempt / Completed Ticket
2. Verification Tax (PR Review Time)
3. Signal-to-Noise Ratio of AI Reviewer
4. Post-Deploy Escape Rate

Plus gate event telemetry for observability.

Outputs: JSONL sidecar + SQLite for Grafana/OTLP export.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path("metrics/ai_sdlc_metrics.db")
JSONL_PATH = Path("metrics/ai_sdlc_metrics.jsonl")

# Ensure metrics directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    """Get database connection with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize SQLite schema."""
    conn = get_db()
    cur = conn.cursor()

    # Task telemetry table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,           -- ISO 8601 UTC
            ticket_id TEXT NOT NULL,           -- e.g., KAN-105
            commit_sha TEXT,                   -- Git commit SHA
            risk_tier TEXT NOT NULL,           -- Tier 1, Tier 2, Tier 3
            iteration_count INTEGER NOT NULL,  -- How many Red->Green cycles
            duration_seconds REAL NOT NULL,    -- Wall-clock time for this attempt
            tokens_consumed INTEGER DEFAULT 0, -- Token count (if available)
            cost_usd REAL DEFAULT 0.0,         -- Cost in USD (if available)
            passed_first_try INTEGER NOT NULL, -- 1 if passed on first attempt, 0 otherwise
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Gate events table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,           -- ISO 8601 UTC
            gate_name TEXT NOT NULL,           -- tdd_gate_push, tdd_gate_transition, code_reviewer, pre-commit, pre-push
            gate_mode TEXT NOT NULL,           -- observation, enforce
            tier TEXT NOT NULL,                -- Tier 1, Tier 2, Tier 3
            result TEXT NOT NULL,              -- PASS, FAIL, FAIL_OBSERVED, OVERRIDE
            override_by TEXT,                  -- Human who overrode (if OVERRIDE)
            false_positive_flag INTEGER DEFAULT 0, -- 1 if false positive detected
            commit_sha TEXT,                   -- Associated commit
            ticket_id TEXT,                    -- Associated ticket
            duration_ms INTEGER DEFAULT 0,     -- Gate execution time
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # AI Reviewer signal/noise tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_reviewer_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            commit_sha TEXT,
            finding_type TEXT NOT NULL,        -- security, complexity, boundary, secret, syntax, false_positive
            severity TEXT NOT NULL,            -- critical, high, medium, low, info
            is_true_positive INTEGER,          -- 1=TP, 0=FP, NULL=unknown (pending human triage)
            human_triaged_at TEXT,             -- When human reviewed
            triaged_by TEXT,                   -- Who triaged
            file_path TEXT,                    -- File path relative to repo root
            line_number INTEGER,               -- Line number of finding
            message TEXT,                      -- Finding message
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Post-deploy escape tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS post_deploy_escapes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            commit_sha TEXT,
            escape_type TEXT NOT NULL,         -- red_team_find, blue_team_find, user_report, monitoring_alert
            severity TEXT NOT NULL,            -- critical, high, medium, low
            description TEXT,
            root_cause TEXT,
            auto_ticket_created INTEGER DEFAULT 0, -- 1 if intent.md/ATOMIC_TICKET.md auto-generated
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Indexes for common queries
    cur.execute("CREATE INDEX IF NOT EXISTS idx_task_ticket ON task_telemetry(ticket_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_task_commit ON task_telemetry(commit_sha)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gate_timestamp ON gate_events(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gate_name ON gate_events(gate_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_review_ticket ON ai_reviewer_signals(ticket_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_escape_ticket ON post_deploy_escapes(ticket_id)")

    conn.commit()
    conn.close()


def write_jsonl(record: dict) -> None:
    """Append record to JSONL sidecar for streaming/Grafana Loki."""
    record["_written_at"] = datetime.now(timezone.utc).isoformat()
    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_task_telemetry(
    ticket_id: str,
    commit_sha: Optional[str],
    risk_tier: str,
    iteration_count: int,
    duration_seconds: float,
    tokens_consumed: int = 0,
    cost_usd: float = 0.0,
    passed_first_try: bool = False,
) -> None:
    """Record a task attempt."""
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "ticket_id": ticket_id,
        "commit_sha": commit_sha,
        "risk_tier": risk_tier,
        "iteration_count": iteration_count,
        "duration_seconds": duration_seconds,
        "tokens_consumed": tokens_consumed,
        "cost_usd": cost_usd,
        "passed_first_try": 1 if passed_first_try else 0,
    }

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO task_telemetry (timestamp, ticket_id, commit_sha, risk_tier,
                                    iteration_count, duration_seconds, tokens_consumed,
                                    cost_usd, passed_first_try)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, ticket_id, commit_sha, risk_tier, iteration_count,
          duration_seconds, tokens_consumed, cost_usd, 1 if passed_first_try else 0))
    conn.commit()
    conn.close()

    write_jsonl({"type": "task_telemetry", **record})


def record_gate_event(
    gate_name: str,
    gate_mode: str,
    tier: str,
    result: str,
    override_by: Optional[str] = None,
    false_positive: int = 0,
    commit_sha: Optional[str] = None,
    ticket_id: Optional[str] = None,
    duration_ms: int = 0,
) -> None:
    """Record a gate event (pre-commit, pre-push, tdd_gate, code_reviewer, CI)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "gate_name": gate_name,
        "gate_mode": gate_mode,
        "tier": tier,
        "result": result,
        "override_by": override_by,
        "false_positive_flag": false_positive,
        "commit_sha": commit_sha,
        "ticket_id": ticket_id,
        "duration_ms": duration_ms,
    }

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO gate_events (timestamp, gate_name, gate_mode, tier, result,
                                 override_by, false_positive_flag, commit_sha, ticket_id, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, gate_name, gate_mode, tier, result, override_by,
          false_positive, commit_sha, ticket_id, duration_ms))
    conn.commit()
    conn.close()

    write_jsonl({"type": "gate_event", **record})


def record_ai_review_signal(
    ticket_id: str,
    commit_sha: Optional[str],
    finding_type: str,
    severity: str,
    is_true_positive: Optional[bool] = None,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    """Record an AI reviewer finding for signal-to-noise tracking."""
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "ticket_id": ticket_id,
        "commit_sha": commit_sha,
        "finding_type": finding_type,
        "severity": severity,
        "is_true_positive": 1 if is_true_positive else 0 if is_true_positive is False else None,
        "file_path": file_path,
        "line_number": line_number,
        "message": message,
    }

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ai_reviewer_signals (timestamp, ticket_id, commit_sha,
                                         finding_type, severity, is_true_positive,
                                         file_path, line_number, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, ticket_id, commit_sha, finding_type, severity,
          1 if is_true_positive else 0 if is_true_positive is False else None,
          file_path, line_number, message))
    conn.commit()
    conn.close()

    write_jsonl({"type": "ai_reviewer_signal", **record})


def record_post_deploy_escape(
    ticket_id: str,
    commit_sha: Optional[str],
    escape_type: str,
    severity: str,
    description: str,
    root_cause: Optional[str] = None,
    auto_ticket_created: bool = False,
) -> None:
    """Record a post-deploy escape (Red/Blue find, user report, etc.)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "ticket_id": ticket_id,
        "commit_sha": commit_sha,
        "escape_type": escape_type,
        "severity": severity,
        "description": description,
        "root_cause": root_cause,
        "auto_ticket_created": 1 if auto_ticket_created else 0,
    }

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO post_deploy_escapes (timestamp, ticket_id, commit_sha,
                                         escape_type, severity, description,
                                         root_cause, auto_ticket_created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, ticket_id, commit_sha, escape_type, severity,
          description, root_cause, 1 if auto_ticket_created else 0))
    conn.commit()
    conn.close()

    write_jsonl({"type": "post_deploy_escape", **record})


def query_cost_per_ticket(ticket_id: str) -> dict:
    """Calculate Cost per Attempt / Completed Ticket."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) as attempts,
            SUM(cost_usd) as total_cost,
            AVG(cost_usd) as avg_cost_per_attempt,
            SUM(duration_seconds) as total_duration,
            SUM(iteration_count) as total_iterations
        FROM task_telemetry
        WHERE ticket_id = ?
    """, (ticket_id,))
    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        return {
            "ticket_id": ticket_id,
            "attempts": row[0],
            "total_cost_usd": row[1] or 0.0,
            "avg_cost_per_attempt_usd": row[2] or 0.0,
            "total_duration_seconds": row[3] or 0.0,
            "total_iterations": row[4] or 0,
        }
    return {"ticket_id": ticket_id, "attempts": 0}


def query_verification_tax(ticket_id: str) -> dict:
    """Calculate Verification Tax (human review time)."""
    conn = get_db()
    cur = conn.cursor()
    # Gate events where human had to intervene (OVERRIDE or FAIL in enforce mode)
    cur.execute("""
        SELECT
            COUNT(*) as total_gates,
            SUM(CASE WHEN result IN ('FAIL', 'OVERRIDE') THEN 1 ELSE 0 END) as human_interventions,
            SUM(CASE WHEN gate_mode = 'enforce' AND result = 'FAIL' THEN duration_ms ELSE 0 END) as enforce_fail_time_ms
        FROM gate_events
        WHERE ticket_id = ?
    """, (ticket_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "ticket_id": ticket_id,
            "total_gate_events": row[0] or 0,
            "human_interventions": row[1] or 0,
            "enforce_fail_time_ms": row[2] or 0,
        }
    return {"ticket_id": ticket_id, "total_gate_events": 0}


def query_signal_to_noise(ticket_id: str) -> dict:
    """Calculate Signal-to-Noise Ratio of AI Reviewer."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) as total_findings,
            SUM(CASE WHEN is_true_positive = 1 THEN 1 ELSE 0 END) as true_positives,
            SUM(CASE WHEN is_true_positive = 0 THEN 1 ELSE 0 END) as false_positives,
            SUM(CASE WHEN is_true_positive IS NULL THEN 1 ELSE 0 END) as pending_triage
        FROM ai_reviewer_signals
        WHERE ticket_id = ?
    """, (ticket_id,))
    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        tp = row[1] or 0
        fp = row[2] or 0
        return {
            "ticket_id": ticket_id,
            "total_findings": row[0],
            "true_positives": tp,
            "false_positives": fp,
            "pending_triage": row[3] or 0,
            "signal_to_noise_ratio": round(tp / fp, 2) if fp > 0 else float('inf') if tp > 0 else 0.0,
        }
    return {"ticket_id": ticket_id, "total_findings": 0}


def query_escape_rate(ticket_id: str) -> dict:
    """Calculate Post-Deploy Escape Rate."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) as total_escapes,
            SUM(CASE WHEN severity IN ('critical', 'high') THEN 1 ELSE 0 END) as high_severity,
            SUM(auto_ticket_created) as auto_tickets_created
        FROM post_deploy_escapes
        WHERE ticket_id = ?
    """, (ticket_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "ticket_id": ticket_id,
            "total_escapes": row[0] or 0,
            "high_severity_escapes": row[1] or 0,
            "auto_tickets_created": row[2] or 0,
        }
    return {"ticket_id": ticket_id, "total_escapes": 0}


def generate_report(ticket_id: Optional[str] = None) -> dict:
    """Generate AI-SDLC metrics report for a ticket or all tickets."""
    conn = get_db()
    cur = conn.cursor()

    if ticket_id:
        where = "WHERE ticket_id = ?"
        params = (ticket_id,)
    else:
        where = ""
        params = ()

    cur.execute(f"SELECT DISTINCT ticket_id FROM task_telemetry {where}", params)
    tickets = [row[0] for row in cur.fetchall()]
    conn.close()

    report = {}
    for tid in tickets:
        report[tid] = {
            "cost_per_ticket": query_cost_per_ticket(tid),
            "verification_tax": query_verification_tax(tid),
            "signal_to_noise": query_signal_to_noise(tid),
            "escape_rate": query_escape_rate(tid),
        }

    return report


def export_for_grafana() -> dict:
    """Export all data in format suitable for Grafana/OTLP ingestion."""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = {
        "task_telemetry": [dict(row) for row in cur.execute("SELECT * FROM task_telemetry").fetchall()],
        "gate_events": [dict(row) for row in cur.execute("SELECT * FROM gate_events").fetchall()],
        "ai_reviewer_signals": [dict(row) for row in cur.execute("SELECT * FROM ai_reviewer_signals").fetchall()],
        "post_deploy_escapes": [dict(row) for row in cur.execute("SELECT * FROM post_deploy_escapes").fetchall()],
    }
    conn.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-SDLC Metrics Telemetry CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    subparsers.add_parser("init", help="Initialize database schema")

    # record-task
    p_task = subparsers.add_parser("record-task", help="Record task telemetry")
    p_task.add_argument("--ticket-id", required=True)
    p_task.add_argument("--commit-sha")
    p_task.add_argument("--risk-tier", required=True, choices=["Tier 1", "Tier 2", "Tier 3"])
    p_task.add_argument("--iterations", type=int, required=True)
    p_task.add_argument("--duration", type=float, required=True)
    p_task.add_argument("--tokens", type=int, default=0)
    p_task.add_argument("--cost", type=float, default=0.0)
    p_task.add_argument("--first-try", action="store_true")

    # record-gate
    p_gate = subparsers.add_parser("record-gate", help="Record gate event")
    p_gate.add_argument("--gate-name", required=True)
    p_gate.add_argument("--gate-mode", required=True, choices=["observation", "enforce"])
    p_gate.add_argument("--tier", required=True, choices=["Tier 1", "Tier 2", "Tier 3"])
    p_gate.add_argument("--result", required=True, choices=["PASS", "FAIL", "FAIL_OBSERVED", "OVERRIDE"])
    p_gate.add_argument("--override-by")
    p_gate.add_argument("--false-positive", type=int, default=0)
    p_gate.add_argument("--commit-sha")
    p_gate.add_argument("--ticket-id")
    p_gate.add_argument("--duration-ms", type=int, default=0)

    # record-review-signal
    p_review = subparsers.add_parser("record-review-signal", help="Record AI reviewer finding")
    p_review.add_argument("--ticket-id", required=True)
    p_review.add_argument("--commit-sha")
    p_review.add_argument("--finding-type", required=True,
                          choices=["security", "complexity", "boundary", "secret", "syntax", "false_positive"])
    p_review.add_argument("--severity", required=True, choices=["critical", "high", "medium", "low", "info"])
    p_review.add_argument("--true-positive", choices=["true", "false", "unknown"], default="unknown")
    p_review.add_argument("--file", help="File path relative to repo root")
    p_review.add_argument("--line", type=int, help="Line number")
    p_review.add_argument("--message", help="Finding message")

    # record-escape
    p_escape = subparsers.add_parser("record-escape", help="Record post-deploy escape")
    p_escape.add_argument("--ticket-id", required=True)
    p_escape.add_argument("--commit-sha")
    p_escape.add_argument("--escape-type", required=True,
                          choices=["red_team_find", "blue_team_find", "user_report", "monitoring_alert"])
    p_escape.add_argument("--severity", required=True, choices=["critical", "high", "medium", "low"])
    p_escape.add_argument("--description", required=True)
    p_escape.add_argument("--root-cause")
    p_escape.add_argument("--auto-ticket", action="store_true")

    # report
    p_report = subparsers.add_parser("report", help="Generate metrics report")
    p_report.add_argument("--ticket-id")
    p_report.add_argument("--json", action="store_true")

    # export
    subparsers.add_parser("export", help="Export all data for Grafana/OTLP")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print(f"✅ Database initialized at {DB_PATH}")
        return 0

    # Ensure DB exists for other commands
    if not DB_PATH.exists():
        init_db()

    if args.command == "record-task":
        record_task_telemetry(
            ticket_id=args.ticket_id,
            commit_sha=args.commit_sha,
            risk_tier=args.risk_tier,
            iteration_count=args.iterations,
            duration_seconds=args.duration,
            tokens_consumed=args.tokens,
            cost_usd=args.cost,
            passed_first_try=args.first_try,
        )
        print(f"✅ Recorded task telemetry for {args.ticket_id}")
        return 0

    if args.command == "record-gate":
        record_gate_event(
            gate_name=args.gate_name,
            gate_mode=args.gate_mode,
            tier=args.tier,
            result=args.result,
            override_by=args.override_by,
            false_positive=args.false_positive,
            commit_sha=args.commit_sha,
            ticket_id=args.ticket_id,
            duration_ms=args.duration_ms,
        )
        print(f"✅ Recorded gate event: {args.gate_name} ({args.result})")
        return 0

    if args.command == "record-review-signal":
        tp_map = {"true": True, "false": False, "unknown": None}
        record_ai_review_signal(
            ticket_id=args.ticket_id,
            commit_sha=args.commit_sha,
            finding_type=args.finding_type,
            severity=args.severity,
            is_true_positive=tp_map[args.true_positive],
            file_path=args.file,
            line_number=args.line,
            message=args.message,
        )
        print(f"✅ Recorded AI reviewer signal for {args.ticket_id}")
        return 0

    if args.command == "record-escape":
        record_post_deploy_escape(
            ticket_id=args.ticket_id,
            commit_sha=args.commit_sha,
            escape_type=args.escape_type,
            severity=args.severity,
            description=args.description,
            root_cause=args.root_cause,
            auto_ticket_created=args.auto_ticket,
        )
        print(f"✅ Recorded post-deploy escape for {args.ticket_id}")
        return 0

    if args.command == "report":
        report = generate_report(args.ticket_id)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            for tid, metrics in report.items():
                print(f"\n=== {tid} ===")
                for category, data in metrics.items():
                    print(f"  {category}: {data}")
        return 0

    if args.command == "export":
        data = export_for_grafana()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())