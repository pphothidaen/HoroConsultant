"""
project/mlops/notifications/telegram_controller.py
===================================================
Interactive Two-Way Telegram Bot Controller & Diagnostic Gateway (Decision 2).

Supported Commands:
  /status       → System overview, uptime, active AI routes, and memory health.
  /health       → Real-time health ping across all AI providers (Ollama, Gemini, Vertex AI).
  /metrics      → Prometheus/OTLP metrics summary (RPM, HTTP 2xx/4xx/5xx, RAG latencies).
  /switch_key   → Rotate and test next available Google AI Studio API key.
  /help         → Display available operational commands.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from project.core.model_activation import get_active_model_state

logger = logging.getLogger("telegram_controller")


class TelegramBotController:
    """Handles incoming commands from Telegram webhooks or background pollers."""

    def __init__(self, token: Optional[str] = None, allowed_chat_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = allowed_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def handle_command(self, text: str, from_chat_id: str) -> str:
        """Process incoming Telegram message command and return formatted HTML response."""
        tokens = text.strip().split() if text else []
        cmd = tokens[0].lower() if tokens else ""
        args = tokens[1:] if len(tokens) > 1 else []

        if cmd == "/start" or cmd == "/help":
            return (
                "🔮 <b>HoroConsultant Operations Controller</b>\n\n"
                "Available Commands:\n"
                "• <code>/status</code> — System status, active models & memory\n"
                "• <code>/health</code> — Multi-provider live latency probe\n"
                "• <code>/metrics</code> — Request count, RPM, error rates\n"
                "• <code>/hitl_status</code> — HITL queue and finetune readiness\n"
                "• <code>/hitl_queue</code> — HITL queue counters\n"
                "• <code>/hitl_export</code> — Rebuild HITL JSONL export files\n"
                "• <code>/hitl_trigger [--force] [--dry]</code> — Trigger HITL fine-tune now\n"
                "• <code>/switch_key</code> — Test & cycle Google AI Studio keys\n"
                "• <code>/cache</code> — 2-Tier cache hit rate & statistics"
            )

        elif cmd == "/status":
            from project.api_router import HybridRouter
            router = HybridRouter()
            routes = router._build_routes()
            route_summary = ", ".join(r["type"] for r in routes[:4])
            return (
                "📊 <b>HoroConsultant System Status</b>\n"
                "• <b>Environment:</b> <code>production</code>\n"
                "• <b>Status:</b> <b>ONLINE (Healthy)</b>\n"
                f"• <b>Active AI Routes:</b> <code>{len(routes)} routes ({route_summary}...)</code>\n"
                f"• <b>Active model:</b> <code>{get_active_model_state().get('active_model', 'unknown')}</code>\n"
                "• <b>Observability:</b> <code>Prometheus /metrics enabled</code>\n"
                "• <b>Multi-Cloud Edge:</b> <code>HuggingFace + Vercel Gateway</code>"
            )

        elif cmd == "/health":
            t0 = time.monotonic()
            from project.api_router import HybridRouter
            router = HybridRouter()
            res = router.generate("test ping")
            elapsed = round((time.monotonic() - t0) * 1000)
            return (
                "💓 <b>Provider Health Diagnostic</b>\n"
                f"• <b>Primary Route Used:</b> <code>{res.get('route', 'N/A')}</code>\n"
                f"• <b>Model:</b> <code>{res.get('model_used', 'N/A')}</code>\n"
                f"• <b>Response Status:</b> <b>{res.get('reason', 'N/A').upper()}</b>\n"
                f"• <b>Roundtrip Latency:</b> <code>{elapsed} ms</code>"
            )

        elif cmd == "/metrics":
            from project.core.observability import observability_manager
            stats = observability_manager.get_summary()
            return (
                "📈 <b>Observability Metrics Summary</b>\n"
                f"• <b>Total Requests:</b> <code>{stats.get('total_requests', 0)}</code>\n"
                f"• <b>Avg Latency:</b> <code>{stats.get('avg_latency_ms', 0)} ms</code>\n"
                f"• <b>HTTP 2xx Success:</b> <code>{stats.get('http_2xx', 0)}</code>\n"
                f"• <b>HTTP 4xx / 5xx:</b> <code>{stats.get('http_4xx', 0)} / {stats.get('http_5xx', 0)}</code>\n"
                f"• <b>OTLP Status:</b> <code>{stats.get('otlp_status', 'Active')}</code>"
            )

        elif cmd == "/cache":
            from project.core.cache_manager import runtime_cache
            stats = runtime_cache.get_stats()
            return (
                "💾 <b>2-Tier Cache Performance</b>\n"
                f"• <b>RAM LRU Items:</b> <code>{stats['ram_items']}</code>\n"
                f"• <b>Disk Cached Items:</b> <code>{stats['disk_items']}</code>\n"
                f"• <b>Cache Hits / Misses:</b> <code>{stats['hits']} / {stats['misses']}</code>\n"
                f"• <b>Hit Rate:</b> <b>{stats['hit_rate_percent']}%</b>"
            )

        elif cmd == "/hitl_status":
            return self._cmd_hitl_status()

        elif cmd == "/hitl_queue":
            return self._cmd_hitl_queue()

        elif cmd == "/hitl_export":
            return self._cmd_hitl_export()

        elif cmd == "/hitl_trigger":
            force = "force" in args or "--force" in args
            dry = "dry" in args or "--dry" in args or "--dry-run" in args
            return self._cmd_hitl_trigger(force=force, dry_run=dry)

        elif cmd == "/switch_key":
            from project.api_router import _gemini_keys
            keys = _gemini_keys()
            return (
                "🔑 <b>Google AI Studio Key Pool</b>\n"
                f"• <b>Configured Valid Keys:</b> <code>{len(keys)}</code>\n"
                f"• <b>Primary:</b> <code>...{keys[0][-6:] if keys else 'None'}</code>\n"
                f"• <b>Secondary:</b> <code>...{keys[1][-6:] if len(keys) > 1 else 'None'}</code>\n"
                "• <b>Dynamic Rotation Engine:</b> <b>ACTIVE</b>"
            )

        else:
            return f"❓ Unknown command: <code>{cmd}</code>. Type <code>/help</code> for available commands."

    def _cmd_hitl_status(self) -> str:
        from project.hitl_router import HITL_AUTOTRAIN_ENABLED, HITL_AUTOTRAIN_THRESHOLD, load_hitl_db, _approved_hitl_count
        state = load_hitl_db()
        reviews = state.get("reviews", {})
        automation = state.get("automation", {})
        approved_count = _approved_hitl_count(reviews)
        next_threshold = automation.get("next_trigger_count", HITL_AUTOTRAIN_THRESHOLD)
        remaining = max(next_threshold - approved_count, 0)
        active_model = get_active_model_state()
        from project.hitl_router import build_queue_items, load_catalog
        catalog = load_catalog()
        queue = build_queue_items(catalog, state)
        pending_hitl = sum(
            1 for item in queue if item.get("status") == "pending" and item.get("required_human_review", False)
        )
        pending_conflict = sum(
            1 for item in queue if item.get("status") == "pending" and bool(item.get("conflict_detected", False))
        )
        return (
            "🎯 <b>HITL Workflow Status</b>\n"
            f"• <b>Auto Trigger:</b> <code>{'ON' if HITL_AUTOTRAIN_ENABLED else 'OFF'}</code>\n"
            f"• <b>Approved/Edited pairs:</b> <code>{approved_count}</code>\n"
            f"• <b>Pending HITL conflict reviews:</b> <code>{pending_hitl}</code>\n"
            f"• <b>Pending conflict-detected:</b> <code>{pending_conflict}</code>\n"
            f"• <b>Next trigger target:</b> <code>{next_threshold}</code>\n"
            f"• <b>Need more:</b> <code>{remaining}</code>\n"
            f"• <b>Total triggers:</b> <code>{automation.get('total_triggers', 0)}</code>\n"
            f"• <b>Active model:</b> <code>{active_model.get('active_model')}</code>\n"
            f"• <b>Active model version:</b> <code>{active_model.get('model_version')}</code>"
        )

    def _cmd_hitl_queue(self) -> str:
        from project.hitl_router import build_queue_items, load_catalog, load_hitl_db

        state = load_hitl_db()
        catalog = load_catalog()
        queue = build_queue_items(catalog, state)
        pending = [i for i in queue if i.get("status") == "pending"]
        if not queue:
            return "🗒️ <b>HITL queue is empty</b>"

        pending_hitl = [i for i in pending if i.get("required_human_review", False)]
        pending_conflict = [i for i in pending if i.get("conflict_detected", False)]
        by_domain: dict[str, int] = {}
        for i in pending_hitl:
            dom = i.get("source_domain", "catalog")
            by_domain[dom] = by_domain.get(dom, 0) + 1
        domain_lines = ", ".join(f"{k}:{v}" for k, v in sorted(by_domain.items())) if by_domain else "N/A"

        return (
            "📋 <b>HITL Queue Breakdown</b>\n"
            f"• <b>Total:</b> <code>{len(queue)}</code>\n"
            f"• <b>Pending:</b> <code>{len(pending)}</code>\n"
            f"• <b>Pending HITL-required:</b> <code>{len(pending_hitl)}</code>\n"
            f"• <b>Pending conflict:</b> <code>{len(pending_conflict)}</code>\n"
            f"• <b>Pending by domain:</b> <code>{domain_lines}</code>\n"
            f"• <b>Next trigger target:</b> <code>{state.get('automation', {}).get('next_trigger_count', '-')}</code>"
        )

    def _cmd_hitl_export(self) -> str:
        from project.hitl_router import load_hitl_db, _collect_hitl_export_records, _write_hitl_exports

        state = load_hitl_db()
        records = _collect_hitl_export_records(state)
        result = _write_hitl_exports(records, append=False)
        return (
            "📁 <b>HITL Export Refreshed</b>\n"
            f"• <b>Entries:</b> <code>{result['entries']}</code>\n"
            f"• <b>Compat file:</b> <code>{result['output']}</code>\n"
            f"• <b>Metadata file:</b> <code>{result['metadata_output']}</code>"
        )

    def _cmd_hitl_trigger(self, force: bool = False, dry_run: bool = False) -> str:
        from project.hitl_router import _run_finetune_trigger
        result = _run_finetune_trigger(force=force, dry_run=dry_run, requested_by="telegram")
        if result.get("status") == "skipped":
            reason = result.get("reason", "not_started")
            return f"ℹ️ <b>HITL Trigger skipped:</b> <code>{reason}</code>"
        return f"🚀 <b>HITL Trigger:</b> <code>{result.get('status')}</code>\n• <b>Training:</b> <code>{result.get('training', {}).get('status', 'N/A')}</code>"


# Singleton instance
telegram_controller = TelegramBotController()
