"""Telemetry and strategy endpoints."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.models.schemas import StrategyResponse, TelemetryResponse
from backend.services.calendar_svc import calendar_service
from backend.services.telemetry_svc import telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Timeout for FastF1 session loading (seconds).
# Prevents OOM on constrained hosting by aborting before memory explodes.
_SESSION_TIMEOUT = 90


async def _resolve_event(year: int, event: str) -> str | int:
    """Resolve virtual event identifiers like 'last' to real round numbers."""
    if event.lower() == "last":
        round_num = await calendar_service.get_last_event_round(year)
        if round_num is None:
            raise HTTPException(status_code=404, detail="No completed events found for this season.")
        return round_num
    try:
        return int(event)
    except ValueError:
        return event


@router.get(
    "/{year}/{event}/{session}/{driver}",
    response_model=TelemetryResponse,
)
async def get_speed_trace(
    year: int,
    event: str,
    session: str,
    driver: str,
    user: dict | None = Depends(get_telegram_user),
) -> TelemetryResponse:
    """Return speed-trace telemetry for a driver, plus list of available drivers.

    Pass `_available` as driver to get only the available drivers list (no telemetry).
    """
    try:
        event_identifier = await _resolve_event(year, event)

        # Get available drivers with timeout protection
        try:
            available = await asyncio.wait_for(
                telemetry_service.get_available_drivers(
                    year, event_identifier, session
                ),
                timeout=_SESSION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Session data is loading. Please try again in a few minutes.",
            )

        # If just requesting the list, return empty laps
        if driver.upper() == "_AVAILABLE":
            return TelemetryResponse(
                year=year,
                event=str(event_identifier),
                session=session,
                available_drivers=available,
            )

        # Otherwise, get the actual telemetry with timeout
        try:
            lap = await asyncio.wait_for(
                telemetry_service.get_speed_trace(
                    year, event_identifier, session, driver.upper()
                ),
                timeout=_SESSION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Telemetry data is loading. Please try again in a few minutes.",
            )

        return TelemetryResponse(
            year=year,
            event=str(event_identifier),
            session=session,
            laps=[lap],
            available_drivers=available,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to load telemetry: %d %s %s %s", year, event, session, driver
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to load telemetry data.",
        )


@router.get(
    "/{year}/{event}/strategy",
    response_model=StrategyResponse,
)
async def get_tire_strategy(
    year: int,
    event: str,
    user: dict | None = Depends(get_telegram_user),
) -> StrategyResponse:
    """Return tire strategy data for an event."""
    try:
        event_identifier = await _resolve_event(year, event)

        try:
            result = await asyncio.wait_for(
                telemetry_service.get_tire_strategy(year, event_identifier),
                timeout=_SESSION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Strategy data is loading. Please try again in a few minutes.",
            )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No strategy data found for {year} {event}.",
            )
        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load strategy: %d %s", year, event)
        raise HTTPException(
            status_code=500,
            detail="Failed to load tire strategy data.",
        )
