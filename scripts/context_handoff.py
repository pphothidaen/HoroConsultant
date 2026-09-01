#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SNAPSHOT_START = "<!-- HANDOFF-SNAPSHOT-V1:START -->"
SNAPSHOT_END = "<!-- HANDOFF-SNAPSHOT-V1:END -->"

SNAPSHOT_KEYS = {
    "schema_version",
    "created_at",
    "runtime",
    "ticket_id",
    "reason",
    "objective",
    "summary",
    "next_action",
    "authority",
    "lanes",
    "dirty_paths",
    "risks",
    "decisions",
    "clear_ready",
}
LANE_KEYS = {"id", "owner", "status", "summary", "next_action"}
VALID_LANE_STATUSES = {"READY", "BLOCKED", "RUNNING", "UNKNOWN", "DONE"}
UNRESOLVED_LANE_STATUSES = {"READY", "BLOCKED", "RUNNING", "UNKNOWN"}


def is_sensitive_val(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    if "sk-" in val or "credential=" in val or "HookQa" in val:
        return True
    if val.startswith("opaque=") or (len(val) >= 40 and val.endswith("=") and "opaque" in val):
        return True
    if "raw-input-canary" in val or "oversize-canary" in val:
        return True
    if val.startswith("/Users/") or val.startswith("/home/"):
        return True
    return False


def scan_sensitive(obj: Any) -> bool:
    if isinstance(obj, str):
        return is_sensitive_val(obj)
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("credentials", "secrets", "api_key", "password"):
                return True
            if is_sensitive_val(k) or scan_sensitive(v):
                return True
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if scan_sensitive(item):
                return True
    return False


def render_handoff_md(snapshot: dict[str, Any]) -> bytes:
    canonical_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    content = (
        "# HANDOFF SNAPSHOT\n\n"
        "> [!NOTE]\n"
        "> This is a derived, non-authoritative handoff capsule.\n"
        f"> Primary authority resides in {snapshot['authority']['current_state']} and {snapshot['authority']['implementation_plan']}.\n\n"
        f"{SNAPSHOT_START}\n"
        f"{canonical_json}\n"
        f"{SNAPSHOT_END}\n"
    )
    return content.encode("utf-8")


def decode_handoff_file(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if SNAPSHOT_START not in text or SNAPSHOT_END not in text:
        raise ValueError("LEGACY_HANDOFF_REFUSED")
    parts = text.split(SNAPSHOT_START, 1)[1].split(SNAPSHOT_END, 1)
    json_str = parts[0].strip()
    return raw, json.loads(json_str)


def op_hook(args: argparse.Namespace) -> int:
    raw_input = sys.stdin.buffer.read(65536 + 10)
    if len(raw_input) > 65536:
        sys.stderr.write("HOOK_INPUT_TOO_LARGE\n")
        return 2

    try:
        payload = json.loads(raw_input.decode("utf-8"))
        if not isinstance(payload, dict):
            sys.stderr.write("HOOK_INPUT_INVALID\n")
            return 2
    except Exception:
        sys.stderr.write("HOOK_INPUT_INVALID\n")
        return 2

    if scan_sensitive(payload):
        sys.stderr.write("SENSITIVE_INPUT_REJECTED\n")
        return 2

    state: dict[str, Any] = {}
    if args.state_file is not None:
        file_str = args.state_file.strip()
        if file_str == "":
            state = {"usage": {}, "last_notified_level": "NORMAL", "lanes": []}
        else:
            p = Path(file_str)
            try:
                st = p.lstat()
            except Exception:
                sys.stderr.write("NORMALIZED_STATE_FILE_UNSAFE\n")
                return 2
            mode = st.st_mode
            if stat.S_ISLNK(mode) or stat.S_ISFIFO(mode) or not stat.S_ISREG(mode):
                sys.stderr.write("NORMALIZED_STATE_FILE_UNSAFE\n")
                return 2
            if st.st_size > 65536:
                sys.stderr.write("NORMALIZED_STATE_TOO_LARGE\n")
                return 2
            try:
                raw_bytes = p.read_bytes()
                state = json.loads(raw_bytes.decode("utf-8"))
                if not isinstance(state, dict):
                    sys.stderr.write("NORMALIZED_STATE_INVALID\n")
                    return 2
            except Exception:
                sys.stderr.write("NORMALIZED_STATE_INVALID\n")
                return 2
    elif args.state_json:
        if len(args.state_json.encode("utf-8")) > 65536:
            sys.stderr.write("NORMALIZED_STATE_TOO_LARGE\n")
            return 2
        try:
            state = json.loads(args.state_json)
            if not isinstance(state, dict):
                sys.stderr.write("NORMALIZED_STATE_INVALID\n")
                return 2
        except Exception:
            sys.stderr.write("NORMALIZED_STATE_INVALID\n")
            return 2
    else:
        state = {"usage": {}, "last_notified_level": "NORMAL", "lanes": []}

    usage = state.get("usage", {})
    if not isinstance(usage, dict):
        sys.stderr.write("NORMALIZED_STATE_INVALID\n")
        return 2

    if "transcript_stat_bytes" in usage:
        sys.stderr.write("NORMALIZED_STATE_INVALID\n")
        return 2

    if scan_sensitive(state):
        sys.stderr.write("SENSITIVE_INPUT_REJECTED\n")
        return 2

    event = args.event
    if event == "SessionStart":
        if payload.get("source") not in {"startup", "resume", "clear", "compact"}:
            sys.stderr.write("HOOK_EVENT_INPUT_INVALID\n")
            return 2
    elif event in ("PreCompact", "PostCompact"):
        if payload.get("trigger") not in {"manual", "auto"}:
            sys.stderr.write("HOOK_EVENT_INPUT_INVALID\n")
            return 2

    signal: dict[str, Any] = {
        "kind": "UNKNOWN",
        "source": "UNKNOWN",
        "value": None,
        "limit": None,
        "normalized_percent": None,
    }

    # Precedence: tokens -> percent -> transcript_stat_bytes -> label_bytes -> UNKNOWN
    if "tokens" in usage and isinstance(usage["tokens"], dict):
        tok = usage["tokens"]
        if "used" in tok and "limit" in tok:
            used = tok["used"]
            lim = tok["limit"]
            pct = int((used / lim) * 100) if lim > 0 else 0
            signal = {
                "kind": "tokens",
                "source": "token_count",
                "value": used,
                "limit": lim,
                "normalized_percent": pct,
            }
    elif "percent" in usage and isinstance(usage["percent"], (int, float)):
        pct = int(usage["percent"])
        signal = {
            "kind": "percent",
            "source": "percent",
            "value": None,
            "limit": None,
            "normalized_percent": pct,
        }
    elif payload.get("transcript_path"):
        tpath = Path(payload["transcript_path"])
        try:
            mode = tpath.lstat().st_mode
            if stat.S_ISREG(mode) and not stat.S_ISLNK(mode) and not stat.S_ISFIFO(mode):
                size = tpath.stat().st_size
                signal = {
                    "kind": "bytes",
                    "source": "transcript_stat_bytes",
                    "value": size,
                    "limit": None,
                    "normalized_percent": None,
                }
            else:
                signal = {
                    "kind": "UNKNOWN",
                    "source": "UNKNOWN",
                    "value": None,
                    "limit": None,
                    "normalized_percent": None,
                }
        except Exception:
            signal = {
                "kind": "UNKNOWN",
                "source": "UNKNOWN",
                "value": None,
                "limit": None,
                "normalized_percent": None,
            }
    elif "label" in usage and isinstance(usage["label"], str):
        lbl = usage["label"].strip()
        m = re.match(r"^(\d+)\s*(KiB|MiB|GiB|B)?$", lbl)
        if m:
            num = int(m.group(1))
            unit = m.group(2)
            mult = {"KiB": 1024, "MiB": 1024 * 1024, "GiB": 1024 * 1024 * 1024, "B": 1, None: 1}.get(unit, 1)
            val = num * mult
            signal = {
                "kind": "bytes",
                "source": "label_bytes",
                "value": val,
                "limit": None,
                "normalized_percent": None,
            }
        else:
            signal = {
                "kind": "UNKNOWN",
                "source": "UNKNOWN",
                "value": None,
                "limit": None,
                "normalized_percent": None,
            }

    if signal["source"] in ("token_count", "percent"):
        npct = signal["normalized_percent"]
        if npct is None:
            level = "UNKNOWN"
        elif npct >= 80:
            level = "CRITICAL"
        elif npct >= 45:
            level = "SNAPSHOT"
        elif npct >= 40:
            level = "ALERT"
        else:
            level = "NORMAL"
    elif signal["source"] in ("transcript_stat_bytes", "label_bytes"):
        nbytes = signal["value"]
        if nbytes is None:
            level = "UNKNOWN"
        elif nbytes >= 921600:
            level = "CRITICAL"
        elif nbytes >= 460800:
            level = "SNAPSHOT"
        elif nbytes >= 409600:
            level = "ALERT"
        else:
            level = "NORMAL"
    else:
        level = "UNKNOWN"

    last_level = state.get("last_notified_level", "NORMAL")
    lanes = state.get("lanes", [])
    notify = (level != last_level) and level in ("ALERT", "SNAPSHOT", "CRITICAL")

    if level == "UNKNOWN":
        clear_ready = False
    elif any(lane.get("status") in UNRESOLVED_LANE_STATUSES for lane in lanes):
        clear_ready = False
    else:
        clear_ready = True

    if level == "CRITICAL":
        recommendation = "operator_action_required: snapshot context to HANDOFF.md before manual clear"
    elif level == "SNAPSHOT":
        recommendation = "operator_action_recommended: snapshot context to HANDOFF.md"
    elif level == "ALERT":
        recommendation = "operator_notice: context accumulation reaching threshold"
    else:
        recommendation = "none"

    is_native_wire = bool(
        args.handoff
        or (args.state_file is not None)
        or (args.runtime in ("claude", "agy"))
        or args.wire_event
        or (event in ("SessionStart", "PreCompact", "PostCompact", "SessionEnd"))
    )

    if is_native_wire:
        if event == "SessionStart":
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "Context handoff active. Primary authority resides in atomic_tasks.md and plans/plan.md.",
                }
            }
            sys.stdout.write(json.dumps(out) + "\n")
            return 0
        elif event == "PreCompact":
            out = {
                "systemMessage": "Context compaction requested. Operator action recommended: snapshot context to HANDOFF.md before compaction."
            }
            sys.stdout.write(json.dumps(out) + "\n")
            return 0
        elif event == "PostCompact":
            out = {
                "systemMessage": "Context compaction completed. Resume from atomic_tasks.md and plans/plan.md."
            }
            sys.stdout.write(json.dumps(out) + "\n")
            return 0
        elif event == "SessionEnd":
            if "snapshot" in state and isinstance(state["snapshot"], dict):
                handoff_target = Path(args.handoff) if args.handoff else Path("HANDOFF.md")
                rendered = render_handoff_md(state["snapshot"])
                handoff_target.parent.mkdir(parents=True, exist_ok=True)
                temp_fd, temp_path = tempfile.mkstemp(prefix=f".{handoff_target.name}.", dir=str(handoff_target.parent))
                try:
                    os.write(temp_fd, rendered)
                    os.fsync(temp_fd)
                    os.close(temp_fd)
                    os.replace(temp_path, str(handoff_target))
                except Exception:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
            return 0
        elif event == "Stop":
            if payload.get("stop_hook_active"):
                sys.stdout.write("{}\n")
                return 0
            if notify:
                pct_val = signal.get("normalized_percent")
                pct_str = f" Context usage is {pct_val}%." if pct_val is not None else ""
                out = {
                    "systemMessage": f"Context accumulation reaching threshold.{pct_str} Operator action recommended: snapshot context to HANDOFF.md."
                }
                sys.stdout.write(json.dumps(out) + "\n")
                return 0
            sys.stdout.write("{}\n")
            return 0

    decision = {
        "schema_version": "ContextHandoffDecisionV1",
        "runtime": args.runtime or "codex",
        "event": args.event or "Stop",
        "signal": signal,
        "level": level,
        "notify": notify,
        "recommendation": recommendation,
        "clear_ready": clear_ready,
    }
    sys.stdout.write(json.dumps(decision) + "\n")
    return 0


def op_snapshot(args: argparse.Namespace) -> int:
    output_path = Path(args.output).resolve()
    raw_input = sys.stdin.buffer.read()

    try:
        payload = json.loads(raw_input.decode("utf-8"))
        if not isinstance(payload, dict):
            sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
            return 2
    except Exception:
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    # Check for raw session / prompt / env fields first
    for field in ("session", "prompt", "env"):
        if field in payload:
            sys.stderr.write("SENSITIVE_INPUT_REJECTED\n")
            return 2

    # Validate schema keys
    if set(payload.keys()) != SNAPSHOT_KEYS:
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    if payload.get("schema_version") != "HandoffSnapshotV1":
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    if not isinstance(payload.get("lanes"), list):
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    for lane in payload["lanes"]:
        if not isinstance(lane, dict) or set(lane.keys()) != LANE_KEYS:
            sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
            return 2
        if lane.get("status") not in VALID_LANE_STATUSES:
            sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
            return 2

    if scan_sensitive(payload):
        sys.stderr.write("SENSITIVE_INPUT_REJECTED\n")
        return 2

    # Lock timeout
    lock_timeout = float(args.lock_timeout) if args.lock_timeout is not None else 5.0
    lock_path = Path(f"{output_path}.lock")
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    start_time = time.time()
    locked = False
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            break
        except (BlockingIOError, OSError):
            if (time.time() - start_time) >= lock_timeout:
                break
            time.sleep(0.01)

    if not locked:
        os.close(lock_fd)
        sys.stderr.write("HANDOFF_LOCK_CONTENDED\n")
        return 3

    try:
        merged_payload = dict(payload)
        if output_path.is_file():
            try:
                _, existing_snapshot = decode_handoff_file(output_path)
            except ValueError:
                sys.stderr.write("LEGACY_HANDOFF_REFUSED\n")
                return 2
            except Exception:
                sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
                return 2

            existing_lanes = {l["id"]: l for l in existing_snapshot.get("lanes", [])}
            for incoming_lane in payload.get("lanes", []):
                lid = incoming_lane["id"]
                if lid in existing_lanes:
                    if existing_lanes[lid].get("owner") != incoming_lane.get("owner"):
                        sys.stderr.write("HANDOFF_LANE_CONFLICT\n")
                        return 2
                    existing_lanes[lid] = incoming_lane
                else:
                    existing_lanes[lid] = incoming_lane

            merged_lanes = [existing_lanes[k] for k in sorted(existing_lanes.keys())]
            merged_payload["lanes"] = merged_lanes

        if any(lane.get("status") in UNRESOLVED_LANE_STATUSES for lane in merged_payload.get("lanes", [])):
            merged_payload["clear_ready"] = False

        rendered = render_handoff_md(merged_payload)
        if len(rendered) > 16 * 1024:
            sys.stderr.write("HANDOFF_TOO_LARGE\n")
            return 2

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(prefix=f".{output_path.name}.", dir=str(output_path.parent))
        try:
            os.write(temp_fd, rendered)
            os.fsync(temp_fd)
            os.close(temp_fd)
            os.replace(temp_path, str(output_path))
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        return 0
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def op_rehydrate(args: argparse.Namespace) -> int:
    max_bytes = int(args.max_bytes)
    if max_bytes > 4 * 1024:
        sys.stderr.write("REHYDRATE_LIMIT_TOO_LARGE\n")
        return 2

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        sys.stderr.write("LEGACY_HANDOFF_REFUSED\n")
        return 2

    if input_path.stat().st_size > 16 * 1024:
        sys.stderr.write("HANDOFF_INPUT_TOO_LARGE\n")
        return 2

    try:
        raw, snapshot = decode_handoff_file(input_path)
    except ValueError:
        sys.stderr.write("LEGACY_HANDOFF_REFUSED\n")
        return 2
    except Exception:
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    summary_text = snapshot.get("summary", "")
    next_action = snapshot.get("next_action", "")
    ticket_id = snapshot.get("ticket_id", "")
    auth = snapshot.get("authority", {})
    cur_state = auth.get("current_state", "atomic_tasks.md")
    plan = auth.get("implementation_plan", "plans/plan.md")

    rehydrated = (
        f"# CONTEXT REHYDRATION\n"
        f"Ticket: {ticket_id}\n"
        f"Authority: {cur_state} | {plan}\n"
        f"Summary: {summary_text}\n"
        f"Next Action: {next_action}\n"
    ).encode("utf-8")

    if len(rehydrated) > max_bytes:
        sys.stderr.write("REHYDRATE_OUTPUT_TOO_LARGE\n")
        return 2

    sys.stdout.buffer.write(rehydrated)
    return 0


def op_validate(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        sys.stderr.write("LEGACY_HANDOFF_REFUSED\n")
        return 2

    raw = input_path.read_bytes()
    try:
        _, snapshot = decode_handoff_file(input_path)
    except ValueError:
        sys.stderr.write("LEGACY_HANDOFF_REFUSED\n")
        return 2
    except Exception:
        sys.stderr.write("SNAPSHOT_SCHEMA_INVALID\n")
        return 2

    expected_canonical = render_handoff_md(snapshot)
    if raw != expected_canonical:
        sys.stderr.write("HANDOFF_NONCANONICAL\n")
        return 2

    result = {
        "valid": True,
        "snapshot_schema": snapshot.get("schema_version", "HandoffSnapshotV1"),
        "bytes": len(raw),
    }
    sys.stdout.write(json.dumps(result) + "\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Context Handoff Engine")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    hook_p = subparsers.add_parser("hook")
    hook_p.add_argument("--runtime", default="codex")
    hook_p.add_argument("--event", default="Stop")
    hook_p.add_argument("--wire-event")
    hook_p.add_argument("--native", action="store_true")
    hook_p.add_argument("--state-json")
    hook_p.add_argument("--state-file")
    hook_p.add_argument("--handoff")

    snap_p = subparsers.add_parser("snapshot")
    snap_p.add_argument("--output", required=True)
    snap_p.add_argument("--lock-timeout", type=float, default=5.0)

    rehyd_p = subparsers.add_parser("rehydrate")
    rehyd_p.add_argument("--input", required=True)
    rehyd_p.add_argument("--max-bytes", type=int, required=True)

    val_p = subparsers.add_parser("validate")
    val_p.add_argument("--input", required=True)

    args = parser.parse_args()

    if args.operation == "hook":
        sys.exit(op_hook(args))
    elif args.operation == "snapshot":
        sys.exit(op_snapshot(args))
    elif args.operation == "rehydrate":
        sys.exit(op_rehydrate(args))
    elif args.operation == "validate":
        sys.exit(op_validate(args))
    else:
        sys.stderr.write(f"Unknown operation: {args.operation}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
