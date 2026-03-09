"""Calendar / schedule endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.config import settings
from backend.models.schemas import CalendarResponse, EventInfo
from backend.services.calendar_svc import calendar_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/next", response_model=EventInfo | None)
async def get_next_event(
    user: dict | None = Depends(get_telegram_user),
) -> EventInfo | None:
    """Return the next upcoming event for the current season."""
    try:
        event = await calendar_service.get_next_event(settings.current_season)
        if event is None:
            raise HTTPException(
                status_code=404,
                detail="No upcoming events found for the current season.",
            )
        return event
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get next event")
        raise HTTPException(
            status_code=500,
            detail="Failed to determine the next event.",
        )


@router.get("/{year}", response_model=CalendarResponse)
async def get_calendar(
    year: int,
    user: dict | None = Depends(get_telegram_user),
) -> CalendarResponse:
    """Return the full season calendar for the given year."""
    try:
        return await calendar_service.get_calendar(year)
    except Exception:
        logger.exception("Failed to load calendar for %d", year)
        raise HTTPException(
            status_code=500,
            detail="Failed to load the season calendar.",
        )
