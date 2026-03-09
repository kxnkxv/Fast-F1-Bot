"""Championship standings service — driver and constructor standings via FastF1 / Ergast."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import fastf1

from backend.cache.dedup import deduplicated_call
from backend.cache.manager import TTL_STANDINGS, cache
from backend.models.schemas import (
    ConstructorStanding,
    DriverStanding,
    StandingsResponse,
)
from backend.services.f1_data import f1_data

logger = logging.getLogger(__name__)


class StandingsService:
    """Fetches and caches WDC / WCC standings."""

    # ------------------------------------------------------------------
    # Driver standings
    # ------------------------------------------------------------------
    async def get_driver_standings(self, year: int) -> StandingsResponse:
        """Return driver championship standings for *year*."""
        cache_key = cache.make_key("standings", "drivers", year)
        cached = await cache.get(cache_key)
        if cached is not None:
            return StandingsResponse(**cached)

        async def _fetch() -> StandingsResponse:
            standings = await self._fetch_driver_standings(year)
            response = StandingsResponse(year=year, drivers=standings)
            await cache.set(
                cache_key,
                response.model_dump(),
                ttl=TTL_STANDINGS,
            )
            return response

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Constructor standings
    # ------------------------------------------------------------------
    async def get_constructor_standings(self, year: int) -> StandingsResponse:
        """Return constructor championship standings for *year*."""
        cache_key = cache.make_key("standings", "constructors", year)
        cached = await cache.get(cache_key)
        if cached is not None:
            return StandingsResponse(**cached)

        async def _fetch() -> StandingsResponse:
            standings = await self._fetch_constructor_standings(year)
            response = StandingsResponse(year=year, constructors=standings)
            await cache.set(
                cache_key,
                response.model_dump(),
                ttl=TTL_STANDINGS,
            )
            return response

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Internal — FastF1 / Ergast fetchers
    # ------------------------------------------------------------------
    async def _fetch_driver_standings(self, year: int) -> list[DriverStanding]:
        """Fetch driver standings using the Ergast API via FastF1."""

        def _blocking() -> list[dict[str, Any]]:
            try:
                ergast = fastf1.ergast.Ergast()
                resp = ergast.get_driver_standings(season=year)
                if resp.content and len(resp.content) > 0:
                    df = resp.content[0]
                    rows: list[dict[str, Any]] = []
                    for _, row in df.iterrows():
                        pos = row.get("position", 0)
                        try:
                            pos = int(float(pos)) if pos == pos else 0  # NaN check
                        except (TypeError, ValueError):
                            pos = 0
                        pts = row.get("points", 0)
                        try:
                            pts = float(pts) if pts == pts else 0.0
                        except (TypeError, ValueError):
                            pts = 0.0
                        wins = row.get("wins", 0)
                        try:
                            wins = int(float(wins)) if wins == wins else 0
                        except (TypeError, ValueError):
                            wins = 0
                        rows.append(
                            {
                                "position": pos,
                                "driver_code": str(row.get("driverCode", "")),
                                "first_name": str(row.get("givenName", "")),
                                "last_name": str(row.get("familyName", "")),
                                "team": str(row.get("constructorName", "") or row.get("constructorNames", "")),
                                "points": pts,
                                "wins": wins,
                            }
                        )
                    return rows
            except Exception:
                logger.exception("Ergast driver standings failed for %d", year)
            return []

        raw_rows = await asyncio.to_thread(_blocking)

        standings: list[DriverStanding] = []
        for r in raw_rows:
            team_name = r["team"]
            # Handle lists of constructor names (mid-season team changes)
            if isinstance(team_name, list):
                team_name = team_name[-1] if team_name else ""
            standings.append(
                DriverStanding(
                    position=r["position"],
                    driver_code=r["driver_code"],
                    driver_name=f'{r["first_name"]} {r["last_name"]}'.strip(),
                    team=str(team_name),
                    team_slug=f1_data.team_slug(str(team_name)),
                    points=r["points"],
                    wins=r["wins"],
                )
            )
        return standings

    async def _fetch_constructor_standings(self, year: int) -> list[ConstructorStanding]:
        """Fetch constructor standings using the Ergast API via FastF1."""

        def _blocking() -> list[dict[str, Any]]:
            try:
                ergast = fastf1.ergast.Ergast()
                resp = ergast.get_constructor_standings(season=year)
                if resp.content and len(resp.content) > 0:
                    df = resp.content[0]
                    rows: list[dict[str, Any]] = []
                    for _, row in df.iterrows():
                        pos = row.get("position", 0)
                        try:
                            pos = int(float(pos)) if pos == pos else 0
                        except (TypeError, ValueError):
                            pos = 0
                        pts = row.get("points", 0)
                        try:
                            pts = float(pts) if pts == pts else 0.0
                        except (TypeError, ValueError):
                            pts = 0.0
                        wins = row.get("wins", 0)
                        try:
                            wins = int(float(wins)) if wins == wins else 0
                        except (TypeError, ValueError):
                            wins = 0
                        rows.append(
                            {
                                "position": pos,
                                "team": str(row.get("constructorName", "")),
                                "points": pts,
                                "wins": wins,
                            }
                        )
                    return rows
            except Exception:
                logger.exception("Ergast constructor standings failed for %d", year)
            return []

        raw_rows = await asyncio.to_thread(_blocking)

        standings: list[ConstructorStanding] = []
        for r in raw_rows:
            standings.append(
                ConstructorStanding(
                    position=r["position"],
                    team=r["team"],
                    team_slug=f1_data.team_slug(r["team"]),
                    points=r["points"],
                    wins=r["wins"],
                )
            )
        return standings


# Global instance
standings_service = StandingsService()
