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
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from project.mlops.distillation.cookie_manager import CookieManager
from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import MINING_ONTOLOGY, HermesKnowledgeMiner
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_bot")


class TelegramBotController:
    """Handles incoming Telegram commands and interacts with Hermes Agent & MLOps tools."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.notifier = WebhookNotifier(telegram_token=self.token)
        self.miner = HermesKnowledgeMiner()
        self.curator = DatasetCurator(output_dir=ROOT_DIR / "project" / "data")
        self.orchestrator = FineTuneOrchestrator(notifier=self.notifier)
        self.cookie_mgr = CookieManager(notifier=self.notifier)

    def handle_command(self, text: str, chat_id: str) -> str:
        """Process incoming command and return response text."""
        cmd_parts = text.strip().split()
        if not cmd_parts:
            return "กรุณาระบุคำสั่ง เช่น /status หรือ /help"

        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        if cmd in ("/start", "/help"):
            return self._cmd_help()
        elif cmd == "/status":
            return self._cmd_status()
        elif cmd == "/sample":
            return self._cmd_sample()
        elif cmd == "/distill":
            domain = args[0] if args else "bazi"
            return self._cmd_distill(domain)
        elif cmd == "/train":
            return self._cmd_train()
        elif cmd == "/cookie":
            return self._cmd_cookie()
        else:
            return f"❌ ไม่รู้จักคำสั่ง <code>{cmd}</code>\nพิมพ์ /help เพื่อดูคำสั่งทั้งหมด"

    def _cmd_help(self) -> str:
        return (
            "🤖 <b>คำสั่งสำหรับสั่งการ Hermes Agent & MLOps:</b>\n\n"
            "• /status — ตรวจสอบสถานะ Dataset, Kaggle GPU, และ Model Hub\n"
            "• /sample — ดูตัวอย่างเนื้อหาที่สกัดได้ล่าสุดพร้อมผลวิเคราะห์ Tri-Thinking\n"
            "• /distill <code>[domain]</code> — สั่ง Hermes Agent สกัดความรู้ (เช่น /distill bazi หรือ all)\n"
            "• /train — สั่งเริ่ม Fine-Tuning บน Kaggle GPU ทันที\n"
            "• /cookie — ตรวจสอบสถานะความสดใหม่ของ Google Session Cookie\n"
            "• /help — แสดงคู่มือการใช้งานนี้"
        )

    def _cmd_status(self) -> str:
        data_dir = ROOT_DIR / "project" / "data"
        datasets = list(data_dir.glob("*.jsonl")) if data_dir.exists() else []
        total_samples = sum(sum(1 for _ in open(f, encoding="utf-8")) for f in datasets)
        
        train_status = self.orchestrator.get_training_status()
        raw_st = train_status.get("raw_status", "N/A")
        
        return (
            "📊 <b>HoroConsultant MLOps Status:</b>\n\n"
            f"• <b>Target Model:</b> <code>pphothidaen/qwen2.5-7b-bazi-instruct-4bit</code>\n"
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
            f"• <b>Target:</b> <code>pphothidaen/qwen2.5-7b-bazi-instruct-4bit</code>\n\n"
            "พิมพ์ /status เพื่อติดตามสถานะการรัน"
        )

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
