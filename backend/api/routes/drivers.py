"""Driver profile endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_telegram_user
from backend.models.schemas import DriverProfile
from backend.services.driver_svc import driver_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/{year}/{abbr}", response_model=DriverProfile)
async def get_driver_profile(
    year: int,
    abbr: str,
    user: dict | None = Depends(get_telegram_user),
) -> DriverProfile:
    """Return a driver profile for the given season and driver abbreviation.

    - **year**: Season year (e.g. 2024)
    - **abbr**: Three-letter driver code (e.g. "VER", "HAM")
    """
    try:
        profile = await driver_service.get_driver_profile(year, abbr.upper())
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail=f"Driver '{abbr.upper()}' not found for the {year} season.",
            )
        return profile
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load driver profile: %d %s", year, abbr)
        raise HTTPException(
            status_code=500,
            detail="Failed to load the driver profile.",
        )
