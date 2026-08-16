"""
project/routers/calendar.py
===========================
API Router for Interactive Astrological Calendar & Auspicious Date Selector.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, HTTPException

from project.core.calendar_engine import CalendarEngine

logger = logging.getLogger("calendar_api")
calendar_router = APIRouter(prefix="/api/v1/calendar", tags=["Astrological Calendar & Date Selection"])


class DateQueryRequest(BaseModel):
    intent: str = Field("business_opening", description="business_opening | marriage_ceremony | home_moving | contract_signing | travel_journey | wealth_investment")
    start_date: str = Field(..., description="YYYY-MM-DD format")
    days_ahead: int = Field(30, description="Number of days to search ahead")
    user_day_master: Optional[str] = Field(None, description="User's Day Master Stem (e.g. 甲, 乙)")
    user_zodiac: Optional[str] = Field(None, description="User's Birth Year Branch (e.g. 子, 丑)")


@calendar_router.get("/month")
def get_monthly_calendar(
    year: int = Query(2026, description="Calendar Year"),
    month: int = Query(8, description="Calendar Month (1-12)"),
    user_day_master: Optional[str] = Query(None, description="User Day Master"),
    user_zodiac: Optional[str] = Query(None, description="User Zodiac Branch")
) -> Dict[str, Any]:
    """Retrieve full monthly astrological calendar metadata with 12 duty officers and suitability."""
    try:
        return CalendarEngine.generate_monthly_calendar(
            year=year,
            month=month,
            user_day_master=user_day_master,
            user_zodiac=user_zodiac
        )
    except Exception as e:
        logger.error(f"[CALENDAR] Failed to generate monthly calendar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@calendar_router.post("/query-dates")
def query_auspicious_dates(req: DateQueryRequest) -> List[Dict[str, Any]]:
    """Find and rank auspicious dates for specific activity in upcoming period."""
    try:
        return CalendarEngine.find_best_dates(
            intent=req.intent,
            start_date=req.start_date,
            days_ahead=req.days_ahead,
            user_day_master=req.user_day_master,
            user_zodiac=req.user_zodiac
        )
    except Exception as e:
        logger.error(f"[CALENDAR] Failed to query auspicious dates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
