"""
project/mlops/notifications/telegram_bot.py
===========================================
Interactive Telegram Bot Controller for Hermes Agent & MLOps Operations.
Allows users to:
  • Inspect fine-tuning progress, loss curves, and dataset sizes
  • View sample mined Q&A pairs with Tri-Thinking reasoning traces
  • Trigger on-demand knowledge distillation (/distill [domain])
  • Dispatch Kaggle GPU fine-tuning (/train)
  • Check Cookie health & Google Session status (/cookie)
  • Manage HITL queue, export, and training triggers (/hitl_status, /hitl_export, /hitl_trigger)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))
ENV_FILE = ROOT_DIR / ".env"

from project.core.model_activation import get_active_model_state
from project.mlops.distillation.cookie_manager import CookieManager
from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import MINING_ONTOLOGY, HermesKnowledgeMiner
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_bot")


def persist_telegram_chat_id(chat_id: str) -> bool:
    """Persist Telegram chat ID locally when it is first discovered."""
    if not chat_id:
        return False

    current_chat = os.getenv("TELEGRAM_CHAT_ID")
    if not current_chat and ENV_FILE.exists():
        from dotenv import dotenv_values

        current_chat = dotenv_values(ENV_FILE).get("TELEGRAM_CHAT_ID")

    if current_chat:
        return False

    logger.info("[TELEGRAM] Discovered user Chat ID. Saving to local env.")
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("TELEGRAM_CHAT_ID=") or line.startswith("export TELEGRAM_CHAT_ID="):
            new_lines.append(f'TELEGRAM_CHAT_ID="{chat_id}"')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'TELEGRAM_CHAT_ID="{chat_id}"')
    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    os.environ["TELEGRAM_CHAT_ID"] = str(chat_id)
    return True


class TelegramBotController:
    """Handles incoming Telegram commands and interacts with Hermes Agent & MLOps tools."""

    def __init__(self, token: Optional[str] = None):
        if not token:
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token and ENV_FILE.exists():
                from dotenv import dotenv_values
                token = dotenv_values(ENV_FILE).get("TELEGRAM_BOT_TOKEN")

        self.token = token
        self.notifier = WebhookNotifier(telegram_token=self.token)
        self.miner = HermesKnowledgeMiner()
        self.curator = DatasetCurator(output_dir=ROOT_DIR / "project" / "data")
        self.orchestrator = FineTuneOrchestrator(notifier=self.notifier)
        self.cookie_mgr = CookieManager(notifier=self.notifier)

    def handle_command(self, text: str, chat_id: str) -> str:
        """Process incoming command and return response text."""
        # Auto-persist and sync chat_id if not present
        if chat_id:
            self._ensure_chat_id_synced(chat_id)

        cmd_parts = text.strip().split()
        if not cmd_parts:
            return "กรุณาระบุคำสั่ง เช่น /status หรือ /help"

        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        if cmd in ("/start", "/help"):
            return self._cmd_help()
        elif cmd in ("/status", "/mlops_status", "/mlops"):
            return self._cmd_status()
        elif cmd == "/sample":
            return self._cmd_sample()
        elif cmd == "/hitl_status":
            return self._cmd_hitl_status()
        elif cmd == "/hitl_queue":
            return self._cmd_hitl_queue()
        elif cmd == "/hitl_export":
            return self._cmd_hitl_export()
        elif cmd == "/hitl_trigger":
            force = "--force" in args
            dry_run = "--dry" in args or "--dry-run" in args
            return self._cmd_hitl_trigger(force=force, dry_run=dry_run)
        elif cmd in ("/distill", "/extract", "/mine"):
            domain = args[0] if args else "bazi"
            return self._cmd_distill(domain)
        elif cmd in ("/train", "/finetune"):
            return self._cmd_train()
        elif cmd in ("/cookie", "/cookie_check", "/cookie_status"):
            return self._cmd_cookie()
        elif cmd in ("/kaggle_status", "/gpu_status"):
            return self._cmd_kaggle_status()
        elif cmd in ("/kaggle_sync", "/pull_logs"):
            return self._cmd_kaggle_sync()
        else:
            return f"❌ ไม่รู้จักคำสั่ง <code>{cmd}</code>\nพิมพ์ /help เพื่อดูคำสั่งทั้งหมด"

    def _ensure_chat_id_synced(self, chat_id: str):
        """Auto-save chat_id to .env and push to GitHub Secrets if not already saved."""
        if persist_telegram_chat_id(chat_id):
            # Sync to GitHub Secrets
            if shutil.which("gh"):
                try:
                    from dotenv import dotenv_values
                    prod = dotenv_values(ROOT_DIR / ".env.production")
                    gh_tok = prod.get("GH_TOKEN") or os.getenv("GH_TOKEN")
                    gh_env = os.environ.copy()
                    if gh_tok:
                        gh_env["GH_TOKEN"] = str(gh_tok)
                    subprocess.run(
                        [
                            "gh",
                            "secret",
                            "set",
                            "TELEGRAM_CHAT_ID",
                            "-R",
                            "pphothidaen/HoroConsultant",
                            "--body",
                            str(chat_id),
                        ],
                        env=gh_env,
                        capture_output=True,
                        timeout=10
                    )
                    logger.info("[TELEGRAM] Chat ID synced to GitHub Secrets.")
                except Exception as e:
                    logger.warning(f"[TELEGRAM] GH sync note: {e}")

    def _cmd_help(self) -> str:
        return (
            "🤖 <b>คำสั่งสำหรับสั่งการ Hermes Agent & MLOps:</b>\n\n"
            "• /status หรือ /mlops — ตรวจสอบสถานะ Dataset, Kaggle GPU, และ Model Hub\n"
            "• /sample — ดูตัวอย่างเนื้อหาที่สกัดได้ล่าสุดพร้อมผลวิเคราะห์ Tri-Thinking\n"
            "• /distill <code>[domain]</code> — สั่ง Hermes Agent สกัดความรู้จาก NotebookLM (เช่น /distill bazi หรือ all)\n"
            "• /train หรือ /finetune — สั่งเริ่ม Fine-Tuning บน Kaggle GPU ทันที\n"
            "• /kaggle_status — ตรวจสอบสถานะ Kaggle GPU Kernel และ log ล่าสุด\n"
            "• /kaggle_sync — ดึง output และ log จาก Kaggle กลับเข้าสู่ระบบ\n"
            "• /cookie — ตรวจสอบสถานะความสดใหม่ของ Google Session Cookie\n"
            "• /hitl_status — ติดตามจำนวน HITL และสถานะ trigger\n"
            "• /hitl_queue — รายละเอียดคิว HITL\n"
            "• /hitl_export — Export JSONL จาก HITL reviewed ทั้งหมด\n"
            "• /hitl_trigger [--force] [--dry] — Trigger fine-tune จาก HITL ได้ทันที\n"
            "• /help — แสดงคู่มือการใช้งานนี้"
        )

    def _cmd_status(self) -> str:
        data_dir = ROOT_DIR / "project" / "data"
        datasets = list(data_dir.glob("*.jsonl")) if data_dir.exists() else []
        total_samples = sum(sum(1 for _ in open(f, encoding="utf-8")) for f in datasets)
        active_model = get_active_model_state()
        
        train_status = self.orchestrator.get_training_status()
        raw_st = train_status.get("raw_status", "N/A")
        
        return (
            "📊 <b>HoroConsultant MLOps Status:</b>\n\n"
            f"• <b>Active Model:</b> <code>{active_model.get('active_model', 'unknown')}</code>\n"
            f"• <b>Model Version:</b> <code>{active_model.get('model_version', 'unknown')}</code>\n"
            f"• <b>Model Source:</b> <code>{active_model.get('source', 'bootstrap')}</code>\n"
            f"• <b>Curated Datasets:</b> <code>{len(datasets)} files</code>\n"
            f"• <b>Total Training Samples:</b> <code>{total_samples} samples</code>\n"
            f"• <b>Kaggle GPU Kernel:</b> <code>{train_status.get('kernel_id')}</code>\n"
            f"• <b>Kernel Status:</b> <code>{raw_st}</code>\n"
            f"• <b>Domains Active:</b> <code>{', '.join(MINING_ONTOLOGY.keys())}</code>"
        )

    def _cmd_sample(self) -> str:
        data_dir = ROOT_DIR / "project" / "data"
        jsonl_files = sorted(list(data_dir.glob("*.jsonl")), key=lambda p: p.stat().st_mtime, reverse=True)
        if not jsonl_files:
            return "⚠️ ยังไม่พบชุดข้อมูลในระบบ กรุณาใช้คำสั่ง /distill ก่อน"

        latest_file = jsonl_files[0]
        sample_record = None
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                for line in f:
                    sample_record = json.loads(line)
                    break
        except Exception as e:
            return f"❌ ไม่สามารถอ่านไฟล์ตัวอย่างได้: {e}"

        if not sample_record:
            return "⚠️ ไฟล์ชุดข้อมูลว่างเปล่า"

        instr = ""
        output = ""
        if "messages" in sample_record:
            for m in sample_record["messages"]:
                if m["role"] == "user":
                    instr = m["content"]
                elif m["role"] == "assistant":
                    output = m["content"]
        else:
            instr = sample_record.get("instruction", "")
            output = sample_record.get("output", "")

        audit = sample_record.get("metadata", {}).get("audit_trace", {})
        sys_note = audit.get("systems_perspective", "Systems Verified")
        crit_note = audit.get("critical_perspective", "Canonical Checked")
        inv_note = audit.get("inversion_perspective", "Premortem Analyzed")

        return (
            f"🔍 <b>ตัวอย่างเนื้อหาจากการสกัดล่าสุด ({latest_file.name}):</b>\n\n"
            f"<b>โจทย์/คำถาม:</b>\n<i>{instr[:200]}</i>\n\n"
            f"<b>🧠 การวิเคราะห์ Tri-Thinking:</b>\n"
            f"• <b>Systems:</b> <code>{sys_note[:80]}...</code>\n"
            f"• <b>Critical:</b> <code>{crit_note[:80]}...</code>\n"
            f"• <b>Inversion:</b> <code>{inv_note[:80]}...</code>\n\n"
            f"<b>คำตอบที่ผ่านการ Fine-tune:</b>\n"
            f"{output[:300]}..."
        )

    def _cmd_distill(self, domain: str) -> str:
        if domain != "all" and domain not in MINING_ONTOLOGY:
            return f"❌ Domain ไม่ถูกต้อง เลือกได้จาก: {list(MINING_ONTOLOGY.keys())} หรือ all"

        if domain == "all":
            all_res = self.miner.mine_all_domains()
            samples = [s for sub in all_res.values() for s in sub]
        else:
            samples = self.miner.mine_domain(domain=domain)

        stats = self.curator.curate_and_export(
            samples=samples,
            dataset_name=f"bazi_{domain}_manual",
            target_format="chatml"
        )
        return (
            f"✅ <b>Hermes Agent สกัดความรู้สำเร็จ ({domain.upper()}):</b>\n\n"
            f"• <b>Total Mined:</b> <code>{stats['total_input']}</code>\n"
            f"• <b>Validated & Saved:</b> <code>{stats['final_unique_count']}</code>\n"
            f"• <b>File:</b> <code>{stats['output_path']}</code>\n\n"
            "พิมพ์ /sample เพื่อดูตัวอย่างข้อความที่สกัดได้"
        )

    def _cmd_train(self) -> str:
        res = self.orchestrator.trigger_kaggle_training(dry_run=False)
        return (
            "⚡ <b>สั่งเริ่ม Fine-Tuning บน Kaggle GPU แล้ว:</b>\n\n"
            f"• <b>Kernel:</b> <code>{res.get('kernel_id')}</code>\n"
            f"• <b>Status:</b> <b>{res.get('status')}</b>\n"
            f"• <b>Target:</b> <code>{res.get('target_model', 'pphothidaen/qwen2.5-7b-bazi-instruct-4bit')}</code>\n\n"
            "พิมพ์ /status เพื่อติดตามสถานะการรัน"
        )

    def _cmd_hitl_status(self) -> str:
        from project.hitl_router import HITL_AUTOTRAIN_ENABLED, HITL_AUTOTRAIN_THRESHOLD, load_hitl_db, _approved_hitl_count
        from project.hitl_router import build_queue_items, load_catalog

        state = load_hitl_db()
        reviews = state.get("reviews", {})
        automation = state.get("automation", {})
        approved_count = _approved_hitl_count(reviews)
        next_threshold = automation.get("next_trigger_count", HITL_AUTOTRAIN_THRESHOLD)
        remaining = max(next_threshold - approved_count, 0)
        active_model = get_active_model_state()
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
            f"• <b>Pending conflict:</b> <code>{pending_conflict}</code>\n"
            f"• <b>Next trigger target:</b> <code>{next_threshold}</code>\n"
            f"• <b>Need more:</b> <code>{remaining}</code>\n"
            f"• <b>Total triggers:</b> <code>{automation.get('total_triggers', 0)}</code>\n"
            f"• <b>Active model:</b> <code>{active_model.get('active_model')}</code>\n"
            f"• <b>Last trigger:</b> <code>{automation.get('last_triggered_at') or 'N/A'}</code>"
        )

    def _cmd_hitl_queue(self) -> str:
        from project.hitl_router import build_queue_items, load_catalog, load_hitl_db

        state = load_hitl_db()
        catalog = load_catalog()
        queue = build_queue_items(catalog, state)
        pending = [i for i in queue if i.get("status") == "pending"]
        if not queue:
            return "🗒️ ยังไม่มีรายการใน HITL queue"

        pending_hitl = [i for i in pending if i.get("required_human_review", False)]
        pending_conflict = [i for i in pending if i.get("conflict_detected", False)]
        by_domain: dict[str, int] = {}
        for item in pending_hitl:
            dom = item.get("source_domain", "catalog")
            by_domain[dom] = by_domain.get(dom, 0) + 1
        domain_lines = ", ".join(f"{k}:{v}" for k, v in sorted(by_domain.items())) if by_domain else "N/A"

        return (
            "📋 <b>HITL Queue Summary</b>\n"
            f"• <b>ทั้งหมด:</b> <code>{len(queue)}</code>\n"
            f"• <b>รอรีวิว:</b> <code>{len(pending)}</code>\n"
            f"• <b>รอ Human Review:</b> <code>{len(pending_hitl)}</code>\n"
            f"• <b>กรณีขัดแย้ง:</b> <code>{len(pending_conflict)}</code>\n"
            f"• <b>แบ่งตาม domain:</b> <code>{domain_lines}</code>\n"
            f"• <b>ยอด trigger ถัดไป:</b> <code>{state.get('automation', {}).get('next_trigger_count', '-')}</code>"
        )

    def _cmd_hitl_export(self) -> str:
        from project.hitl_router import load_hitl_db, _collect_hitl_export_records, _write_hitl_exports

        state = load_hitl_db()
        records = _collect_hitl_export_records(state)
        result = _write_hitl_exports(records, append=False)
        if result.get("entries", 0) == 0:
            return "⚠️ <b>ยังไม่มี HITL approve/edit</b>\n• กรุณาทำการ review ก่อน export"
        return (
            "📁 <b>HITL Export Rebuilt</b>\n"
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
        training = result.get("training", {})
        return (
            "🚀 <b>HITL Trigger Fired</b>\n"
            f"• <b>Status:</b> <code>{result.get('status')}</code>\n"
            f"• <b>Training:</b> <code>{training.get('status', 'N/A')}</code>\n"
            f"• <b>Kernel:</b> <code>{training.get('kernel_id', 'N/A')}</code>\n"
            f"• <b>Target:</b> <code>{training.get('target_model', 'N/A')}</code>"
        )

    def _cmd_kaggle_status(self) -> str:
        train_status = self.orchestrator.get_training_status()
        raw_st = train_status.get("raw_status", "N/A")
        kernel_id = train_status.get("kernel_id", "N/A")
        target = train_status.get("target_model", "N/A")

        log_file = ROOT_DIR / "project" / "kaggle_kernel" / "train_execution.log"
        tail_lines = ""
        if log_file.exists():
            tail_lines = "".join(log_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)[-8:])

        res = (
            "⚡ <b>Kaggle GPU Training Status:</b>\n\n"
            f"• <b>Kernel ID:</b> <code>{kernel_id}</code>\n"
            f"• <b>Status:</b> <b>{raw_st}</b>\n"
            f"• <b>Target Model:</b> <code>{target}</code>\n"
        )
        if tail_lines:
            res += f"\n📄 <b>Latest Local Log:</b>\n<pre>{tail_lines[:350]}</pre>\n"
        res += "\nพิมพ์ /kaggle_sync เพื่อดึง logs และโมเดลล่าสุดจาก Kaggle"
        return res

    def _cmd_kaggle_sync(self) -> str:
        try:
            cmd = [sys.executable, str(ROOT_DIR / "scripts" / "kaggle_notebook_manager.py"), "--output"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                log_file = ROOT_DIR / "project" / "kaggle_kernel" / "train_execution.log"
                tail_lines = ""
                if log_file.exists():
                    tail_lines = "".join(log_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)[-6:])
                res = (
                    "📥 <b>Kaggle Output Sync Completed!</b>\n\n"
                    "• <b>Status:</b> 🟢 <b>Success</b>\n"
                    "• <b>Destination:</b> <code>project/kaggle_kernel/</code>\n"
                )
                if tail_lines:
                    res += f"\n📄 <b>Latest Log:</b>\n<pre>{tail_lines[:300]}</pre>"
                return res
            else:
                return f"❌ <b>Kaggle Sync Failed:</b>\n<code>{proc.stderr[:300] or proc.stdout[:300]}</code>"
        except Exception as e:
            return f"❌ <b>Kaggle Sync Exception:</b>\n<code>{e}</code>"

    def _cmd_cookie(self) -> str:
        is_valid, reason = self.cookie_mgr.check_cookie_validity(skip_network=True)
        return (
            "🍪 <b>Google Session Cookie Health:</b>\n\n"
            f"• <b>Status:</b> {'🟢 ACTIVE' if is_valid else '🔴 EXPIRED/INVALID'}\n"
            f"• <b>Details:</b> <code>{reason}</code>\n"
            f"• <b>Cookie Length:</b> <code>{len(self.cookie_mgr.get_current_cookie())} chars</code>\n\n"
            "หากหมดอายุ สามารถรัน <code>python3 scripts/hermes_cookie_sync.py</code> เพื่อต่ออายุ"
        )

    def poll_updates(self, interval_sec: int = 3):
        """Run long-polling loop to listen for incoming Telegram messages."""
        if not self.token:
            logger.error("[ERROR] TELEGRAM_BOT_TOKEN not configured.")
            return

        logger.info("🤖 [TELEGRAM BOT] Starting interactive polling loop for Hermes Agent commands...")
        last_update_id = 0

        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={last_update_id + 1}&timeout=20"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        for update in data.get("result", []):
                            last_update_id = update["update_id"]
                            msg = update.get("message", {})
                            text = msg.get("text", "")
                            chat_id = str(msg.get("chat", {}).get("id", ""))
                            
                            if text and chat_id:
                                logger.info(f"[TELEGRAM RECV] Chat {chat_id}: '{text}'")
                                reply = self.handle_command(text, chat_id)
                                self.notifier.send_direct_message(reply, chat_id=chat_id)
            except Exception as e:
                logger.warning(f"[TELEGRAM POLL] Exception: {e}")
                time.sleep(interval_sec)


if __name__ == "__main__":
    bot = TelegramBotController()
    bot.poll_updates()
