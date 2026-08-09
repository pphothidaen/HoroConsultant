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
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("hitl_router")

ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH     = ROOT / "project" / "data" / "knowledge_catalog.json"
GRAYZONE_DB_PATH = ROOT / "project" / "data" / "grayzone_answers.json"
HITL_DB_PATH     = ROOT / "project" / "data" / "hitl_reviews.json"
HITL_EXPORT_PATH = ROOT / "project" / "rag" / "datasets" / "hitl_approved.jsonl"
DATASETS_DIR     = ROOT / "project" / "rag" / "datasets"

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
        return {"reviews": {}, "drafts": {}, "stats": {"approved": 0, "edited": 0, "rejected": 0, "pending": 0}}
    return json.loads(HITL_DB_PATH.read_text(encoding="utf-8"))


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

    return JSONResponse(content={
        "total":    total,
        "pending":  pending,
        "approved": approved,
        "edited":   edited,
        "rejected": rejected,
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
async def submit_review(item_id: str, req: ReviewDecision):
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
        "source_title":     item["source_title"],
        "category":         item["category"],
        "question":         item["question"],
        "decision":         req.decision,
        "final_answer":     final_answer,
        "tags":             req.tags or [],
        "reject_reason":    req.reject_reason,
        "confidence_rating": req.confidence_rating,
        "reviewer":         req.reviewer or "human",
        "notes":            req.notes,
        "reviewed_at":      datetime.now().isoformat(),
    }

    save_hitl_db(hitl_db)

    # Auto-sync approved/edited to grayzone_answers.json
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
        "last_updated":    hitl_db.get("last_updated"),
    })


@hitl_router.get("/export", summary="Export HITL-approved JSONL")
async def export_hitl_jsonl(download: bool = Query(False)):
    hitl_db = load_hitl_db()
    reviews = hitl_db.get("reviews", {})
    entries = []

    for r in reviews.values():
        if r.get("decision") not in (DECISION_APPROVE, DECISION_EDIT):
            continue
        answer = r.get("final_answer", "")
        if not answer:
            continue
        system_prompt = SYSTEM_PROMPT_MAP.get(r.get("category", ""), DEFAULT_SYSTEM)
        entries.append({
            "messages": [
                {"role": "system",    "content": system_prompt},
                {"role": "user",      "content": r["question"]},
                {"role": "assistant", "content": answer},
            ]
        })

    HITL_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HITL_EXPORT_PATH, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)

    if download:
        return FileResponse(
            path=str(HITL_EXPORT_PATH),
            media_type="application/jsonl",
            filename="hitl_approved.jsonl",
        )

    return JSONResponse(content={
        "status":  "exported",
        "entries": len(entries),
        "output":  str(HITL_EXPORT_PATH),
    })


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
