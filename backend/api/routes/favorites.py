"""Favorites API endpoints for the WebApp."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.auth import get_telegram_user
from backend.services.favorites import favorites_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoritesResponse(BaseModel):
    drivers: list[str]
    teams: list[str]


class ToggleResponse(BaseModel):
    added: bool
    drivers: list[str]
    teams: list[str]


@router.get("", response_model=FavoritesResponse)
async def get_favorites(
    user: dict | None = Depends(get_telegram_user),
) -> FavoritesResponse:
    """Get current user's favorites."""
    user_id = user.get("id", 0) if user else 0
    if not user_id:
        return FavoritesResponse(drivers=[], teams=[])
    fav = favorites_service.get(user_id)
    return FavoritesResponse(drivers=fav.drivers, teams=fav.teams)


@router.post("/drivers/{code}", response_model=ToggleResponse)
async def toggle_driver(
    code: str,
    user: dict | None = Depends(get_telegram_user),
) -> ToggleResponse:
    """Toggle a driver as favorite."""
    user_id = user.get("id", 0) if user else 0
    if not user_id:
        return ToggleResponse(added=False, drivers=[], teams=[])
    added = favorites_service.toggle_driver(user_id, code.upper())
    fav = favorites_service.get(user_id)
    return ToggleResponse(added=added, drivers=fav.drivers, teams=fav.teams)


@router.post("/teams/{slug}", response_model=ToggleResponse)
async def toggle_team(
    slug: str,
    user: dict | None = Depends(get_telegram_user),
) -> ToggleResponse:
    """Toggle a team as favorite."""
    user_id = user.get("id", 0) if user else 0
    if not user_id:
        return ToggleResponse(added=False, drivers=[], teams=[])
    added = favorites_service.toggle_team(user_id, slug.lower())
    fav = favorites_service.get(user_id)
    return ToggleResponse(added=added, drivers=fav.drivers, teams=fav.teams)
