"""Session results endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.models.schemas import DriverResult, SessionResult
from backend.services.calendar_svc import calendar_service
from backend.services.f1_data import f1_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{year}/{event}/{session}", response_model=SessionResult)
async def get_results(
    year: int,
    event: str,
    session: str,
    user: dict | None = Depends(get_telegram_user),
) -> SessionResult:
    """Load session results for a given year, event, and session type.

    - **year**: Season year (e.g. 2024)
    - **event**: Event name or round number (e.g. "Bahrain" or "1")
    - **session**: Session type (e.g. "R", "Q", "FP1")
    """
    try:
        # Resolve virtual identifiers like "last"
        if event.lower() == "last":
            round_num = await calendar_service.get_last_event_round(year)
            if round_num is None:
                raise HTTPException(status_code=404, detail="No completed events found.")
            event_identifier: str | int = round_num
        else:
            try:
                event_identifier = int(event)
            except ValueError:
                event_identifier = event

        results: list[DriverResult] = await f1_data.load_results(
            year, event_identifier, session
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for {year} {event} {session}",
            )

        # Build the response — use the first result's info for event metadata
        # Since we don't have the raw session here, construct a basic response
        return SessionResult(
            year=year,
            event_name=str(event_identifier),
            event_round=int(event) if event.isdigit() else 0,
            session_type=session,
            country="",
            results=results,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load results: %d %s %s", year, event, session)
        raise HTTPException(
            status_code=500,
            detail="Failed to load session results. The data may not be available yet.",
        )
