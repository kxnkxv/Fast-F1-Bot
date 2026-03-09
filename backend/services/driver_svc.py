"""Driver service — driver profile aggregation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import fastf1

from backend.cache.dedup import deduplicated_call
from backend.cache.manager import TTL_STANDINGS, cache
from backend.config import settings
from backend.models.schemas import DriverProfile, DriverResult
from backend.services.f1_data import f1_data
from backend.services.standings import standings_service

logger = logging.getLogger(__name__)


class DriverService:
    """Aggregates driver information from FastF1 data and standings."""

    async def get_driver_profile(self, year: int, driver_code: str) -> DriverProfile:
        """Build a complete ``DriverProfile`` for *driver_code* in *year*.

        Combines basic identity data from FastF1 with championship standing
        information and recent race results.
        """
        cache_key = cache.make_key("driver", "profile", year, driver_code)
        cached = await cache.get(cache_key)
        if cached is not None:
            return DriverProfile(**cached)

        async def _fetch() -> DriverProfile:
            profile = await self._build_profile(year, driver_code)
            await cache.set(cache_key, profile.model_dump(), ttl=TTL_STANDINGS)
            return profile

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _build_profile(self, year: int, driver_code: str) -> DriverProfile:
        """Gather data from multiple sources and assemble the profile."""
        # Fetch driver identity and standings concurrently
        identity_task = asyncio.create_task(self._get_driver_identity(year, driver_code))
        standings_task = asyncio.create_task(standings_service.get_driver_standings(year))
        results_task = asyncio.create_task(self._get_season_results(year, driver_code))

        identity = await identity_task
        standings_resp = await standings_task
        season_results = await results_task

        # Find this driver in standings
        standing_entry = None
        for d in standings_resp.drivers:
            if d.driver_code == driver_code:
                standing_entry = d
                break

        # Count podiums from results
        podiums = sum(1 for r in season_results if r.position <= 3)

        first_name = identity.get("first_name", "")
        last_name = identity.get("last_name", "")
        team_name = identity.get("team", standing_entry.team if standing_entry else "")
        number = identity.get("number")

        return DriverProfile(
            code=driver_code,
            first_name=first_name,
            last_name=last_name,
            number=number,
            team=team_name,
            team_slug=f1_data.team_slug(team_name),
            country=identity.get("country"),
            season_points=standing_entry.points if standing_entry else 0,
            season_wins=standing_entry.wins if standing_entry else 0,
            season_podiums=podiums,
            season_position=standing_entry.position if standing_entry else None,
            results=season_results,
        )

    async def _get_driver_identity(self, year: int, driver_code: str) -> dict[str, Any]:
        """Load basic driver identity (name, number, nationality) from FastF1."""

        def _blocking() -> dict[str, Any]:
            try:
                schedule = fastf1.get_event_schedule(year, include_testing=False)
                if schedule.empty:
                    return {}
                # Use the first event to load driver info
                first_round = int(schedule.iloc[0]["RoundNumber"])
                session = fastf1.get_session(year, first_round, "Race")
                session.load(laps=False, telemetry=False, weather=False, messages=False)
                results = session.results
                if results is None or results.empty:
                    return {}
                driver_row = results[results["Abbreviation"] == driver_code]
                if driver_row.empty:
                    return {}
                row = driver_row.iloc[0]
                number_raw = row.get("DriverNumber")
                number: int | None = None
                try:
                    number = int(number_raw)
                except (TypeError, ValueError):
                    pass
                return {
                    "first_name": str(row.get("FirstName", "")),
                    "last_name": str(row.get("LastName", "")),
                    "team": str(row.get("TeamName", "")),
                    "number": number,
                    "country": str(row.get("CountryCode", "")) or None,
                }
            except Exception:
                logger.exception("Failed to load identity for %s in %d", driver_code, year)
                return {}

        return await asyncio.to_thread(_blocking)

    async def _get_season_results(self, year: int, driver_code: str) -> list[DriverResult]:
        """Collect race results for *driver_code* across all completed rounds."""

        def _blocking() -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            try:
                schedule = fastf1.get_event_schedule(year, include_testing=False)
                for _, event_row in schedule.iterrows():
                    round_num = int(event_row["RoundNumber"])
                    try:
                        session = fastf1.get_session(year, round_num, "Race")
                        session.load(laps=False, telemetry=False, weather=False, messages=False)
                        results = session.results
                        if results is None or results.empty:
                            continue
                        driver_rows = results[results["Abbreviation"] == driver_code]
                        if driver_rows.empty:
                            continue
                        r = driver_rows.iloc[0]
                        position_raw = r.get("Position")
                        try:
                            position = int(float(position_raw))
                        except (TypeError, ValueError):
                            position = 0
                        points_raw = r.get("Points", 0)
                        try:
                            points = float(points_raw)
                        except (TypeError, ValueError):
                            points = 0.0
                        grid_raw = r.get("GridPosition")
                        grid_position: int | None = None
                        try:
                            grid_position = int(float(grid_raw))
                        except (TypeError, ValueError):
                            pass
                        time_val = r.get("Time")
                        time_str: str | None = None
                        if time_val is not None and str(time_val) not in ("NaT", "nan", ""):
                            time_str = str(time_val)
                        team_name = str(r.get("TeamName", ""))
                        rows.append(
                            {
                                "position": position,
                                "driver_code": driver_code,
                                "driver_name": f'{r.get("FirstName", "")} {r.get("LastName", "")}'.strip(),
                                "team": team_name,
                                "team_slug": f1_data.team_slug(team_name),
                                "time": time_str,
                                "gap": None,
                                "points": points,
                                "grid_position": grid_position,
                                "status": str(r.get("Status", "")) or None,
                                "fastest_lap": False,
                            }
                        )
                    except Exception:
                        # Session not yet available or failed to load — skip
                        continue
            except Exception:
                logger.exception("Failed to gather season results for %s/%d", driver_code, year)
            return rows

        raw = await asyncio.to_thread(_blocking)
        return [DriverResult(**r) for r in raw]


# Global instance
driver_service = DriverService()
