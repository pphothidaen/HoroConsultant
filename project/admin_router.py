"""
project/admin_router.py
========================
Admin Panel API Router for Knowledge Source Management,
Gray-Zone Answer Collection, and Fine-Tune Pipeline Control.

Endpoints:
  GET  /admin/                           → Admin Dashboard UI
  GET  /admin/catalog                    → Full knowledge catalog
  GET  /admin/catalog/summary            → Coverage summary report
  GET  /admin/grayzone                   → All gray-zone questions
  POST /admin/grayzone/answer            → Submit answer for a gray-zone question
  PUT  /admin/grayzone/answer/{source_id} → Update existing answer
  DELETE /admin/grayzone/answer/{source_id} → Delete answer
  GET  /admin/finetune/status            → Fine-tune dataset statistics
  POST /admin/finetune/export-grayzone   → Build JSONL from answered gray-zone
  POST /admin/finetune/merge             → Merge all datasets into combined_train.jsonl
  POST /admin/finetune/trigger           → Trigger external AI fine-tune job
  GET  /admin/finetune/download          → Download combined_train.jsonl
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("admin_router")

ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH      = ROOT / "project" / "data" / "knowledge_catalog.json"
GRAYZONE_DB_PATH  = ROOT / "project" / "data" / "grayzone_answers.json"
SUMMARY_OUT_PATH  = ROOT / "project" / "data" / "source_summaries.json"
DATASETS_DIR      = ROOT / "project" / "rag" / "datasets"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/admin", tags=["Admin — Knowledge Management"])


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class GrayzoneAnswerRequest(BaseModel):
    source_id: str = Field(..., description="Source ID (e.g. CM-BZ-004)")
    question:  str = Field(..., description="The gray-zone question text")
    answer:    str = Field(..., description="Expert answer for fine-tuning")
    reviewer:  Optional[str] = Field(None, description="Reviewer name/identifier")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0–1")
    notes:     Optional[str] = Field(None, description="Optional review notes")


class FinetuneTriggerRequest(BaseModel):
    provider:       str  = Field("ollama", description="Provider: 'ollama', 'openai', 'together', 'gemini'")
    model_name:     str  = Field("Qwen/Qwen2.5-7B-Instruct", description="Base model name")
    dataset:        str  = Field("combined_train.jsonl", description="Dataset filename in datasets dir")
    dry_run:        bool = Field(False, description="Dry run — validate without launching")
    max_iterations: int  = Field(1000, ge=100, le=10000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_catalog() -> Dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_grayzone_db() -> Dict[str, Any]:
    if not GRAYZONE_DB_PATH.exists():
        return {"answers": {}, "metadata": {"total_answered": 0, "last_updated": None}}
    return json.loads(GRAYZONE_DB_PATH.read_text(encoding="utf-8"))


def save_grayzone_db(data: Dict[str, Any]) -> None:
    GRAYZONE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.setdefault("metadata", {})
    data["metadata"]["total_answered"] = len(data.get("answers", {}))
    data["metadata"]["last_updated"]   = datetime.now().isoformat()
    GRAYZONE_DB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def iter_all_sources(catalog: Dict[str, Any]):
    for cat_key, cat_val in catalog.get("categories", {}).items():
        if "sources" in cat_val:
            for src in cat_val["sources"]:
                yield cat_key, src
        if "subcategories" in cat_val:
            for _sub_key, sub_val in cat_val["subcategories"].items():
                if "sources" in sub_val:
                    for src in sub_val["sources"]:
                        yield cat_key, src


def get_dataset_stats() -> Dict[str, Any]:
    stats: Dict[str, Any] = {}
    for fname in ["train.jsonl", "valid.jsonl", "grayzone_finetune.jsonl", "combined_train.jsonl"]:
        p = DATASETS_DIR / fname
        if p.exists():
            with open(p, encoding="utf-8") as f:
                count = sum(1 for l in f if l.strip())
            stats[fname] = {
                "exists": True,
                "entries": count,
                "size_kb": round(p.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            }
        else:
            stats[fname] = {"exists": False, "entries": 0}
    return stats


# ---------------------------------------------------------------------------
# Routes — Catalog
# ---------------------------------------------------------------------------

@admin_router.get("/catalog", summary="Full knowledge source catalog")
async def get_catalog():
    """Return the complete knowledge_catalog.json."""
    catalog = load_catalog()
    if not catalog:
        raise HTTPException(status_code=404, detail="Knowledge catalog not found")
    return JSONResponse(content=catalog)


@admin_router.get("/catalog/summary", summary="Coverage summary by category")
async def get_catalog_summary():
    """Generate a compact summary of catalog coverage status."""
    catalog = load_catalog()
    if not catalog:
        raise HTTPException(status_code=404, detail="Knowledge catalog not found")

    from project.core.source_summarizer import generate_summary_report
    report = generate_summary_report(catalog)

    # Cache to disk
    SUMMARY_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return JSONResponse(content=report)


@admin_router.get("/catalog/source/{source_id}", summary="Get single source details")
async def get_source_detail(source_id: str):
    """Return details for a single source by ID."""
    catalog = load_catalog()
    answers_db = load_grayzone_db()
    answers = answers_db.get("answers", {})

    for cat_key, src in iter_all_sources(catalog):
        if src["id"] == source_id:
            # Attach answered status to each gray-zone question
            enriched_questions = []
            for q in src.get("gray_zone_questions", []):
                key = f"{source_id}::{q}"
                enriched_questions.append({
                    "question": q,
                    "answer_key": key,
                    "answered": key in answers,
                    "answer": answers.get(key, {}).get("answer") if key in answers else None,
                    "confidence": answers.get(key, {}).get("confidence") if key in answers else None,
                })
            result = {**src, "category": cat_key, "gray_zone_questions_enriched": enriched_questions}
            return JSONResponse(content=result)

    raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found in catalog")


# ---------------------------------------------------------------------------
# Routes — Gray-Zone Answers
# ---------------------------------------------------------------------------

@admin_router.get("/grayzone", summary="All gray-zone questions with answer status")
async def get_all_grayzone(
    category:    Optional[str] = Query(None, description="Filter by category key"),
    answered:    Optional[bool] = Query(None, description="Filter by answered status"),
    source_id:   Optional[str] = Query(None, description="Filter by source ID"),
):
    """Return all gray-zone questions with their answer status."""
    catalog    = load_catalog()
    answers_db = load_grayzone_db()
    answers    = answers_db.get("answers", {})

    items: List[Dict[str, Any]] = []

    for cat_key, src in iter_all_sources(catalog):
        if category and cat_key != category:
            continue
        if source_id and src["id"] != source_id:
            continue

        gz_qs = src.get("gray_zone_questions", [])
        for q in gz_qs:
            key = f"{src['id']}::{q}"
            is_answered = key in answers
            if answered is not None and is_answered != answered:
                continue

            ans_data = answers.get(key, {})
            items.append({
                "source_id":     src["id"],
                "source_title":  src.get("title_th", src.get("title", "")),
                "source_domain": src.get("domain", ""),
                "category":      cat_key,
                "coverage_pct":  src.get("coverage_pct", 0),
                "question":      q,
                "answer_key":    key,
                "answered":      is_answered,
                "answer":        ans_data.get("answer") if is_answered else None,
                "confidence":    ans_data.get("confidence") if is_answered else None,
                "reviewer":      ans_data.get("reviewer") if is_answered else None,
                "answered_at":   ans_data.get("answered_at") if is_answered else None,
                "notes":         ans_data.get("notes") if is_answered else None,
            })

    total        = len(items)
    total_ans    = sum(1 for i in items if i["answered"])
    total_not    = total - total_ans

    return JSONResponse(content={
        "total":           total,
        "answered":        total_ans,
        "unanswered":      total_not,
        "completion_pct":  round(total_ans / max(total, 1) * 100, 1),
        "items":           items,
    })


@admin_router.post("/grayzone/answer", summary="Submit answer for a gray-zone question")
async def submit_grayzone_answer(req: GrayzoneAnswerRequest):
    """
    Store an expert answer for a gray-zone question.
    Answer is linked by source_id + question text → used in fine-tuning.
    """
    catalog = load_catalog()

    # Verify source_id exists
    src_found = None
    for _cat_key, src in iter_all_sources(catalog):
        if src["id"] == req.source_id:
            src_found = src
            break

    if not src_found:
        raise HTTPException(status_code=404, detail=f"Source ID '{req.source_id}' not found")

    # Verify question exists in gray_zone_questions (or allow new questions)
    gz_qs = src_found.get("gray_zone_questions", [])
    if req.question not in gz_qs:
        logger.warning(f"Question not in official gray_zone list for {req.source_id} — storing anyway")

    db = load_grayzone_db()
    answer_key = f"{req.source_id}::{req.question}"

    was_update = answer_key in db["answers"]
    db["answers"][answer_key] = {
        "source_id":   req.source_id,
        "question":    req.question,
        "answer":      req.answer,
        "reviewer":    req.reviewer or "admin",
        "confidence":  req.confidence,
        "notes":       req.notes,
        "answered_at": datetime.now().isoformat(),
    }

    save_grayzone_db(db)

    # Sync to Supabase DB if configured
    try:
        from project.core.supabase_db import SupabaseDB
        sdb = SupabaseDB()
        if sdb.is_configured():
            sdb.upsert("qa_knowledge_base", [{
                "question": req.question,
                "answer": req.answer,
                "source_book": f"GrayZone:{req.source_id}",
                "is_verified": True,
                "system_prompt": (
                    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ (Computational Metaphysics) "
                    "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราที่ผ่านการพิสูจน์"
                )
            }])
            logger.info(f"☁️ Synced Gray-Zone answer '{req.source_id}' to Supabase DB `qa_knowledge_base`")
    except Exception as e:
        logger.warning(f"⚠️ Supabase Gray-Zone sync note: {e}")

    return JSONResponse(content={
        "status":     "updated" if was_update else "created",
        "answer_key": answer_key,
        "source_id":  req.source_id,
        "question":   req.question,
        "total_answered": len(db["answers"]),
    })


@admin_router.delete("/grayzone/answer", summary="Delete a gray-zone answer")
async def delete_grayzone_answer(
    source_id: str = Query(..., description="Source ID"),
    question:  str = Query(..., description="Question text"),
):
    """Delete an existing gray-zone answer."""
    db = load_grayzone_db()
    answer_key = f"{source_id}::{question}"

    if answer_key not in db["answers"]:
        raise HTTPException(status_code=404, detail="Answer not found")

    del db["answers"][answer_key]
    save_grayzone_db(db)

    return JSONResponse(content={
        "status": "deleted",
        "answer_key": answer_key,
        "total_answered": len(db["answers"]),
    })


# ---------------------------------------------------------------------------
# Routes — Fine-Tune Pipeline
# ---------------------------------------------------------------------------

@admin_router.get("/finetune/status", summary="Fine-tune dataset statistics")
async def finetune_status():
    """Return statistics for all fine-tune datasets."""
    db    = load_grayzone_db()
    stats = get_dataset_stats()

    return JSONResponse(content={
        "datasets":              stats,
        "grayzone_answered":     db.get("metadata", {}).get("total_answered", 0),
        "last_grayzone_update":  db.get("metadata", {}).get("last_updated"),
        "ready_for_finetune":    stats.get("combined_train.jsonl", {}).get("exists", False),
    })


@admin_router.post("/finetune/export-grayzone", summary="Build JSONL from answered gray-zone Q&A")
async def export_grayzone_finetune():
    """Build grayzone_finetune.jsonl from all answered gray-zone questions."""
    catalog    = load_catalog()
    answers_db = load_grayzone_db()

    from project.core.source_summarizer import build_finetune_from_grayzone
    result = build_finetune_from_grayzone(catalog, answers_db, DATASETS_DIR)

    return JSONResponse(content={
        "status": result["status"],
        "included": result["included"],
        "skipped": result["skipped"],
        "output": result.get("output"),
        "message": (
            f"Exported {result['included']} answered gray-zone Q&A to grayzone_finetune.jsonl"
            if result["status"] == "success"
            else "No answered questions found. Use admin panel to add answers."
        ),
    })


@admin_router.post("/finetune/merge", summary="Merge all datasets into combined_train.jsonl")
async def merge_finetune_datasets():
    """
    Merge train.jsonl + grayzone_finetune.jsonl → combined_train.jsonl.
    This is the master dataset for External AI fine-tuning.
    """
    from project.core.source_summarizer import merge_all_finetune_datasets
    result = merge_all_finetune_datasets(DATASETS_DIR)

    return JSONResponse(content={
        "status": result["status"],
        "total_entries": result.get("total", 0),
        "output": result.get("output"),
        "message": (
            f"Merged {result.get('total', 0)} entries into combined_train.jsonl — ready for fine-tuning"
            if result["status"] == "success"
            else "No entries to merge. Export datasets first."
        ),
    })


@admin_router.post("/finetune/trigger", summary="Trigger external AI fine-tune job")
async def trigger_finetune(req: FinetuneTriggerRequest):
    """
    Trigger fine-tuning on the selected provider.
    Supports: local MLX (Apple Silicon), Ollama, or External API.
    """
    dataset_path = DATASETS_DIR / req.dataset
    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{req.dataset}' not found. Run /admin/finetune/merge first."
        )

    with open(dataset_path, encoding="utf-8") as f:
        entry_count = sum(1 for l in f if l.strip())

    if req.dry_run:
        return JSONResponse(content={
            "status":       "dry_run",
            "provider":     req.provider,
            "model_name":   req.model_name,
            "dataset":      req.dataset,
            "entry_count":  entry_count,
            "max_iterations": req.max_iterations,
            "message":      f"DRY RUN: Would fine-tune {req.model_name} with {entry_count} entries via {req.provider}",
        })

    # Route to provider-specific logic
    if req.provider == "ollama":
        # Local MLX Fine-Tune
        import subprocess, sys
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_mlx_finetune.py"),
            "--dataset", str(dataset_path),
            "--iters", str(req.max_iterations),
        ]
        logger.info(f"🚀 Launching MLX fine-tune: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return JSONResponse(content={
            "status":      "launched",
            "provider":    "ollama/mlx",
            "pid":         proc.pid,
            "command":     " ".join(cmd),
            "entry_count": entry_count,
            "message":     f"MLX fine-tune launched (PID {proc.pid}). Check logs for progress.",
        })

    elif req.provider in ("openai", "together", "gemini"):
        from project.rag.external_finetune import launch_external_finetune
        res = launch_external_finetune(
            provider=req.provider,
            model_name=req.model_name,
            dataset_path=dataset_path,
            max_iterations=req.max_iterations,
        )
        return JSONResponse(content={
            **res,
            "entry_count": entry_count,
            "dataset": req.dataset,
        })

    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")


@admin_router.get("/finetune/download", summary="Download combined fine-tune dataset")
async def download_finetune():
    """Download combined_train.jsonl for external use."""
    path = DATASETS_DIR / "combined_train.jsonl"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="combined_train.jsonl not found. Run /admin/finetune/merge first."
        )
    return FileResponse(
        path=str(path),
        media_type="application/jsonl",
        filename="combined_train.jsonl",
    )


@admin_router.get("/finetune/download-grayzone", summary="Download gray-zone fine-tune dataset")
async def download_grayzone_finetune():
    """Download grayzone_finetune.jsonl."""
    path = DATASETS_DIR / "grayzone_finetune.jsonl"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="grayzone_finetune.jsonl not found. Run /admin/finetune/export-grayzone first."
        )
    return FileResponse(
        path=str(path),
        media_type="application/jsonl",
        filename="grayzone_finetune.jsonl",
    )
