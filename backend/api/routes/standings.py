"""Championship standings endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth import get_telegram_user
from backend.config import settings
from backend.models.schemas import StandingsResponse
from backend.services.standings import standings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/standings", tags=["standings"])


@router.get("/drivers", response_model=StandingsResponse)
async def get_driver_standings(
    year: int = Query(default=None, description="Season year"),
    user: dict | None = Depends(get_telegram_user),
) -> StandingsResponse:
    """Return the driver championship standings for a given year."""
    if year is None:
        year = settings.current_season
    try:
        return await standings_service.get_driver_standings(year)
    except Exception:
        logger.exception("Failed to load driver standings for %d", year)
        raise HTTPException(
            status_code=500,
            detail="Failed to load driver standings.",
        )


@router.get("/constructors", response_model=StandingsResponse)
async def get_constructor_standings(
    year: int = Query(default=None, description="Season year"),
    user: dict | None = Depends(get_telegram_user),
) -> StandingsResponse:
    """Return the constructor championship standings for a given year."""
    if year is None:
        year = settings.current_season
    try:
        return await standings_service.get_constructor_standings(year)
    except Exception:
        logger.exception("Failed to load constructor standings for %d", year)
        raise HTTPException(
            status_code=500,
            detail="Failed to load constructor standings.",
        )
