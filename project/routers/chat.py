"""
project/routers/chat.py
=======================
FastAPI Router for Metaphysics AI Live Consultant Chat Assistant.
Provides SSE streaming (/api/v2/chat/stream), Synchronous Consultation (/api/v2/chat/consult),
Dynamic Prompt Pills (/api/v2/chat/prompt-pills), and Anonymized Feedback (/api/v2/chat/anonymized-feedback).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from project.core.chat_assistant_engine import chat_assistant_engine

logger = logging.getLogger("chat_router")

router = APIRouter(
    prefix="/api/v2/chat",
    tags=["Metaphysics AI Live Consultant Chat Assistant"]
)


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message author role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatConsultRequest(BaseModel):
    query: str = Field(..., description="User's metaphysics query")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Recent conversation turns")
    profile: Optional[Dict[str, Any]] = Field(default=None, description="Active user BaZi chart context or birth parameters")


class AnonymizedFeedbackRequest(BaseModel):
    query: str = Field(..., description="User question (anonymized, no PII)")
    response: str = Field(..., description="AI assistant response")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star user rating")
    tags: Optional[List[str]] = Field(default_factory=list, description="Categorization error tags")
    feedback_text: Optional[str] = Field(None, description="Optional user correction")


@router.post("/stream", summary="Live SSE Streaming Consultation Endpoint")
async def stream_chat_consultation(payload: ChatConsultRequest):
    """
    Streams Server-Sent Events (SSE) including delta tokens, RAG citations, and dynamic prompt pills.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history] if payload.history else []
    
    return StreamingResponse(
        chat_assistant_engine.generate_consultation_stream(
            query=payload.query.strip(),
            history=history_dicts,
            profile=payload.profile
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/consult", summary="Synchronous Consultation JSON Endpoint")
async def consult_chat_synchronous(payload: ChatConsultRequest):
    """
    Returns complete synthesized consultation with grounded citations, prompt pills, and context.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history] if payload.history else []

    try:
        response = chat_assistant_engine.generate_consultation_sync(
            query=payload.query.strip(),
            history=history_dicts,
            profile=payload.profile
        )
        return response
    except Exception as e:
        logger.error(f"Chat consultation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consultation generation error: {str(e)}"
        )


@router.post("/prompt-pills", summary="Dynamic Ranked Prompt Pills")
async def get_prompt_pills(profile: Optional[Dict[str, Any]] = None):
    """
    Returns 5 categories of dynamic prompt pills customized to the user's active BaZi chart.
    """
    try:
        context = chat_assistant_engine.build_user_context(profile)
        pills = chat_assistant_engine.generate_dynamic_pills(context)
        return {
            "status": "success",
            "pills": pills,
            "count": len(pills)
        }
    except Exception as e:
        logger.error(f"Prompt pills generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/anonymized-feedback", summary="Submit Opt-in Anonymized QA Feedback")
async def submit_anonymized_feedback(payload: AnonymizedFeedbackRequest):
    """
    Accepts anonymized user feedback to enrich the HITL fine-tuning pipeline.
    Enforces privacy: strictly no PII stored.
    """
    try:
        # In a real environment, can append to hitl_feedback dataset
        logger.info(f"[HITL:Feedback] Anonymized QA feedback received (Rating: {payload.rating}, Tags: {payload.tags})")
        return {
            "status": "success",
            "message": "Thank you for contributing anonymized knowledge to our open metaphysics research pipeline."
        }
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
