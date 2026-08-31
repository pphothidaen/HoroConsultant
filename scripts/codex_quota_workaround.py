#!/usr/bin/env python3
"""Codex Multi-Account Quota & Status Workaround Helper.

Implements 4 operational workaround patterns to inspect and monitor
codex1, codex2, codex3 account health, token burn rates, and rate limits:
1. Local Token Burn Rate Ledger (1h, 3h, 24h tokens from rollout logs)
2. Active Micro-Canary Probe (fast read-only ephemeral test for 429/limits)
3. Auth & Login Heartbeat Check (session validity)
4. Dashboard & Web UI Context Guidance
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any

KNOWN_ACCOUNTS = ("codex1", "codex2", "codex3")
BASE_ACCOUNTS_DIR = "/Users/kimlenglim/.ai-accounts/codex"


def get_account_home(alias: str) -> str:
    """Resolve account home path."""
    idx = alias.replace("codex", "")
    return os.path.join(BASE_ACCOUNTS_DIR, f"account{idx}")


def check_auth_status(alias: str) -> dict[str, Any]:
    """Workaround 3: Auth & Login Heartbeat Check."""
    home = get_account_home(alias)
    if not os.path.isdir(home):
        return {"alias": alias, "status": "NOT_FOUND", "logged_in": False}

    wrapper = shutil.which(alias) or f"/Users/kimlenglim/.local/bin/{alias}"
    env = dict(os.environ)
    env["CODEX_HOME"] = home

    try:
        cmd = [wrapper, "login", "status"] if os.path.exists(wrapper) else ["codex", "login", "status"]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)
        out = (proc.stdout + proc.stderr).strip()
        logged_in = "Logged in using" in out
        return {
            "alias": alias,
            "status": "OK" if logged_in else "UNAUTHENTICATED",
            "logged_in": logged_in,
            "raw": out.splitlines()[0] if out else "no output",
        }
    except Exception as exc:
        return {"alias": alias, "status": "ERROR", "logged_in": False, "error": str(exc)}


def calculate_token_burn_rate(alias: str) -> dict[str, Any]:
    """Workaround 1: Local Token Burn Rate & Activity Ledger."""
    home = get_account_home(alias)
    now = time.time()
    one_hour_ago = now - 3600
    three_hours_ago = now - 10800
    day_ago = now - 86400

    sessions_24h = 0
    t1 = t3 = t24 = 0

    rollouts = glob.glob(f"{home}/sessions/**/rollout*.jsonl", recursive=True)
    for fpath in rollouts:
        try:
            mtime = os.path.getmtime(fpath)
            if mtime < day_ago:
                continue
            sessions_24h += 1
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "token_count" not in line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get("type") == "event_msg":
                            payload = d.get("payload", {})
                            if payload.get("type") == "token_count":
                                last_u = payload.get("info", {}).get("last_token_usage", {})
                                tot = int(last_u.get("total_tokens", 0))
                                t24 += tot
                                if mtime >= three_hours_ago:
                                    t3 += tot
                                if mtime >= one_hour_ago:
                                    t1 += tot
                    except Exception:
                        pass
        except Exception:
            pass

    # Determine load band
    if t1 > 10_000_000:
        load_band = "HEAVY"
    elif t1 > 1_000_000:
        load_band = "MODERATE"
    elif t3 > 0:
        load_band = "LOW"
    else:
        load_band = "IDLE"

    return {
        "alias": alias,
        "active_sessions_24h": sessions_24h,
        "tokens_1h": t1,
        "tokens_3h": t3,
        "tokens_24h": t24,
        "load_band": load_band,
    }


def run_canary_probe(alias: str) -> dict[str, Any]:
    """Workaround 2: Active Micro-Canary Probe."""
    home = get_account_home(alias)
    wrapper = shutil.which(alias) or f"/Users/kimlenglim/.local/bin/{alias}"
    env = dict(os.environ)
    env["CODEX_HOME"] = home

    cmd = [
        wrapper if os.path.exists(wrapper) else "codex",
        "exec",
        "--ephemeral",
        "-s",
        "read-only",
        "-a",
        "never",
        "--skip-git-repo-check",
        "ping",
    ]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            return {"alias": alias, "probe_status": "PASS", "rate_limited": False}
        err = proc.stderr.lower()
        is_429 = "rate limit" in err or "429" in err or "exceeded" in err
        return {
            "alias": alias,
            "probe_status": "RATE_LIMITED" if is_429 else "FAIL",
            "rate_limited": is_429,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"alias": alias, "probe_status": "TIMEOUT", "rate_limited": False}
    except Exception as exc:
        return {"alias": alias, "probe_status": "ERROR", "error": str(exc), "rate_limited": False}


def get_supported_models(alias: str) -> dict[str, Any]:
    """Inspect supported models and reasoning efforts from models_cache.json."""
    home = get_account_home(alias)
    fpath = os.path.join(home, "models_cache.json")
    if not os.path.exists(fpath):
        return {"alias": alias, "models": []}
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        out = []
        for m in data.get("models", []):
            out.append({
                "slug": m.get("slug"),
                "display_name": m.get("display_name"),
                "default_effort": m.get("default_reasoning_level"),
                "supported_efforts": [e.get("effort") for e in m.get("supported_reasoning_levels", [])],
                "context_window": m.get("context_window"),
                "max_context_window": m.get("max_context_window"),
            })
        return {"alias": alias, "models": out}
    except Exception as exc:
        return {"alias": alias, "models": [], "error": str(exc)}


def classify_quota_tier(
    burn_rate: dict[str, Any],
    auth: dict[str, Any] | None = None,
    probe: dict[str, Any] | None = None,
    quota_percent: float | None = None,
) -> dict[str, Any]:
    """Classify account state into 4 governance tiers with adaptive polling."""
    alias = burn_rate.get("alias", "unknown")
    t1 = burn_rate.get("tokens_1h", 0)
    load = burn_rate.get("load_band", "UNKNOWN")

    # Check for hard exhaustion / 429
    is_rate_limited = bool(probe and probe.get("rate_limited"))
    is_unauth = bool(auth and auth.get("status") == "UNAUTHENTICATED")
    is_low_quota = quota_percent is not None and quota_percent < 10.0

    if is_rate_limited or is_low_quota or is_unauth:
        return {
            "tier": 4,
            "tier_code": "TIER_4_RED",
            "tier_name": "Tier 4: Exhausted (Red)",
            "alias": alias,
            "max_concurrency": 0,
            "poll_interval_sec": 0,
            "status": "EXHAUSTED",
            "action_required": "Immediate circuit break. Dump tickets to HANDOFF.md Rescue Queue and failover.",
        }

    if (quota_percent is not None and quota_percent < 20.0) or t1 > 10_000_000 or load == "HEAVY":
        return {
            "tier": 3,
            "tier_code": "TIER_3_ORANGE",
            "tier_name": "Tier 3: Critical (Orange)",
            "alias": alias,
            "max_concurrency": 1,
            "poll_interval_sec": 30,
            "status": "CRITICAL",
            "action_required": "High-frequency poll (30s). Max 1 concurrency. Pre-commit state to disk.",
        }

    if (quota_percent is not None and quota_percent < 40.0) or t1 > 1_000_000 or load == "MODERATE":
        return {
            "tier": 2,
            "tier_code": "TIER_2_AMBER",
            "tier_name": "Tier 2: Warning (Amber)",
            "alias": alias,
            "max_concurrency": 2,
            "poll_interval_sec": 120,
            "status": "WARNING",
            "action_required": "Moderate-frequency poll (120s). Max 2 concurrency. Warn operator.",
        }

    return {
        "tier": 1,
        "tier_code": "TIER_1_GREEN",
        "tier_name": "Tier 1: Normal (Green)",
        "alias": alias,
        "max_concurrency": 3,
        "poll_interval_sec": 600,
        "status": "NORMAL",
        "action_required": "Normal poll (600s). Max 3 concurrency. Standard multi-agent dispatch allowed.",
    }


def get_interrupted_threads(alias: str, limit: int = 10) -> list[dict[str, Any]]:
    """Inspect state_5.sqlite and thread_history_1.sqlite for recent interrupted/failed threads."""
    import sqlite3
    home = get_account_home(alias)
    state_db = os.path.join(home, "state_5.sqlite")
    hist_db = os.path.join(home, "thread_history_1.sqlite")
    if not os.path.exists(state_db):
        return []

    results = []
    try:
        conn = sqlite3.connect(state_db)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, agent_role, model, reasoning_effort, created_at FROM threads ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        threads = cur.fetchall()
        conn.close()

        err_map = {}
        if os.path.exists(hist_db):
            hconn = sqlite3.connect(hist_db)
            hcur = hconn.cursor()
            for tid, _, _, _, _, _ in threads:
                hcur.execute(
                    "SELECT status, error_json FROM thread_turns WHERE thread_id = ? ORDER BY rollout_ordinal DESC LIMIT 1",
                    (tid,),
                )
                r = hcur.fetchone()
                if r:
                    err_map[tid] = {"turn_status": r[0], "error_json": r[1]}
            hconn.close()

        for tid, title, role, model, effort, cat in threads:
            turn_info = err_map.get(tid, {})
            results.append({
                "thread_id": tid,
                "title": title,
                "role": role or "unknown",
                "model": model or "unknown",
                "reasoning_effort": effort or "unknown",
                "created_at": cat,
                "turn_status": turn_info.get("turn_status", "UNKNOWN"),
                "error": turn_info.get("error_json"),
            })
    except Exception:
        pass
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex Quota & Status Workaround Monitor")
    parser.add_argument(
        "--mode",
        choices=["summary", "burn-rate", "probe", "auth", "models", "tier", "rescue"],
        default="summary",
    )
    parser.add_argument("--alias", choices=KNOWN_ACCOUNTS, default=None, help="Target alias")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    aliases = [args.alias] if args.alias else list(KNOWN_ACCOUNTS)
    results = {}

    for alias in aliases:
        item: dict[str, Any] = {}
        if args.mode in ("summary", "burn-rate", "tier"):
            item["burn_rate"] = calculate_token_burn_rate(alias)
        if args.mode in ("summary", "auth", "tier"):
            item["auth"] = check_auth_status(alias)
        if args.mode == "probe":
            item["probe"] = run_canary_probe(alias)
        if args.mode == "models":
            item["models"] = get_supported_models(alias)
        if args.mode == "tier":
            item["tier_info"] = classify_quota_tier(item.get("burn_rate", {}), item.get("auth", {}))
        if args.mode == "rescue":
            item["interrupted_threads"] = get_interrupted_threads(alias)
        results[alias] = item

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print("=" * 80)
    print(f"[INFO] Codex Quota & Workaround Status Monitor (Mode: {args.mode.upper()})")
    print("=" * 80)

    if args.mode == "summary":
        print(f"{'Alias':<10} | {'Auth':<12} | {'Tier':<20} | {'Tokens (1h)':<14} | {'Tokens (24h)':<14}")
        print("-" * 80)
        for alias, data in results.items():
            auth_str = data.get("auth", {}).get("status", "UNKNOWN")
            br = data.get("burn_rate", {})
            tier_info = classify_quota_tier(br, data.get("auth", {}))
            t1 = br.get("tokens_1h", 0)
            t24 = br.get("tokens_24h", 0)
            print(f"{alias:<10} | {auth_str:<12} | {tier_info['tier_name']:<20} | {t1:>14,} | {t24:>14,}")
        print("=" * 80)
        print("[INFO] Workaround 4 (Web Dashboard): Check ChatGPT Settings per profile for exact quota caps.")
    elif args.mode == "tier":
        for alias, data in results.items():
            ti = data["tier_info"]
            print(f"[{alias}] {ti['tier_name']} | Max Concurrency: {ti['max_concurrency']} | Poll Interval: {ti['poll_interval_sec']}s")
            print(f"       Action: {ti['action_required']}")
    elif args.mode == "rescue":
        for alias, data in results.items():
            threads = data.get("interrupted_threads", [])
            print(f"\n[{alias}] Found {len(threads)} Recent Threads:")
            for t in threads:
                st = t.get("turn_status", "UNKNOWN")
                print(f"  - {t['thread_id']} | Role: {t['role']} | Status: {st} | Title: {t['title'][:60]}...")
    elif args.mode == "burn-rate":
        for alias, data in results.items():
            br = data["burn_rate"]
            print(f"[{alias}] Sessions(24h): {br['active_sessions_24h']} | 1h: {br['tokens_1h']:,} | 3h: {br['tokens_3h']:,} | 24h: {br['tokens_24h']:,} | Load: {br['load_band']}")
    elif args.mode == "auth":
        for alias, data in results.items():
            print(f"[{alias}] Auth: {data['auth']['status']} ({data['auth'].get('raw', '')})")
    elif args.mode == "probe":
        for alias, data in results.items():
            print(f"[{alias}] Canary Probe: {data['probe']['probe_status']}")
    elif args.mode == "models":
        for alias, data in results.items():
            models = data.get("models", {}).get("models", [])
            print(f"\n[{alias}] -> {len(models)} Models Supported:")
            for m in models:
                eff = m['supported_efforts']
                print(f"  - {m['slug']:<20} | Display: {m['display_name']:<18} | Efforts: {eff} | Ctx: {m['context_window']}")


if __name__ == "__main__":
    main()

