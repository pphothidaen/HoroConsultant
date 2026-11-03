#!/usr/bin/env python3
"""
scripts/auto_intent_generator.py — Closed-Loop Incident to Intent/Ticket Synthesizer.

Ingests test failure reports, deduplicates against existing records via SHA-256 error fingerprints,
and produces structured tickets based on risk classification.

Features:
- Persistent deduplication via JSONL ledger (works on ephemeral CI runners)
- SQLite backend for local development
- Ticket lifecycle management: resolve/dismiss with reasons
- Tier 2 (ATOMIC_TICKET.md) and Tier 3 (intent-{id}.md) synthesis
- Correct DISMISSED vs RESOLVED semantics per AI-Native SDLC Playbook:
    * DISMISSED (false alarm/flaky) → suppresses future occurrences (noise reduction)
    * RESOLVED (fixed & deployed) → allows re-occurrence as REGRESSION (bug returned)
- Auto-creates Configuration Regression Eval stubs on --resolve
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = Path("plans/ai_sdlc_metrics.db")
DEFAULT_LEDGER_PATH = Path("plans/escapes_ledger.jsonl")


class AutoIntentGenerator:
    def __init__(
        self,
        report_path: Optional[Path] = None,
        db_path: Path = DEFAULT_DB_PATH,
        ledger_path: Path = DEFAULT_LEDGER_PATH,
        dry_run: bool = False,
        action: str = "synthesize",
        fingerprint: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.report_path = Path(report_path) if report_path else None
        self.db_path = Path(db_path)
        self.ledger_path = Path(ledger_path)
        self.dry_run = dry_run
        self.action = action
        self.fingerprint = fingerprint
        self.reason = reason
        self.data = self._load_report() if self.report_path else {}
        self._init_db()
        self._init_ledger()

    def _init_db(self) -> None:
        if self.dry_run and not self.db_path.exists():
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS post_deploy_escapes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticket_id TEXT NOT NULL,
                error_fingerprint TEXT UNIQUE NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT DEFAULT 'OPEN',
                occurrence_count INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolution_reason TEXT
            );
            """)
            conn.commit()

    def _init_ledger(self) -> None:
        if self.dry_run and not self.ledger_path.exists():
            return
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.write_text("", encoding="utf-8")

    def _load_report(self) -> Dict[str, Any]:
        if not self.report_path or not self.report_path.exists():
            return {"raw_log": f"Report file not found: {self.report_path}"}
        try:
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"raw_log": self.report_path.read_text(encoding="utf-8")}

    def compute_fingerprint(self) -> str:
        """Generates a normalized SHA-256 hash of the core stack trace / error string."""
        raw_trace = self.data.get("error_trace") or self.data.get("raw_log") or "unknown_error"
        # Normalize memory addresses, line numbers, and timestamps to avoid duplicate hashes
        normalized = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", raw_trace)
        normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b", "TIMESTAMP", normalized)
        normalized = re.sub(r"line \d+", "line N", normalized)
        return hashlib.sha256(normalized.strip().encode("utf-8")).hexdigest()[:12]

    def _get_latest_status(self, fingerprint: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Get latest status, ticket_id, and resolution_reason from both backends.
        
        Returns: (status, ticket_id, resolution_reason)
        Priority: JSONL ledger (source of truth for CI) > SQLite
        """
        # Check JSONL ledger first (persistent across CI runs)
        if self.ledger_path.exists():
            latest_entry = None
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("error_fingerprint") == fingerprint:
                        latest_entry = entry
                except json.JSONDecodeError:
                    continue
            if latest_entry:
                return (
                    latest_entry.get("status"),
                    latest_entry.get("ticket_id"),
                    latest_entry.get("resolution_reason")
                )

        # Fallback to SQLite
        if not self.db_path.exists():
            return (None, None, None)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT status, ticket_id, resolution_reason FROM post_deploy_escapes WHERE error_fingerprint = ? ORDER BY id DESC LIMIT 1",
                (fingerprint,),
            ).fetchone()
            if row:
                return (row["status"], row["ticket_id"], row["resolution_reason"])

        return (None, None, None)

    def check_duplicate(self, fingerprint: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks if fingerprint should be deduplicated based on latest status.
        
        Returns: (is_duplicate, existing_ticket_id, suppression_reason)
        
        Logic per AI-Native SDLC Playbook:
        - OPEN      → duplicate (increment occurrence_count)
        - DISMISSED → duplicate (suppress noise, print reason)
        - RESOLVED  → NOT duplicate (allow regression re-open)
        - None      → NOT duplicate (new incident)
        """
        status, ticket_id, resolution_reason = self._get_latest_status(fingerprint)

        if status == "OPEN":
            # Increment occurrence count in SQLite
            if not self.dry_run:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE post_deploy_escapes SET occurrence_count = occurrence_count + 1, last_seen = CURRENT_TIMESTAMP WHERE error_fingerprint = ? AND status = 'OPEN'",
                        (fingerprint,),
                    )
                    conn.commit()
            return True, ticket_id, "open"

        if status == "DISMISSED":
            # Suppress dismissed findings (noise reduction)
            reason = resolution_reason or "previously dismissed"
            print(f"[AUTO-INTENT] Suppressed dismissed finding ({reason}) for fingerprint {fingerprint}.")
            return True, ticket_id, "dismissed"

        if status == "RESOLVED":
            # Allow regression re-open — bug returned after fix
            return False, ticket_id, "resolved"

        # No record found → new incident
        return False, None, None

    def _append_ledger(self, entry: Dict[str, Any]) -> None:
        """Append entry to JSONL ledger for persistent deduplication."""
        if not self.dry_run:
            with self.ledger_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _update_ledger_status(self, fingerprint: str, new_status: str, reason: Optional[str] = None) -> bool:
        """Append new status entry to JSONL ledger (append-only, latest status wins on read)."""
        if not self.ledger_path.exists():
            return False
        
        # Get the latest entry to copy metadata
        latest_entry = None
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("error_fingerprint") == fingerprint:
                    latest_entry = entry
            except json.JSONDecodeError:
                continue
        
        if not latest_entry:
            return False
        
        # Append new status entry
        new_entry = {
            "ticket_id": latest_entry.get("ticket_id"),
            "error_fingerprint": fingerprint,
            "severity": latest_entry.get("severity"),
            "summary": latest_entry.get("summary"),
            "status": new_status,
            "resolution_reason": reason,
            "resolved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "previous_status": latest_entry.get("status"),
        }
        
        if not self.dry_run:
            with self.ledger_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(new_entry, ensure_ascii=False) + "\n")
        return True

    def _create_eval_stub(self, fingerprint: str, ticket_id: str, reason: str, error_trace: str) -> None:
        """Create Configuration Regression Eval stub for resolved incident.
        
        Per AI-Native SDLC Playbook: Every resolved production incident must
        generate an eval case to prevent regression when agent behavior files change.
        """
        eval_dir = Path("tests/evals")
        if not self.dry_run:
            eval_dir.mkdir(parents=True, exist_ok=True)
        
        eval_path = eval_dir / f"eval_{fingerprint}.json"
        
        eval_data = {
            "fingerprint": fingerprint,
            "ticket_id": ticket_id,
            "resolved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "resolution_reason": reason,
            "original_error_trace": error_trace[:2000],
            "eval_type": "configuration_regression",
            "description": f"Regression test for {ticket_id}. Ensures agent behavior changes don't reintroduce this failure class.",
            "test_criteria": [
                "Agent must detect this error pattern in post-deploy verification",
                "Agent must classify severity correctly (Tier 2/3)",
                "Agent must generate correct ticket type (ATOMIC_TICKET/intent.md)"
            ],
            "agent_files_to_monitor": [
                "AGENTS.md",
                "skills/*/SKILL.md",
                ".githooks/*",
                "scripts/auto_intent_generator.py"
            ]
        }
        
        if not self.dry_run:
            eval_path.write_text(json.dumps(eval_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[AUTO-INTENT] Created Configuration Regression Eval stub: {eval_path}")

    def resolve_incident(self, fingerprint: str, reason: str) -> bool:
        """Mark an incident as RESOLVED with a reason and create eval stub."""
        if not fingerprint:
            print("[AUTO-INTENT] Error: fingerprint required for --resolve")
            return False
        if not reason:
            print("[AUTO-INTENT] Error: --reason required for --resolve")
            return False

        # Get original error trace for eval stub
        status, ticket_id, _ = self._get_latest_status(fingerprint)
        error_trace = self.data.get("error_trace") or self.data.get("raw_log") or ""

        # Update SQLite (update regardless of current status)
        sqlite_updated = False
        if not self.dry_run:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE post_deploy_escapes SET status = 'RESOLVED', resolution_reason = ? WHERE error_fingerprint = ?",
                    (reason, fingerprint),
                )
                conn.commit()
                sqlite_updated = cursor.rowcount > 0
        else:
            # dry-run: check existence
            if self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    row = conn.execute("SELECT 1 FROM post_deploy_escapes WHERE error_fingerprint = ?", (fingerprint,)).fetchone()
                    sqlite_updated = row is not None

        # Update JSONL ledger
        ledger_updated = self._update_ledger_status(fingerprint, "RESOLVED", reason)

        # Create Configuration Regression Eval stub (even if dry-run for preview)
        self._create_eval_stub(fingerprint, ticket_id or f"KAN-INC-{fingerprint[:6].upper()}", reason, error_trace)

        if self.dry_run:
            exists = self._get_latest_status(fingerprint)[0] is not None
            if exists:
                print(f"[AUTO-INTENT] [DRY-RUN] Would mark incident {fingerprint} RESOLVED: {reason}")
                return True
            print(f"[AUTO-INTENT] No incident found for fingerprint {fingerprint}")
            return False

        if sqlite_updated or ledger_updated:
            print(f"[AUTO-INTENT] Incident {fingerprint} marked RESOLVED: {reason}")
            return True
        else:
            print(f"[AUTO-INTENT] No incident found for fingerprint {fingerprint}")
            return False

    def dismiss_incident(self, fingerprint: str, reason: str) -> bool:
        """Mark an incident as DISMISSED with a reason (e.g., false alarm)."""
        if not fingerprint:
            print("[AUTO-INTENT] Error: fingerprint required for --dismiss")
            return False
        if not reason:
            print("[AUTO-INTENT] Error: --reason required for --dismiss")
            return False

        # Update SQLite (update regardless of current status)
        sqlite_updated = False
        if not self.dry_run:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE post_deploy_escapes SET status = 'DISMISSED', resolution_reason = ? WHERE error_fingerprint = ?",
                    (reason, fingerprint),
                )
                conn.commit()
                sqlite_updated = cursor.rowcount > 0
        else:
            if self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    row = conn.execute("SELECT 1 FROM post_deploy_escapes WHERE error_fingerprint = ?", (fingerprint,)).fetchone()
                    sqlite_updated = row is not None

        # Update JSONL ledger
        ledger_updated = self._update_ledger_status(fingerprint, "DISMISSED", reason)

        if self.dry_run:
            exists = self._get_latest_status(fingerprint)[0] is not None
            if exists:
                print(f"[AUTO-INTENT] [DRY-RUN] Would mark incident {fingerprint} DISMISSED: {reason}")
                return True
            print(f"[AUTO-INTENT] No incident found for fingerprint {fingerprint}")
            return False

        if sqlite_updated or ledger_updated:
            print(f"[AUTO-INTENT] Incident {fingerprint} marked DISMISSED: {reason}")
            return True
        else:
            print(f"[AUTO-INTENT] No incident found for fingerprint {fingerprint}")
            return False

    def triage_severity(self) -> str:
        """Determines Tier 2 (Functional bug) vs Tier 3 (Core/Security breach)."""
        category = str(self.data.get("category", "")).lower()
        error_text = (str(self.data.get("error_trace", "")) + " " + str(self.data.get("summary", ""))).lower()

        security_keywords = ["injection", "auth", "rce", "token_leak", "secret", "tamper", "redteam_attack"]
        if any(k in category or k in error_text for k in security_keywords):
            return "Tier 3"
        return "Tier 2"

    def synthesize(self) -> Optional[str]:
        if self.action != "synthesize":
            return None
            
        fingerprint = self.compute_fingerprint()
        is_dup, existing_ticket, suppression_reason = self.check_duplicate(fingerprint)

        if is_dup:
            if suppression_reason == "dismissed":
                # Already printed in check_duplicate
                pass
            else:
                print(f"[AUTO-INTENT] Duplicate suppressed for fingerprint {fingerprint}. Linked to open ticket {existing_ticket}.")
            return None

        tier = self.triage_severity()
        ticket_id = f"KAN-INC-{fingerprint[:6].upper()}"
        summary = self.data.get("summary", "Automated Post-Deployment Verification Failure")
        error_body = self.data.get("error_trace") or self.data.get("raw_log") or "No detailed stack trace available."

        # Check if this is a regression re-open
        status, original_ticket, _ = self._get_latest_status(fingerprint)
        is_regression = (status == "RESOLVED")
        
        if is_regression and original_ticket:
            # Update ticket_id to show regression and add note
            ticket_id = f"{original_ticket}-REGRESSION"
            summary = f"[REGRESSION of {original_ticket}] {summary}"

        if tier == "Tier 3":
            target_path = Path(f"docs/specs/intent-{ticket_id.lower()}.md")
            content = f"""# Incident Intent: {ticket_id}

- **Source:** Post-Deployment Verification / Red Team Attack Simulation
- **Risk Tier:** Tier 3 (Strict Governance / PO Sign-Off Required)
- **Error Fingerprint:** `{fingerprint}`

## Summary
{summary}

## Diagnostic Evidence
```text
{error_body[:2000]}
```

## Required Actions (AI-SDLC Invariants)

1. Human Security Lead / Product Owner sign-off on scope.
2. Architecture Decision Record (ADR) update in `docs/adr/` if structural boundaries were altered.
3. Add non-regressing evaluation diff to `tests/evals/`.
"""
        else:
            target_path = Path("ATOMIC_TICKET.md")
            regression_note = f"\n* **Regression Of:** {original_ticket}\n" if is_regression else ""
            content = f"""# ATOMIC TICKET: {ticket_id}

## Metadata

* **Ticket ID:** {ticket_id}
* **Summary:** Fix regression: {summary}
* **Risk Tier:** {tier}{regression_note}
* **Authoritative Source:** Automated Continuous Evaluation (`scripts/auto_intent_generator.py`)
* **Error Fingerprint:** `{fingerprint}`

## Acceptance Criteria

1. [ ] Replicate error with a failing integration test under `tests/integration/`
2. [ ] Transition TDD: `SPEC_VERIFIED` -> `TDD_RED_INTEGRATION` -> `TDD_GREEN_INTEGRATION`
3. [ ] Keep all frozen test baselines intact (Anti-Tamper enforced)
4. [ ] Pass Layered Review checks (`code_reviewer.py`)
"""

        if self.dry_run:
            print(f"[AUTO-INTENT DRY-RUN] Would synthesize {target_path} for {ticket_id} ({tier})")
            return str(target_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        # Record in SQLite - use upsert to handle re-opening resolved incidents (regression)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO post_deploy_escapes (ticket_id, error_fingerprint, severity, summary, status, resolution_reason)
                VALUES (?, ?, ?, ?, 'OPEN', NULL)
                ON CONFLICT(error_fingerprint) DO UPDATE SET
                    ticket_id = excluded.ticket_id,
                    severity = excluded.severity,
                    summary = excluded.summary,
                    status = 'OPEN',
                    occurrence_count = occurrence_count + 1,
                    last_seen = CURRENT_TIMESTAMP,
                    resolution_reason = NULL
                """,
                (ticket_id, fingerprint, tier, summary),
            )
            conn.commit()

        # Record in JSONL ledger (persistent across CI runs)
        ledger_entry = {
            "ticket_id": ticket_id,
            "error_fingerprint": fingerprint,
            "severity": tier,
            "summary": summary,
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        self._append_ledger(ledger_entry)

        # Telemetry registration
        metrics_script = Path("scripts/ai_sdlc_metrics.py")
        if metrics_script.exists():
            subprocess.run([
                sys.executable, str(metrics_script), "record-escape",
                "--ticket-id", ticket_id,
                "--severity", tier.lower(),
                "--summary", summary
            ], capture_output=True)

        print(f"[AUTO-INTENT] Generated {target_path} for incident {ticket_id}")
        return str(target_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Closed-Loop Incident to Intent/Ticket Synthesizer")
    parser.add_argument("--report", help="Path to failure report JSON or raw log (required for synthesize)")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite metrics database")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH), help="Path to JSONL ledger for persistent deduplication")
    parser.add_argument("--dry-run", action="store_true", help="Simulate synthesis without writing files or state")
    
    # Action subcommands
    parser.add_argument("--resolve", metavar="FINGERPRINT", help="Mark incident as RESOLVED with --reason (creates eval stub)")
    parser.add_argument("--dismiss", metavar="FINGERPRINT", help="Mark incident as DISMISSED with --reason (e.g., false alarm)")
    parser.add_argument("--reason", help="Reason for resolve/dismiss action")

    args = parser.parse_args()

    # Validate arguments
    if args.resolve or args.dismiss:
        if not args.reason:
            print("Error: --reason is required for --resolve and --dismiss")
            return 1
        action = "resolve" if args.resolve else "dismiss"
        fingerprint = args.resolve or args.dismiss
        generator = AutoIntentGenerator(
            db_path=Path(args.db),
            ledger_path=Path(args.ledger),
            action=action,
            fingerprint=fingerprint,
            reason=args.reason,
            dry_run=args.dry_run,
        )
        if action == "resolve":
            success = generator.resolve_incident(fingerprint, args.reason)
        else:
            success = generator.dismiss_incident(fingerprint, args.reason)
        return 0 if success else 1
    else:
        # Synthesize action (default)
        if not args.report:
            print("Error: --report is required for synthesize action")
            return 1
        generator = AutoIntentGenerator(
            report_path=Path(args.report),
            db_path=Path(args.db),
            ledger_path=Path(args.ledger),
            dry_run=args.dry_run,
        )
        result = generator.synthesize()
        return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())