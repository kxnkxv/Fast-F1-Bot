"""Telemetry service — speed traces, lap comparisons, and tire strategy data."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.cache.dedup import deduplicated_call
from backend.cache.manager import TTL_FINAL_RESULT, cache
from backend.models.schemas import (
    LapTelemetry,
    StrategyResponse,
    TelemetryPoint,
    TireStint,
)
from backend.services.f1_data import f1_data

logger = logging.getLogger(__name__)


class TelemetryService:
    """Extracts telemetry and strategy information from FastF1 sessions."""

    # ------------------------------------------------------------------
    # Available drivers for a session
    # ------------------------------------------------------------------
    async def get_available_drivers(
        self,
        year: int,
        event: str | int,
        session_type: str,
    ) -> list[str]:
        """Return list of driver codes that have laps in the session."""
        cache_key = cache.make_key("telemetry", "drivers", year, event, session_type)
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        async def _fetch() -> list[str]:
            session = await f1_data.load_session(year, event, session_type)
            drivers = await asyncio.to_thread(
                lambda: sorted(session.laps["Driver"].unique().tolist())
            )
            await cache.set(cache_key, drivers, ttl=TTL_FINAL_RESULT)
            return drivers

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Speed trace for a single driver
    # ------------------------------------------------------------------
    async def get_speed_trace(
        self,
        year: int,
        event: str | int,
        session_type: str,
        driver_code: str,
    ) -> LapTelemetry:
        """Return telemetry for the *driver_code*'s fastest lap."""
        cache_key = cache.make_key("telemetry", "speed", year, event, session_type, driver_code)
        cached = await cache.get(cache_key)
        if cached is not None:
            return LapTelemetry(**cached)

        async def _fetch() -> LapTelemetry:
            session = await f1_data.load_session(year, event, session_type)
            lap_telemetry = await asyncio.to_thread(
                self._extract_speed_trace, session, driver_code
            )
            await cache.set(cache_key, lap_telemetry.model_dump(), ttl=TTL_FINAL_RESULT)
            return lap_telemetry

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Lap comparison for multiple drivers
    # ------------------------------------------------------------------
    async def get_lap_comparison(
        self,
        year: int,
        event: str | int,
        session_type: str,
        drivers: list[str],
    ) -> list[LapTelemetry]:
        """Return fastest-lap telemetry for each driver in *drivers*."""
        drivers_key = ",".join(sorted(drivers))
        cache_key = cache.make_key("telemetry", "compare", year, event, session_type, drivers_key)
        cached = await cache.get(cache_key)
        if cached is not None:
            return [LapTelemetry(**lt) for lt in cached]

        async def _fetch() -> list[LapTelemetry]:
            session = await f1_data.load_session(year, event, session_type)
            results: list[LapTelemetry] = []
            for code in drivers:
                try:
                    lt = await asyncio.to_thread(
                        self._extract_speed_trace, session, code
                    )
                    results.append(lt)
                except Exception:
                    logger.warning("Telemetry extraction failed for %s", code)
            await cache.set(
                cache_key,
                [r.model_dump() for r in results],
                ttl=TTL_FINAL_RESULT,
            )
            return results

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Tire strategy
    # ------------------------------------------------------------------
    async def get_tire_strategy(
        self,
        year: int,
        event: str | int,
    ) -> StrategyResponse:
        """Return pit-stop / tire compound strategy for the race."""
        cache_key = cache.make_key("strategy", year, event)
        cached = await cache.get(cache_key)
        if cached is not None:
            return StrategyResponse(**cached)

        async def _fetch() -> StrategyResponse:
            # Strategy is always from the race session
            session = await f1_data.load_session(year, event, "Race")
            strategy = await asyncio.to_thread(self._extract_strategy, session)
            await cache.set(cache_key, strategy.model_dump(), ttl=TTL_FINAL_RESULT)
            return strategy

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Internal extraction helpers (run in thread)
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_speed_trace(session: Any, driver_code: str) -> LapTelemetry:
        """Extract fastest-lap telemetry for *driver_code* from a loaded session."""
        laps = session.laps.pick_driver(driver_code)
        fastest = laps.pick_fastest()
        if fastest is None:
            raise ValueError(f"No fastest lap found for {driver_code}")

        tel = fastest.get_telemetry()
        points: list[TelemetryPoint] = []
        for _, row in tel.iterrows():
            points.append(
                TelemetryPoint(
                    distance=float(row.get("Distance", 0)),
                    speed=float(row.get("Speed", 0)),
                    throttle=_safe_float(row.get("Throttle")),
                    brake=_safe_float(row.get("Brake")),
                    gear=_safe_int(row.get("nGear")),
                    drs=_safe_int(row.get("DRS")),
                )
            )

        team_name = str(fastest.get("Team", ""))
        lap_time_raw = fastest.get("LapTime")
        lap_time_str: str | None = None
        if lap_time_raw is not None and str(lap_time_raw) not in ("NaT", "nan", ""):
            lap_time_str = str(lap_time_raw)

        lap_number_raw = fastest.get("LapNumber")
        lap_number: int | None = None
        try:
            lap_number = int(lap_number_raw)
        except (TypeError, ValueError):
            pass

        return LapTelemetry(
            driver_code=driver_code,
            team=team_name,
            team_slug=f1_data.team_slug(team_name),
            lap_number=lap_number,
            lap_time=lap_time_str,
            telemetry=points,
        )

    @staticmethod
    def _extract_strategy(session: Any) -> StrategyResponse:
        """Extract tire strategy (stints per driver) from the race session."""
        laps = session.laps
        event_name = str(getattr(session.event, "EventName", ""))
        year = int(getattr(session.event, "year", 0) or session.event.get("year", 0) if hasattr(session.event, "get") else 0)

        # Determine total race laps
        try:
            total_laps = int(laps["LapNumber"].max())
        except Exception:
            total_laps = 0

        stints: list[TireStint] = []
        drivers = laps["Driver"].unique()
        for driver in drivers:
            driver_laps = laps.pick_driver(driver).sort_values("LapNumber")
            if driver_laps.empty:
                continue

            team_name = str(driver_laps.iloc[0].get("Team", ""))
            team_slug = f1_data.team_slug(team_name)

            stint_num = 0
            current_compound: str | None = None
            stint_start: int = 0

            for _, lap in driver_laps.iterrows():
                compound = str(lap.get("Compound", "UNKNOWN"))
                lap_num = int(lap.get("LapNumber", 0))

                if compound != current_compound:
                    # Close previous stint
                    if current_compound is not None:
                        stints.append(
                            TireStint(
                                driver_code=str(driver),
                                team_slug=team_slug,
                                stint_number=stint_num,
                                compound=current_compound,
                                start_lap=stint_start,
                                end_lap=lap_num - 1,
                                laps=(lap_num - 1) - stint_start + 1,
                            )
                        )
                    stint_num += 1
                    current_compound = compound
                    stint_start = lap_num

            # Close final stint
            if current_compound is not None:
                last_lap = int(driver_laps.iloc[-1].get("LapNumber", stint_start))
                stints.append(
                    TireStint(
                        driver_code=str(driver),
                        team_slug=team_slug,
                        stint_number=stint_num,
                        compound=current_compound,
                        start_lap=stint_start,
                        end_lap=last_lap,
                        laps=last_lap - stint_start + 1,
                    )
                )

        return StrategyResponse(
            year=year,
            event_name=event_name,
            total_laps=total_laps,
            stints=stints,
        )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
        if v != v:  # NaN check
            return None
        return v
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        v = float(value)
        if v != v:  # NaN check
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


# Global instance
telemetry_service = TelemetryService()
