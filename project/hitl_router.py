"""
project/hitl_router.py
=======================
Human-in-the-Loop (HITL) API Router.

Manages the full HITL workflow:
  1. Queue gray-zone questions for human review
  2. Generate AI draft answers (via HybridRouter / Gemini)
  3. Accept human corrections + confidence tags
  4. Export HITL-approved pairs as Fine-Tune JSONL

Endpoints:
  GET  /hitl/queue                  → List items pending human review
  GET  /hitl/item/{item_id}         → Get single review item
  POST /hitl/draft/{item_id}        → Generate AI draft answer for an item
  POST /hitl/review/{item_id}       → Submit human decision (approve/edit/reject)
  GET  /hitl/stats                  → Review session statistics
  GET  /hitl/export                 → Export HITL-approved JSONL
  POST /hitl/batch-draft            → Generate AI drafts for all pending items
  DELETE /hitl/review/{item_id}     → Undo a review decision
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from project.core.model_activation import get_active_model_state
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

logger = logging.getLogger("hitl_router")

ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH     = ROOT / "project" / "data" / "knowledge_catalog.json"
GRAYZONE_DB_PATH = ROOT / "project" / "data" / "grayzone_answers.json"
HITL_DB_PATH     = ROOT / "project" / "data" / "hitl_reviews.json"
HITL_EXPORT_PATH = ROOT / "project" / "rag" / "datasets" / "hitl_approved.jsonl"
HITL_EXPORT_WITH_META_PATH = ROOT / "project" / "rag" / "datasets" / "hitl_approved_with_metadata.jsonl"
DATASETS_DIR     = ROOT / "project" / "rag" / "datasets"
HITL_EXTERNAL_ITEMS_KEY = "external_items"
HITL_AUTOTRAIN_THRESHOLD = max(1, int(os.getenv("HITL_AUTOTRAIN_TRIGGER_THRESHOLD", os.getenv("HITL_FINETUNE_TRIGGER_THRESHOLD", "50"))))
HITL_AUTOTRAIN_STEP = max(1, int(os.getenv("HITL_AUTOTRAIN_TRIGGER_STEP", str(HITL_AUTOTRAIN_THRESHOLD))))
HITL_AUTOTRAIN_DRY_RUN = os.getenv("HITL_AUTOTRAIN_DRY_RUN", "false").lower() == "true"
HITL_AUTOTRAIN_ENABLED = os.getenv("HITL_AUTOTRAIN_ENABLED", "true").lower() != "false"

SYSTEM_PROMPT_MAP = {
    "chinese_metaphysics": (
        "คุณคือผู้เชี่ยวชาญด้านอภิปรัชญาเชิงคำนวณ (Computational Metaphysics) "
        "เชี่ยวชาญทั้ง BaZi (四柱命理), ปรัชญาจีน, คัมภีร์โบราณ อาทิ 子平真詮, 滴天髓, 窮通寶鑑 "
        "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราที่ผ่านการพิสูจน์"
    ),
    "vedic_astrology": (
        "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เวท (Jyotish Shastra) "
        "เชี่ยวชาญใน BPHS, Jaimini Sutras, Phaladeepika, Saravali, Brihat Jataka "
        "ตอบด้วยภาษาวิชาการ อ้างอิงบทและข้อของตำราต้นฉบับ"
    ),
    "thai_astrology": (
        "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์ไทยและตำราโบราณ "
        "เชี่ยวชาญในคัมภีร์สุริยยาตร์, มานัต, โหราศาสตร์ไทยมาตรฐาน, โหงวเฮ้ง "
        "ตอบด้วยความเคารพต่อวัฒนธรรม อธิบายเชิงประวัติศาสตร์และการประยุกต์ใช้"
    ),
    "astrophysics_math": (
        "คุณคือผู้เชี่ยวชาญด้านดาราศาสตร์ฟิสิกส์เชิงคำนวณ "
        "เชี่ยวชาญใน Swiss Ephemeris, JPL DE440, ICRF3, IAU 2006, IERS, NARDL Model "
        "ตอบด้วยความถูกต้องทางวิทยาศาสตร์ แสดงสูตรคณิตศาสตร์และ Margin of Error ±σ"
    ),
    "western_scientific": (
        "คุณคือผู้เชี่ยวชาญด้านทฤษฎีโหราศาสตร์ตะวันตกและการวิพากษ์เชิงวิทยาศาสตร์ "
        "เชี่ยวชาญใน Hellenistic Astrology, Gauquelin Mars Effect, Genovese (2014) "
        "ตอบด้วยมุมมองที่สมดุลระหว่างประเพณีกับหลักฐานเชิงประจักษ์"
    ),
}

DEFAULT_SYSTEM = (
    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ เชี่ยวชาญทั้ง BaZi, Vedic, "
    "โหราศาสตร์ไทย และดาราศาสตร์ฟิสิกส์ ตอบด้วยการวิเคราะห์เชิงวิชาการ"
)

# Decision types
DECISION_APPROVE  = "approve"
DECISION_EDIT     = "edit"
DECISION_REJECT   = "reject"

# Tag categories
TAG_CORRECT        = "correct"
TAG_NEEDS_REWRITE  = "needs_rewrite"
TAG_FACTUALLY_WRONG = "factually_wrong"
TAG_HALLUCINATION  = "hallucination"
TAG_BAD_TONE       = "bad_tone"
TAG_INCOMPLETE     = "incomplete"
TAG_EXCELLENT      = "excellent"

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

hitl_router = APIRouter(prefix="/hitl", tags=["HITL — Human-in-the-Loop Review"])


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ReviewDecision(BaseModel):
    decision:          str   = Field(..., description="'approve' | 'edit' | 'reject'")
    human_answer:      str | None = Field(None, description="Human-corrected answer (for edit/approve)")
    tags:              list[str] | None = Field(None, description="Tag list from TAG_* constants")
    reject_reason:     str | None = Field(None, description="Reason for rejection")
    confidence_rating: int | None = Field(None, ge=1, le=5, description="Human confidence 1-5 stars")
    reviewer:          str | None = Field(None, description="Reviewer name")
    notes:             str | None = Field(None, description="Additional reviewer notes")


class BatchDraftRequest(BaseModel):
    limit:             int   = Field(20, ge=1, le=100, description="Max items to draft")
    category_filter:   str | None = Field(None, description="Limit to one category")
    force_regenerate:  bool  = Field(False, description="Regenerate even if draft exists")


# ---------------------------------------------------------------------------
# DB Helpers
# ---------------------------------------------------------------------------

def load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_hitl_db() -> dict[str, Any]:
    if not HITL_DB_PATH.exists():
        return _ensure_hitl_automation_defaults({
            "reviews": {},
            "drafts": {},
            HITL_EXTERNAL_ITEMS_KEY: {},
            "stats": {"approved": 0, "edited": 0, "rejected": 0, "pending": 0},
        })
    data = json.loads(HITL_DB_PATH.read_text(encoding="utf-8"))
    return _ensure_hitl_automation_defaults(data)


def save_hitl_db(data: dict[str, Any]) -> None:
    HITL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    reviews = data.get("reviews", {})
    data["stats"] = {
        "approved":  sum(1 for r in reviews.values() if r.get("decision") == DECISION_APPROVE),
        "edited":    sum(1 for r in reviews.values() if r.get("decision") == DECISION_EDIT),
        "rejected":  sum(1 for r in reviews.values() if r.get("decision") == DECISION_REJECT),
        "total_reviewed": len(reviews),
    }
    data["last_updated"] = datetime.now().isoformat()
    HITL_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ensure_hitl_automation_defaults(hitl_db: dict[str, Any]) -> dict[str, Any]:
    automation = hitl_db.setdefault("automation", {})
    automation.setdefault("threshold", HITL_AUTOTRAIN_THRESHOLD)
    automation.setdefault("step", HITL_AUTOTRAIN_STEP)
    automation.setdefault("next_trigger_count", automation.get("threshold", HITL_AUTOTRAIN_THRESHOLD))
    automation.setdefault("last_trigger_count", 0)
    automation.setdefault("total_triggers", 0)
    automation.setdefault("last_triggered_at", None)
    automation.setdefault("trigger_history", [])
    return hitl_db


def _approved_hitl_count(reviews: dict[str, Any]) -> int:
    return sum(
        1 for r in reviews.values()
        if r.get("decision") in (DECISION_APPROVE, DECISION_EDIT) and (r.get("final_answer") or "").strip()
    )


def _normalize_hitl_payload(item_id: str, review: dict[str, Any]) -> dict[str, Any] | None:
    question = (review.get("question") or "").strip()
    final_answer = (review.get("final_answer") or "").strip()
    if not question or not final_answer:
        return None

    category = review.get("category", "")
    system_prompt = SYSTEM_PROMPT_MAP.get(category, DEFAULT_SYSTEM)
    reviewed_at = review.get("reviewed_at") or datetime.now().isoformat()

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
            {"role": "assistant", "content": final_answer},
        ],
        "_meta": {
            "item_id": item_id,
            "source_domain": review.get("source_domain", ""),
            "source_id": review.get("source_id", ""),
            "source_title": review.get("source_title", ""),
            "category": category,
            "question": question,
            "required_human_review": review.get("required_human_review", False),
            "conflict_detected": review.get("conflict_detected", False),
            "conflicting_domains": review.get("conflicting_domains", []),
            "consensus_score": review.get("consensus_score"),
            "hitl_routing": review.get("hitl_routing"),
            "decision": review.get("decision"),
            "reviewer": review.get("reviewer"),
            "confidence_rating": review.get("confidence_rating"),
            "tags": review.get("tags", []),
            "notes": review.get("notes"),
            "reviewed_at": reviewed_at,
            "pipeline": "hitl_router",
        },
    }


def _collect_hitl_export_records(hitl_db: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, review in hitl_db.get("reviews", {}).items():
        payload = _normalize_hitl_payload(item_id, review)
        if payload:
            records.append(payload)
    records.sort(key=lambda r: r["_meta"].get("reviewed_at") or "")
    return records


def make_external_item_id(source_domain: str, source_id: str, question: str) -> str:
    import hashlib
    raw = f"{source_domain}::{source_id}::{question}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def upsert_external_hitl_item(
    item: dict[str, Any],
) -> str:
    hitl_db = load_hitl_db()
    hitl_db.setdefault(HITL_EXTERNAL_ITEMS_KEY, {})
    question = str(item.get("question", "")).strip()
    source_domain = str(item.get("source_domain", "metaphysical-domain-engine")).strip()
    source_id = str(item.get("source_id", source_domain)).strip() or source_domain
    item_id = str(item.get("item_id") or make_external_item_id(source_domain, source_id, question)).strip()
    now = datetime.now().isoformat()

    if not question:
        question = "Metaphysical deliberation review item"

    existing = hitl_db[HITL_EXTERNAL_ITEMS_KEY].get(item_id, {})
    payload = {
        "item_id": item_id,
        "source_domain": source_domain,
        "source_id": source_id,
        "source_title": item.get("source_title", "Metaphysical Domain Engine"),
        "category": item.get("category", "metaphysical_debate"),
        "question": question,
        "required_human_review": bool(item.get("required_human_review", True)),
        "conflict_detected": bool(item.get("conflict_detected", False)),
        "conflicting_domains": item.get("conflicting_domains", []),
        "consensus_score": item.get("consensus_score"),
        "hitl_routing": item.get("hitl_routing", {}),
        "synthesis_snapshot": item.get("synthesis_snapshot", {}),
        "notes": item.get("notes"),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "status": existing.get("status", "pending"),
        "review": existing.get("review"),
    }
    hitl_db[HITL_EXTERNAL_ITEMS_KEY][item_id] = payload
    save_hitl_db(hitl_db)
    return item_id


def _write_hitl_exports(records: list[dict[str, Any]], *, append: bool = False) -> dict[str, Any]:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(HITL_EXPORT_PATH, mode, encoding="utf-8") as f_messages, open(
        HITL_EXPORT_WITH_META_PATH, mode, encoding="utf-8"
    ) as f_metadata:
        for entry in records:
            f_messages.write(json.dumps({"messages": entry["messages"]}, ensure_ascii=False) + "\n")
            f_metadata.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {
        "status": "success",
        "entries": len(records),
        "output": str(HITL_EXPORT_PATH),
        "metadata_output": str(HITL_EXPORT_WITH_META_PATH),
    }


def _run_finetune_trigger(
    force: bool,
    dry_run: bool = False,
    requested_by: str = "system",
) -> dict[str, Any]:
    if not HITL_AUTOTRAIN_ENABLED and not force:
        return {
            "status": "skipped",
            "reason": "autotrain_disabled",
            "requested_by": requested_by,
        }

    hitl_db = load_hitl_db()
    automation = _ensure_hitl_automation_defaults(hitl_db)
    reviews = hitl_db.get("reviews", {})
    approved_count = _approved_hitl_count(reviews)
    next_threshold = automation.get("next_trigger_count", automation.get("threshold", HITL_AUTOTRAIN_THRESHOLD))
    records = _collect_hitl_export_records(hitl_db)

    if not records:
        return {
            "status": "skipped",
            "reason": "no_approved_or_edited_pairs",
            "approved_count": approved_count,
            "requested_by": requested_by,
        }

    _write_hitl_exports(records, append=False)

    if not force and approved_count < next_threshold:
        return {
            "status": "skipped",
            "reason": "threshold_not_reached",
            "approved_count": approved_count,
            "next_trigger_count": next_threshold,
            "requested_by": requested_by,
        }

    active_model = get_active_model_state().get("active_model")
    orchestrator = FineTuneOrchestrator(target_model=active_model)
    training = orchestrator.trigger_kaggle_training(
        dataset_path=str(HITL_EXPORT_PATH),
        dry_run=dry_run or HITL_AUTOTRAIN_DRY_RUN,
    )
    status = training.get("status", "FAILED")
    trigger_ok = status in {"RUNNING", "QUEUED (DRY-RUN)"}

    if trigger_ok:
        now_iso = datetime.now().isoformat()
        step = max(1, automation.get("step", HITL_AUTOTRAIN_STEP))
        automation["last_triggered_at"] = now_iso
        automation["last_trigger_count"] = approved_count
        automation["next_trigger_count"] = approved_count + step
        automation["total_triggers"] = automation.get("total_triggers", 0) + 1
        automation.setdefault("trigger_history", [])
        automation["trigger_history"].insert(
            0,
            {
                "approved_count": approved_count,
                "requested_by": requested_by,
                "status": status,
                "timestamp": now_iso,
                "dataset": str(HITL_EXPORT_PATH),
                "target_model": training.get("target_model"),
            },
        )
        automation["trigger_history"] = automation["trigger_history"][:20]
        save_hitl_db(hitl_db)

    return {
        "status": status,
        "requested_by": requested_by,
        "approved_count": approved_count,
        "next_trigger_count": automation.get("next_trigger_count", next_threshold),
        "training": training,
        "reason": None if trigger_ok else training.get("error") or training.get("status"),
    }


def iter_all_sources(catalog: dict[str, Any]):
    for cat_key, cat_val in catalog.get("categories", {}).items():
        if "sources" in cat_val:
            for src in cat_val["sources"]:
                yield cat_key, src
        if "subcategories" in cat_val:
            for sub_val in cat_val["subcategories"].values():
                if "sources" in sub_val:
                    for src in sub_val["sources"]:
                        yield cat_key, src


def make_item_id(source_id: str, question: str) -> str:
    import hashlib
    raw = f"{source_id}::{question}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def build_queue_items(
    catalog: dict[str, Any],
    hitl_db: dict[str, Any],
    category_filter: str | None = None,
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    reviews = hitl_db.get("reviews", {})
    drafts  = hitl_db.get("drafts", {})
    items   = []

    for cat_key, src in iter_all_sources(catalog):
        if category_filter and cat_key != category_filter:
            continue
        gz_qs = src.get("gray_zone_questions", [])
        for q in gz_qs:
            item_id = make_item_id(src["id"], q)
            review  = reviews.get(item_id, {})
            draft   = drafts.get(item_id, {})
            status  = review.get("decision", "pending") if review else "pending"

            if status_filter and status != status_filter:
                continue

            items.append({
                "item_id":       item_id,
                "source_id":     src["id"],
                "source_title":  src.get("title_th", src.get("title", "")),
                "source_domain": src.get("domain", ""),
                "category":      cat_key,
                "coverage_pct":  src.get("coverage_pct", 0),
                "question":      q,
                "status":        status,
                "has_draft":     bool(draft),
                "ai_draft":      draft.get("answer") if draft else None,
                "ai_confidence": draft.get("confidence_scores") if draft else None,
                "review":        review if review else None,
                "reviewed_at":   review.get("reviewed_at") if review else None,
                "required_human_review": False,
                "conflict_detected": False,
                "conflicting_domains": [],
                "consensus_score": None,
                "hitl_routing": None,
            })

    for ext_item_id, ext_item in hitl_db.get(HITL_EXTERNAL_ITEMS_KEY, {}).items():
        review = reviews.get(ext_item_id, {})
        draft = drafts.get(ext_item_id, {})
        status = review.get("decision", "pending") if review else ext_item.get("status", "pending")
        if category_filter and ext_item.get("category") != category_filter:
            continue

        if status_filter and status != status_filter:
            continue

        items.append({
            "item_id":       ext_item_id,
            "source_id":     ext_item.get("source_id", "metaphysical-domain-engine"),
            "source_title":  ext_item.get("source_title", "Metaphysical Domain Engine"),
            "source_domain":  ext_item.get("source_domain", "metaphysical-domain-engine"),
            "category":      ext_item.get("category", "metaphysical_debate"),
            "coverage_pct":  ext_item.get("coverage_pct", 0),
            "question":      ext_item.get("question", ""),
            "status":        status,
            "has_draft":     bool(draft),
            "ai_draft":      draft.get("answer") if draft else None,
            "ai_confidence": draft.get("confidence_scores") if draft else None,
            "review":        review if review else ext_item.get("review"),
            "reviewed_at":   review.get("reviewed_at") if review else ext_item.get("reviewed_at"),
            "required_human_review": bool(ext_item.get("required_human_review", True)),
            "conflict_detected": bool(ext_item.get("conflict_detected", False)),
            "conflicting_domains": ext_item.get("conflicting_domains", []),
            "consensus_score": ext_item.get("consensus_score"),
            "hitl_routing": ext_item.get("hitl_routing"),
        })

    return items


# ---------------------------------------------------------------------------
# AI Draft Generator
# ---------------------------------------------------------------------------

async def generate_ai_draft(
    question: str,
    system_prompt: str,
    source_title: str,
) -> dict[str, Any]:
    """Generate an AI draft answer via HybridRouter."""
    try:
        from project.api_router import HybridRouter
        router = HybridRouter()

        prompt = (
            f"แหล่งข้อมูล: {source_title}\n\n"
            f"คำถาม: {question}\n\n"
            f"โปรดตอบด้วยความถูกต้องทางวิชาการ ครบถ้วน และอ้างอิงตำราหรือแหล่งข้อมูลที่เกี่ยวข้อง"
        )

        result = router.generate(prompt=prompt, system_instruction=system_prompt)
        answer = result.get("text", "")
        model  = result.get("model_used", "unknown")

        # Simulate confidence scores per sentence
        sentences = [s.strip() for s in answer.split(".") if s.strip()]
        import random
        random.seed(hash(question) % 10000)
        confidence_scores = []
        for sent in sentences:
            # Heuristic: shorter sentences and those with hedging words get lower confidence
            base_conf = 0.75
            if any(w in sent.lower() for w in ["อาจ", "น่าจะ", "ประมาณ", "maybe", "possibly", "around"]):
                base_conf -= 0.2
            if len(sent) < 30:
                base_conf -= 0.1
            if any(w in sent for w in ["ตาม", "อ้างอิง", "คัมภีร์", "ตำรา", "หลักการ"]):
                base_conf += 0.1
            score = max(0.3, min(1.0, base_conf + random.uniform(-0.1, 0.1)))
            confidence_scores.append({
                "text":       sent + ".",
                "confidence": round(score, 2),
            })

        return {
            "answer":            answer,
            "model_used":        model,
            "confidence_scores": confidence_scores,
            "latency_ms":        result.get("latency_ms", 0),
            "generated_at":      datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"AI draft generation failed: {e}")
        return {
            "answer":            "",
            "error":             str(e),
            "confidence_scores": [],
            "generated_at":      datetime.now().isoformat(),
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@hitl_router.get("/queue", summary="List items pending human review")
async def get_review_queue(
    status:   str | None = Query(None, description="Filter: pending|approve|edit|reject"),
    category: str | None = Query(None, description="Filter by category key"),
    limit:    int = Query(50, ge=1, le=200),
    offset:   int = Query(0, ge=0),
):
    catalog  = load_catalog()
    hitl_db  = load_hitl_db()
    items    = build_queue_items(catalog, hitl_db, category, status)
    total    = len(items)
    paged    = items[offset: offset + limit]

    pending  = sum(1 for i in items if i["status"] == "pending")
    approved = sum(1 for i in items if i["status"] == DECISION_APPROVE)
    edited   = sum(1 for i in items if i["status"] == DECISION_EDIT)
    rejected = sum(1 for i in items if i["status"] == DECISION_REJECT)
    pending_required_hitl = sum(
        1 for i in items if i["status"] == "pending" and i.get("required_human_review", False)
    )
    pending_conflicts = sum(
        1 for i in items if i["status"] == "pending" and (
            bool(i.get("conflict_detected", False)) or bool(i.get("required_human_review", False))
        )
    )
    automation = hitl_db.get("automation", {})
    conflict_domains = sorted({
        dom
        for i in items
        for dom in i.get("conflicting_domains", []) or []
        if isinstance(dom, str)
    })

    return JSONResponse(content={
        "total":    total,
        "pending":  pending,
        "approved": approved,
        "edited":   edited,
        "rejected": rejected,
        "automation": {
            "approved_count": _approved_hitl_count(hitl_db.get("reviews", {})),
            "next_trigger_count": automation.get("next_trigger_count", HITL_AUTOTRAIN_THRESHOLD),
            "threshold": automation.get("threshold", HITL_AUTOTRAIN_THRESHOLD),
            "last_trigger_count": automation.get("last_trigger_count", 0),
            "total_triggers": automation.get("total_triggers", 0),
        },
        "hitl_summary": {
            "pending_required_human_review": pending_required_hitl,
            "pending_conflict_items": pending_conflicts,
            "conflict_domains": conflict_domains,
        },
        "offset":   offset,
        "limit":    limit,
        "items":    paged,
    })


@hitl_router.get("/item/{item_id}", summary="Get single review item detail")
async def get_item(item_id: str):
    catalog = load_catalog()
    hitl_db = load_hitl_db()
    items   = build_queue_items(catalog, hitl_db)
    item    = next((i for i in items if i["item_id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    return JSONResponse(content=item)


@hitl_router.post("/draft/{item_id}", summary="Generate AI draft answer for an item")
async def generate_draft(item_id: str, background_tasks: BackgroundTasks):
    catalog = load_catalog()
    hitl_db = load_hitl_db()
    items   = build_queue_items(catalog, hitl_db)
    item    = next((i for i in items if i["item_id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")

    system_prompt = SYSTEM_PROMPT_MAP.get(item["category"], DEFAULT_SYSTEM)
    draft = await generate_ai_draft(item["question"], system_prompt, item["source_title"])

    hitl_db.setdefault("drafts", {})[item_id] = draft
    save_hitl_db(hitl_db)

    return JSONResponse(content={
        "item_id":  item_id,
        "question": item["question"],
        "draft":    draft,
    })


@hitl_router.post("/review/{item_id}", summary="Submit human review decision")
async def submit_review(
    item_id: str,
    req: ReviewDecision,
    background_tasks: BackgroundTasks,
):
    catalog = load_catalog()
    hitl_db = load_hitl_db()
    items   = build_queue_items(catalog, hitl_db)
    item    = next((i for i in items if i["item_id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")

    if req.decision not in (DECISION_APPROVE, DECISION_EDIT, DECISION_REJECT):
        raise HTTPException(status_code=400, detail=f"Invalid decision '{req.decision}'")

    # Determine final answer
    if req.decision == DECISION_REJECT:
        final_answer = None
    elif req.decision == DECISION_EDIT and req.human_answer:
        final_answer = req.human_answer
    elif req.decision == DECISION_APPROVE:
        draft = hitl_db.get("drafts", {}).get(item_id, {})
        final_answer = req.human_answer or draft.get("answer", "")
    else:
        final_answer = req.human_answer or ""

    hitl_db.setdefault("reviews", {})[item_id] = {
        "item_id":          item_id,
        "source_id":        item["source_id"],
        "source_domain":    item.get("source_domain"),
        "source_title":     item["source_title"],
        "category":         item["category"],
        "question":         item["question"],
        "decision":         req.decision,
        "final_answer":     final_answer,
        "required_human_review": item.get("required_human_review"),
        "conflict_detected": bool(item.get("conflict_detected", False)),
        "conflicting_domains": item.get("conflicting_domains", []),
        "consensus_score": item.get("consensus_score"),
        "hitl_routing": item.get("hitl_routing"),
        "tags":             req.tags or [],
        "reject_reason":    req.reject_reason,
        "confidence_rating": req.confidence_rating,
        "reviewer":         req.reviewer or "human",
        "notes":            req.notes,
        "reviewed_at":      datetime.now().isoformat(),
    }

    save_hitl_db(hitl_db)

    # Auto-sync approved/edited to grayzone_answers.json & Instant FAISS Ingest (Decision 6)
    if req.decision in (DECISION_APPROVE, DECISION_EDIT) and final_answer:
        from project.admin_router import load_grayzone_db, save_grayzone_db
        gz_db = load_grayzone_db()
        answer_key = f"{item['source_id']}::{item['question']}"
        gz_db.setdefault("answers", {})[answer_key] = {
            "source_id":   item["source_id"],
            "question":    item["question"],
            "answer":      final_answer,
            "reviewer":    req.reviewer or "human-hitl",
            "confidence":  (req.confidence_rating or 3) / 5.0,
            "notes":       f"HITL reviewed: {req.decision}" + (f" | Tags: {req.tags}" if req.tags else ""),
            "answered_at": datetime.now().isoformat(),
        }
        save_grayzone_db(gz_db)

        # 1. Append to HITL approved JSONL dataset + metadata dataset
        try:
            records = []
            payload = _normalize_hitl_payload(item_id, {
                "item_id": item_id,
                "source_id": item["source_id"],
                "source_domain": item.get("source_domain"),
                "source_title": item["source_title"],
                "category": item["category"],
                "question": item["question"],
                "decision": req.decision,
                "final_answer": final_answer,
                "required_human_review": item.get("required_human_review"),
                "conflict_detected": bool(item.get("conflict_detected", False)),
                "conflicting_domains": item.get("conflicting_domains", []),
                "consensus_score": item.get("consensus_score"),
                "hitl_routing": item.get("hitl_routing"),
                "synthesis_snapshot": item.get("synthesis_snapshot"),
                "reviewer": req.reviewer or "human",
                "confidence_rating": req.confidence_rating,
                "tags": req.tags or [],
                "notes": f"HITL reviewed: {req.decision}" + (f" | Tags: {req.tags}" if req.tags else ""),
                "reviewed_at": datetime.now().isoformat(),
            })
            if payload:
                records.append(payload)
            _write_hitl_exports(records, append=True)
            logger.info(f"[HITL] Appended approved item {item_id} to {HITL_EXPORT_PATH}")
        except Exception as e:
            logger.warning(f"[HITL] Failed to append to approved dataset: {e}")

        # 2. Instant FAISS Vector Store Ingest (Decision 6)
        try:
            from project.rag.vector_store import VectorStore
            vs = VectorStore.load()
            new_chunk = {
                "text": f"Q: {item['question']}\nA: {final_answer}",
                "source": f"hitl_{item_id}",
                "category": item["category"],
            }
            if hasattr(vs, "_chunks"):
                vs._chunks.append(new_chunk)
                vs.save()
                logger.info(f"[HITL:RAG] Instant vector ingest completed for item {item_id}")
        except Exception as e:
            logger.debug(f"[HITL:RAG] Vector store instant ingest note: {e}")

        # 3. Schedule auto-finetraining when milestone is reached
        background_tasks.add_task(_run_finetune_trigger, False, False, f"review:{item_id}")

    return JSONResponse(content={
        "status":      "saved",
        "item_id":     item_id,
        "decision":    req.decision,
        "tags":        req.tags or [],
        "final_answer": final_answer[:200] + "..." if final_answer and len(final_answer) > 200 else final_answer,
    })


@hitl_router.delete("/review/{item_id}", summary="Undo a review decision")
async def undo_review(item_id: str):
    hitl_db = load_hitl_db()
    if item_id not in hitl_db.get("reviews", {}):
        raise HTTPException(status_code=404, detail="Review not found")
    del hitl_db["reviews"][item_id]
    save_hitl_db(hitl_db)
    return JSONResponse(content={"status": "undone", "item_id": item_id})


@hitl_router.get("/stats", summary="Review session statistics")
async def get_stats():
    catalog = load_catalog()
    hitl_db = load_hitl_db()
    items   = build_queue_items(catalog, hitl_db)
    reviews = hitl_db.get("reviews", {})
    automation = hitl_db.get("automation", {})

    # Tag breakdown
    tag_counts: dict[str, int] = {}
    for r in reviews.values():
        for t in r.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1

    # Category breakdown
    cat_stats: dict[str, dict] = {}
    for item in items:
        cat = item["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "approved": 0, "edited": 0, "rejected": 0, "pending": 0}
        cat_stats[cat]["total"] += 1
        cat_stats[cat][item["status"]] += 1

    return JSONResponse(content={
        "overall": {
            "total":    len(items),
            "pending":  sum(1 for i in items if i["status"] == "pending"),
            "approved": sum(1 for i in items if i["status"] == DECISION_APPROVE),
            "edited":   sum(1 for i in items if i["status"] == DECISION_EDIT),
            "rejected": sum(1 for i in items if i["status"] == DECISION_REJECT),
            "completion_pct": round(len(reviews) / max(len(items), 1) * 100, 1),
        },
        "tag_counts":      tag_counts,
        "by_category":     cat_stats,
        "automation": {
            "approved_count": _approved_hitl_count(reviews),
            "next_trigger_count": automation.get("next_trigger_count", HITL_AUTOTRAIN_THRESHOLD),
            "total_triggers": automation.get("total_triggers", 0),
            "last_triggered_at": automation.get("last_triggered_at"),
            "last_trigger_count": automation.get("last_trigger_count", 0),
            "trigger_history": automation.get("trigger_history", [])[:5],
        },
        "last_updated":    hitl_db.get("last_updated"),
    })


@hitl_router.get("/export", summary="Export HITL-approved JSONL")
async def export_hitl_jsonl(download: bool = Query(False)):
    hitl_db = load_hitl_db()
    entries = _collect_hitl_export_records(hitl_db)
    result = _write_hitl_exports(entries, append=False)

    if download:
        return FileResponse(
            path=str(HITL_EXPORT_PATH),
            media_type="application/jsonl",
            filename="hitl_approved.jsonl",
        )

    return JSONResponse(content={
        "status":         "exported",
        "entries":        len(entries),
        "output":         result["output"],
        "metadata_output": result["metadata_output"],
        "approved_count":  _approved_hitl_count(hitl_db.get("reviews", {})),
    })


@hitl_router.post("/trigger", summary="Trigger Fine-tuning from HITL-approved pairs")
async def trigger_finetune(
    force: bool = Query(False, description="Force trigger even before threshold"),
    dry_run: bool = Query(False, description="Run dry-run only (no external platform call)"),
):
    result = _run_finetune_trigger(force=force, dry_run=dry_run, requested_by="api/manual")
    if result.get("status") == "skipped":
        return JSONResponse(status_code=200, content=result)
    return JSONResponse(content=result)


@hitl_router.post("/batch-draft", summary="Generate AI drafts for multiple pending items")
async def batch_draft(req: BatchDraftRequest, background_tasks: BackgroundTasks):
    catalog = load_catalog()
    hitl_db = load_hitl_db()
    items   = build_queue_items(catalog, hitl_db, req.category_filter, "pending")

    if not req.force_regenerate:
        items = [i for i in items if not i.get("has_draft")]

    items = items[:req.limit]

    if not items:
        return JSONResponse(content={"status": "nothing_to_draft", "queued": 0})

    async def run_drafts():
        for item in items:
            system_prompt = SYSTEM_PROMPT_MAP.get(item["category"], DEFAULT_SYSTEM)
            draft = await generate_ai_draft(item["question"], system_prompt, item["source_title"])
            db = load_hitl_db()
            db.setdefault("drafts", {})[item["item_id"]] = draft
            save_hitl_db(db)

    background_tasks.add_task(run_drafts)

    return JSONResponse(content={
        "status": "queued",
        "queued": len(items),
        "items":  [i["item_id"] for i in items],
        "message": f"Generating AI drafts for {len(items)} items in background...",
    })
