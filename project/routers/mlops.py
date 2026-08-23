"""
project/routers/mlops.py
========================
FastAPI Router for Autonomous MLOps, Distillation, and Fine-Tuning Monitoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from project.core.model_activation import get_active_model_state
from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import MINING_ONTOLOGY, HermesKnowledgeMiner
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

router = APIRouter(prefix="/api/v1/mlops", tags=["MLOps Pipeline & Monitoring"])
ROOT_DIR = Path(__file__).resolve().parents[2]


class DistillRequest(BaseModel):
    domain: str = Field(default="bazi", description="Domain to mine: bazi, ziwei, fengshui, qimen, all")
    dataset_name: str = Field(default="finetune_bazi_qwen25")
    format: str = Field(default="chatml", description="Target format: chatml, alpaca, raw")
    dry_run: bool = Field(default=False)
    force: bool = Field(default=False, description="Force re-distillation ignoring checklist cache")


class TrainRequest(BaseModel):
    dataset_path: Optional[str] = Field(default=None)
    dry_run: bool = Field(default=False)


@router.get("/status")
def get_mlops_status() -> Dict[str, Any]:
    """Get real-time status of MLOps datasets, ontology topics, and Kaggle GPU."""
    data_dir = ROOT_DIR / "project" / "data"
    datasets = []
    if data_dir.exists():
        for f in data_dir.glob("*.jsonl"):
            line_count = sum(1 for _ in open(f, encoding="utf-8")) if f.is_file() else 0
            datasets.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "sample_count": line_count,
                "modified": f.stat().st_mtime
            })

    orchestrator = FineTuneOrchestrator()
    kaggle_status = orchestrator.get_training_status()
    active_model = get_active_model_state()

    return {
        "target_model": active_model["active_model"],
        "active_model_state": active_model,
        "available_domains": list(MINING_ONTOLOGY.keys()),
        "datasets": datasets,
        "kaggle_kernel_status": kaggle_status,
        "scheduler_configured": True
    }


@router.get("/hf_status")
def get_huggingface_model_status(repo_id: Optional[str] = None) -> Dict[str, Any]:
    """Inspect and verify Hugging Face model repository tree/main files and latest commit."""
    from scripts.verify_hf_model_status import check_hf_model_status
    target_repo = repo_id or "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"
    return check_hf_model_status(repo_id=target_repo)


@router.get("/checklist")
def get_distillation_checklist() -> Dict[str, Any]:
    """Get topic-level distillation progress, completed items, and multimodal diagram stats."""
    from project.mlops.distillation.checklist_tracker import DistillationChecklistTracker
    tracker = DistillationChecklistTracker()
    return tracker.get_summary_stats()


@router.get("/datasets")
def list_datasets() -> List[Dict[str, Any]]:
    """List all curated training datasets stored locally."""
    data_dir = ROOT_DIR / "project" / "data"
    res = []
    if data_dir.exists():
        for f in data_dir.glob("*.jsonl"):
            lines = 0
            sample_preview = None
            try:
                with open(f, encoding="utf-8") as fp:
                    for i, line in enumerate(fp):
                        lines += 1
                        if i == 0:
                            sample_preview = json.loads(line)
            except Exception:
                pass
            res.append({
                "name": f.name,
                "samples": lines,
                "size_kb": round(f.stat().st_size / 1024, 2),
                "preview": sample_preview
            })
    return res


@router.post("/distill")
def trigger_distillation(req: DistillRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger on-demand knowledge distillation from NotebookLM via Hermes Agent."""
    if req.domain != "all" and req.domain not in MINING_ONTOLOGY:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Choose from: {list(MINING_ONTOLOGY.keys())} or 'all'")

    miner = HermesKnowledgeMiner()
    curator = DatasetCurator(output_dir=ROOT_DIR / "project" / "data")
    notifier = WebhookNotifier()

    force_mining = req.force or req.dry_run
    if req.domain == "all":
        domain_dict = miner.mine_all_domains(force=force_mining)
        samples = [s for d_samples in domain_dict.values() for s in d_samples]
    else:
        samples = miner.mine_domain(domain=req.domain, force=force_mining)

    stats = curator.curate_and_export(
        samples=samples,
        dataset_name=req.dataset_name,
        target_format=req.format
    )

    background_tasks.add_task(notifier.notify_distillation_complete, stats)

    return {
        "status": "SUCCESS",
        "domain": req.domain,
        "stats": stats
    }


@router.post("/train")
def trigger_training(req: TrainRequest) -> Dict[str, Any]:
    """Trigger Kaggle GPU fine-tuning execution."""
    orchestrator = FineTuneOrchestrator()
    res = orchestrator.trigger_kaggle_training(
        dataset_path=req.dataset_path,
        dry_run=req.dry_run
    )
    return res


@router.post("/telegram/webhook")
async def telegram_webhook(payload: Dict[str, Any], background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Receive incoming webhook updates from Telegram Bot API and dispatch Hermes Agent tasks."""
    from project.mlops.notifications.telegram_bot import TelegramBotController
    bot = TelegramBotController()
    
    msg = payload.get("message", {})
    text = msg.get("text", "")
    chat_id = str(msg.get("chat", {}).get("id", ""))
    
    if text and chat_id:
        reply = bot.handle_command(text, chat_id)
        background_tasks.add_task(bot.notifier.send_direct_message, reply, chat_id)
        return {"status": "ok", "action": "dispatched", "command": text}
    
    return {"status": "ok", "action": "ignored"}
