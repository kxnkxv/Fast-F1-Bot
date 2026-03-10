"""Telemetry and strategy endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.models.schemas import StrategyResponse, TelemetryResponse
from backend.services.telemetry_svc import telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


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
        try:
            event_identifier: str | int = int(event)
        except ValueError:
            event_identifier = event

        # Always get available drivers for the session
        available = await telemetry_service.get_available_drivers(
            year, event_identifier, session
        )

        # If just requesting the list, return empty laps
        if driver.upper() == "_AVAILABLE":
            return TelemetryResponse(
                year=year,
                event=event,
                session=session,
                available_drivers=available,
            )

        # Otherwise, get the actual telemetry
        lap = await telemetry_service.get_speed_trace(
            year, event_identifier, session, driver.upper()
        )
        return TelemetryResponse(
            year=year,
            event=event,
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
    """Return tire strategy data for an event.

    - **year**: Season year
    - **event**: Event name or round number
    """
    try:
        try:
            event_identifier: str | int = int(event)
        except ValueError:
            event_identifier = event

        result = await telemetry_service.get_tire_strategy(year, event_identifier)
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
