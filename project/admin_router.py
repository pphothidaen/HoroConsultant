"""
project/admin_router.py
========================
Admin Panel API Router for Knowledge Source Management,
Gray-Zone Answer Collection, and Fine-Tune Pipeline Control.

Endpoints:
  GET  /admin/                           -> Admin Dashboard UI
  GET  /admin/catalog                    -> Full knowledge catalog
  GET  /admin/catalog/summary            -> Coverage summary report
  GET  /admin/provider-pools             -> Live AI provider pools, circuit breakers & stats
  GET  /admin/grayzone                   -> All gray-zone questions
  POST /admin/grayzone/answer            -> Submit answer for a gray-zone question
  PUT  /admin/grayzone/answer/{source_id} -> Update existing answer
  DELETE /admin/grayzone/answer/{source_id} -> Delete answer
  GET  /admin/finetune/status            -> Fine-tune dataset statistics
  POST /admin/finetune/export-grayzone   -> Build JSONL from answered gray-zone
  POST /admin/finetune/merge             -> Merge all datasets into combined_train.jsonl
  POST /admin/finetune/trigger           -> Trigger external AI fine-tune job
  GET  /admin/finetune/download          -> Download combined_train.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import time
from base64 import urlsafe_b64decode
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.hashes import SHA256
from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
    reviewer:  str | None = Field(None, description="Reviewer name/identifier")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Confidence score 0–1")
    notes:     str | None = Field(None, description="Optional review notes")


class FinetuneTriggerRequest(BaseModel):
    provider:       str  = Field("ollama", description="Provider: 'ollama', 'openai', 'gemini'")
    model_name:     str  = Field("pphothidaen/qwen2.5-7b-bazi-instruct-4bit", description="Base model name")
    dataset:        str  = Field("combined_train.jsonl", description="Dataset filename in datasets dir")
    dry_run:        bool = Field(False, description="Dry run — validate without launching")
    max_iterations: int  = Field(1000, ge=100, le=10000)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=20, description="Google OAuth ID Token from GIS SDK")


# ---------------------------------------------------------------------------
# Helpers & Auth Verification
# ---------------------------------------------------------------------------

def get_allowed_emails() -> list[str]:
    """Return an explicitly configured allowlist; no production defaults exist."""
    raw = os.getenv("ADMIN_ALLOWED_EMAILS", "")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
_JWKS_CACHE: tuple[float, dict[str, dict[str, Any]]] | None = None


def _token_part(value: str) -> bytes:
    return urlsafe_b64decode(value + "=" * (-len(value) % 4))


async def _google_jwks() -> dict[str, dict[str, Any]]:
    """Get Google signing keys with a short process-local cache."""
    global _JWKS_CACHE
    now = time.monotonic()
    if _JWKS_CACHE and _JWKS_CACHE[0] > now:
        return _JWKS_CACHE[1]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(_GOOGLE_JWKS_URL)
            response.raise_for_status()
        keys = {
            key["kid"]: key
            for key in response.json()["keys"]
            if key.get("kty") == "RSA" and key.get("alg") == "RS256" and key.get("kid")
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Authentication required.") from None
    if not keys:
        raise HTTPException(status_code=401, detail="Authentication required.")
    _JWKS_CACHE = (now + 300.0, keys)
    return keys


async def verify_google_id_token(credential: str) -> dict[str, Any]:
    """Verify a Google GIS ID token's signature and required production claims."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    allowed_emails = get_allowed_emails()
    if not client_id or not allowed_emails:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        header_b64, payload_b64, signature_b64 = credential.split(".")
        header = json.loads(_token_part(header_b64))
        payload = json.loads(_token_part(payload_b64))
        signature = _token_part(signature_b64)
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise ValueError("unsupported token")
        key = (await _google_jwks()).get(header["kid"])
        if not key:
            raise ValueError("unknown key")
        public_key = rsa.RSAPublicNumbers(
            int.from_bytes(_token_part(key["e"]), "big"),
            int.from_bytes(_token_part(key["n"]), "big"),
        ).public_key()
        public_key.verify(
            signature,
            f"{header_b64}.{payload_b64}".encode("ascii"),
            padding.PKCS1v15(),
            SHA256(),
        )
        now = time.time()
        if (payload.get("iss") not in _GOOGLE_ISSUERS
            or payload.get("aud") != client_id
            or not isinstance(payload.get("exp"), (int, float))
            or payload["exp"] <= now
            or not isinstance(payload.get("iat"), (int, float))
            or payload["iat"] > now + 60
            or payload.get("email_verified") not in (True, "true")
            or not isinstance(payload.get("email"), str)):
            raise ValueError("invalid claims")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, Exception) as error:
        if isinstance(error, HTTPException):
            raise
        raise HTTPException(status_code=401, detail="Authentication required.") from None

    email = payload["email"].strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if email not in allowed_emails:
        raise HTTPException(status_code=403, detail="Access denied.")
    return payload


async def require_admin(request: Request) -> None:
    """Protect every Admin data, mutation, download, and review endpoint."""
    if request.url.path in {"/admin/auth/config", "/admin/auth/google"}:
        return
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    await verify_google_id_token(authorization.removeprefix("Bearer ").strip())


admin_router.dependencies.append(Depends(require_admin))


@admin_router.post("/auth/google")
async def verify_google_auth(req: GoogleAuthRequest):
    """Verify a real Google OAuth ID token without exposing allowlist details."""
    payload = await verify_google_id_token(req.credential)
    email = payload["email"].strip().lower()
    return {
        "status": "authenticated",
        "user": {
            "email": email,
            "name": payload.get("name", email.split("@")[0]),
            "picture": payload.get("picture", ""),
            "role": "admin",
            "auth_provider": "google",
        },
    }


@admin_router.get("/auth/config")
async def get_auth_config():
    """Return public Google Auth client configuration."""
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "auth_required": os.getenv("ADMIN_AUTH_REQUIRED", "true").lower() in ("true", "1", "yes"),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_grayzone_db() -> dict[str, Any]:
    if not GRAYZONE_DB_PATH.exists():
        return {"answers": {}, "metadata": {"total_answered": 0, "last_updated": None}}
    return json.loads(GRAYZONE_DB_PATH.read_text(encoding="utf-8"))


def save_grayzone_db(data: dict[str, Any]) -> None:
    GRAYZONE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.setdefault("metadata", {})
    data["metadata"]["total_answered"] = len(data.get("answers", {}))
    data["metadata"]["last_updated"]   = datetime.now().isoformat()
    GRAYZONE_DB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def iter_all_sources(catalog: dict[str, Any]):
    for cat_key, cat_val in catalog.get("categories", {}).items():
        if "sources" in cat_val:
            for src in cat_val["sources"]:
                yield cat_key, src
        if "subcategories" in cat_val:
            for _sub_key, sub_val in cat_val["subcategories"].items():
                if "sources" in sub_val:
                    for src in sub_val["sources"]:
                        yield cat_key, src


def get_dataset_stats() -> dict[str, Any]:
    stats: dict[str, Any] = {}
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
# Routes - Provider Pools & Health
# ---------------------------------------------------------------------------

@admin_router.get("/provider-pools", summary="Live AI provider pools, circuit breakers, and rate limiter stats")
@admin_router.get("/api/admin/provider-pools", summary="Live AI provider pools alias", include_in_schema=False)
@admin_router.get("/api/provider-pools", summary="Live AI provider pools alias", include_in_schema=False)
async def get_provider_pools():
    """
    Return live AI provider pool health, circuit breaker states,
    quota rotation pools, rate limiter metrics, and semantic cache stats.
    """
    from project.core.ai_provider_router import ai_router
    from project.core.rate_limiter import rate_limiter
    from project.core.semantic_cache import semantic_cache

    cb_stats: dict[str, Any] = {}
    for name, cb in ai_router.circuit_breakers.items():
        cb_stats[name] = {
            "name": cb.name,
            "state": cb.state,
            "is_open": cb.is_open(),
            "failure_count": cb.failure_count,
            "cooldown_seconds": cb.cooldown_seconds,
            "last_failure_time": cb.last_failure_time,
        }

    pools_data: dict[str, Any] = {}
    for name, pool in ai_router.provider_pools.items():
        active_proj = pool.get_active_project()
        pools_data[name] = {
            "provider_name": pool.provider_name,
            "billing_mode": pool.billing_mode.value if hasattr(pool.billing_mode, "value") else str(pool.billing_mode),
            "is_available": pool.is_available(),
            "active_project_index": pool.active_project_index,
            "active_project_id": active_proj.project_id if active_proj else None,
            "projects_count": len(pool.projects),
            "projects": [
                {
                    "project_id": p.project_id,
                    "key_count": len(p.api_keys),
                    "active_key_index": p.active_key_index,
                    "is_rate_limited": p.is_rate_limited,
                    "is_available": p.is_available(),
                }
                for p in pool.projects
            ],
        }

    return JSONResponse(
        content={
            "status": "healthy",
            "zero_cost_only": ai_router.zero_cost_only,
            "zero_cost_policy": "ACTIVE" if ai_router.zero_cost_only else "DISABLED",
            "circuit_breakers": cb_stats,
            "provider_pools": pools_data,
            "provider_health": ai_router.get_provider_health(),
            "rate_limiter_stats": rate_limiter.get_stats(),
            "semantic_cache_stats": semantic_cache.get_stats(),
            "timestamp": datetime.now().isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Routes - Catalog
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
    category:    str | None = Query(None, description="Filter by category key"),
    answered:    bool | None = Query(None, description="Filter by answered status"),
    source_id:   str | None = Query(None, description="Filter by source ID"),
):
    """Return all gray-zone questions with their answer status."""
    catalog    = load_catalog()
    answers_db = load_grayzone_db()
    answers    = answers_db.get("answers", {})

    items: list[dict[str, Any]] = []

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
    Supports: local MLX/Ollama, OpenAI, or Google Gemini.
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
        import subprocess
        import sys
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

    elif req.provider in ("openai", "gemini"):
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


@admin_router.get("/code-review", summary="Run pre-deployment code review and safety audit")
async def run_pre_deployment_code_review():
    """Run automated code reviewer & safety audit before pushing to production."""
    from project.core.code_reviewer import CodeReviewer
    reviewer = CodeReviewer()
    report = reviewer.run_full_review()
    return JSONResponse(content=report)
