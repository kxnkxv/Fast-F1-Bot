"""Telemetry and strategy endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.cache.manager import cache
from backend.models.schemas import StrategyResponse, TelemetryResponse
from backend.services.calendar_svc import calendar_service
from backend.services.telemetry_svc import telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


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


async def _has_cached_data(year: int, event: str | int, session: str) -> bool:
    """Check if telemetry data is already in cache (safe to serve)."""
    drivers_key = cache.make_key("telemetry", "drivers", year, event, session)
    return await cache.get(drivers_key) is not None


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

        # Only serve from cache — loading FastF1 sessions is too heavy for
        # constrained hosting (OOM with 1 GB RAM).  Bot commands pre-warm
        # the cache; the webapp reads from it.
        if not await _has_cached_data(year, event_identifier, session):
            raise HTTPException(
                status_code=503,
                detail="Telemetry data is not yet available. Send /speed in the bot to load it.",
            )

        available = await telemetry_service.get_available_drivers(
            year, event_identifier, session
        )

        if driver.upper() == "_AVAILABLE":
            return TelemetryResponse(
                year=year,
                event=str(event_identifier),
                session=session,
                available_drivers=available,
            )

        # Check if this specific driver's telemetry is cached
        speed_key = cache.make_key("telemetry", "speed", year, event_identifier, session, driver.upper())
        if await cache.get(speed_key) is None:
            raise HTTPException(
                status_code=503,
                detail=f"Telemetry for {driver.upper()} is not cached. Send /speed in the bot to load it.",
            )

        lap = await telemetry_service.get_speed_trace(
            year, event_identifier, session, driver.upper()
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

        # Only serve from cache
        strategy_key = cache.make_key("strategy", year, event_identifier)
        if await cache.get(strategy_key) is None:
            raise HTTPException(
                status_code=503,
                detail="Strategy data is not yet available. Send /strategy in the bot to load it.",
            )

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
