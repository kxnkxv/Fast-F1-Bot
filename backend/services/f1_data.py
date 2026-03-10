"""FastF1 wrapper service — loads sessions, results, and provides CDN slug helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import fastf1

from backend.cache.dedup import deduplicated_call
from backend.cache.manager import TTL_FINAL_RESULT, TTL_RECENT_RESULT, cache
from backend.config import settings
from backend.models.schemas import DriverResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Team name → CDN slug mapping
# ---------------------------------------------------------------------------
TEAM_SLUG_MAP: dict[str, str] = {
    "Red Bull Racing": "redbullracing",
    "Red Bull": "redbullracing",
    "Mercedes": "mercedes",
    "McLaren": "mclaren",
    "Ferrari": "ferrari",
    "Aston Martin": "astonmartin",
    "Alpine": "alpine",
    "Alpine F1 Team": "alpine",
    "Williams": "williams",
    "RB": "rb",
    "RB F1 Team": "rb",
    "AlphaTauri": "rb",
    "Kick Sauber": "kicksauber",
    "Alfa Romeo": "kicksauber",
    "Audi": "audi",
    "Haas F1 Team": "haasf1team",
    "Haas": "haasf1team",
    "Cadillac F1 Team": "cadillac",
    "Cadillac": "cadillac",
}

# ---------------------------------------------------------------------------
# Driver abbreviation → CDN code mapping
# ---------------------------------------------------------------------------
DRIVER_CDN_CODE_MAP: dict[str, str] = {
    "VER": "maxver01",
    "HAM": "lewham44",
    "NOR": "lanNor04",
    "LEC": "chalec16",
    "PIA": "oscpia81",
    "SAI": "carsai55",
    "RUS": "georus63",
    "PER": "serper11",
    "ALO": "feralo14",
    "STR": "lanstr18",
    "GAS": "piegas10",
    "OCO": "estoco31",
    "TSU": "yuktsu22",
    "RIC": "danric03",
    "HUL": "nichul27",
    "MAG": "kevmag20",
    "BOT": "valbot77",
    "ZHO": "guazho24",
    "ALB": "alexalb23",
    "SAR": "logsAR02",
}


def _normalise_team_slug(team_name: str) -> str:
    """Return CDN-compatible team slug for a given team name."""
    slug = TEAM_SLUG_MAP.get(team_name)
    if slug:
        return slug
    # Fallback: lowercase, strip spaces and non-alpha characters
    return "".join(ch for ch in team_name.lower() if ch.isalpha())


def _driver_cdn_code(abbreviation: str, first_name: str = "", last_name: str = "", number: int | None = None) -> str:
    """Return CDN driver code for a given abbreviation.

    If the abbreviation is not in the static map, attempt to construct the
    code from the driver's first name, last name and number using the pattern
    ``<first3_first><last3_last><number:02d>``.
    """
    code = DRIVER_CDN_CODE_MAP.get(abbreviation)
    if code:
        return code
    # Attempt to construct from FastF1 data
    if first_name and last_name:
        prefix = first_name[:3].lower() + last_name[:3].lower()
        suffix = f"{number:02d}" if number else "01"
        return f"{prefix}{suffix}"
    return abbreviation.lower()


class F1DataService:
    """High-level facade around FastF1 session loading and result extraction."""

    # ------------------------------------------------------------------
    # Cache / init
    # ------------------------------------------------------------------
    def enable_cache(self) -> None:
        """Enable the FastF1 on-disk cache."""
        path = settings.ff1_cache_path
        fastf1.Cache.enable_cache(str(path))
        logger.info("FastF1 disk cache enabled at %s", path)

    # ------------------------------------------------------------------
    # Session loading
    # ------------------------------------------------------------------
    async def load_session(
        self,
        year: int,
        event: str | int,
        session_type: str,
        *,
        telemetry: bool = True,
    ) -> Any:
        """Load a FastF1 session (blocking work offloaded to a thread).

        Set *telemetry=False* for a lightweight load (laps only, much less RAM).
        Returns the raw ``fastf1.core.Session`` object.
        """
        suffix = "full" if telemetry else "light"
        cache_key = cache.make_key("session", year, event, session_type, suffix)

        async def _fetch() -> Any:
            def _blocking() -> Any:
                session = fastf1.get_session(year, event, session_type)
                session.load(
                    laps=True,
                    telemetry=telemetry,
                    weather=False,
                    messages=False,
                )
                return session

            return await asyncio.to_thread(_blocking)

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Results extraction
    # ------------------------------------------------------------------
    async def load_results(
        self,
        year: int,
        event: str | int,
        session_type: str,
    ) -> list[DriverResult]:
        """Load session and return a structured list of ``DriverResult``."""
        cache_key = cache.make_key("results", year, event, session_type)
        cached = await cache.get(cache_key)
        if cached is not None:
            return [DriverResult(**r) for r in cached]

        # Results only need laps for fastest-lap detection, not full telemetry
        session = await self.load_session(year, event, session_type, telemetry=False)
        results = self._extract_results(session)

        # Determine TTL — completed sessions get a long TTL
        ttl = TTL_FINAL_RESULT if self._is_session_final(session) else TTL_RECENT_RESULT
        await cache.set(cache_key, [r.model_dump() for r in results], ttl=ttl)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_results(session: Any) -> list[DriverResult]:
        """Parse the FastF1 results DataFrame into ``DriverResult`` models."""
        results: list[DriverResult] = []
        df = session.results
        if df is None or df.empty:
            logger.warning("No results available for session %s", session)
            return results

        for _, row in df.iterrows():
            abbreviation = str(row.get("Abbreviation", ""))
            team_name = str(row.get("TeamName", ""))
            first_name = str(row.get("FirstName", ""))
            last_name = str(row.get("LastName", ""))
            driver_number = row.get("DriverNumber")

            # Time / gap formatting
            time_val = row.get("Time")
            time_str: str | None = None
            if time_val is not None and str(time_val) not in ("NaT", "nan", ""):
                time_str = str(time_val)

            gap_val = row.get("Gap")  # only in race-type sessions
            gap_str: str | None = None
            if gap_val is not None and str(gap_val) not in ("NaT", "nan", ""):
                gap_str = str(gap_val)

            position_raw = row.get("Position")
            try:
                position = int(float(position_raw))
            except (TypeError, ValueError):
                position = 0

            grid_raw = row.get("GridPosition")
            grid_position: int | None = None
            try:
                grid_position = int(float(grid_raw))
            except (TypeError, ValueError):
                pass

            points_raw = row.get("Points", 0)
            try:
                points = float(points_raw)
            except (TypeError, ValueError):
                points = 0.0

            results.append(
                DriverResult(
                    position=position,
                    driver_code=abbreviation,
                    driver_name=f"{first_name} {last_name}".strip(),
                    team=team_name,
                    team_slug=_normalise_team_slug(team_name),
                    time=time_str,
                    gap=gap_str,
                    points=points,
                    grid_position=grid_position,
                    status=str(row.get("Status", "")) or None,
                    fastest_lap=False,
                )
            )

        # Mark fastest lap holder (lowest lap time in laps data if available)
        try:
            laps = session.laps
            if laps is not None and not laps.empty:
                fastest = laps.pick_fastest()
                if fastest is not None:
                    fl_code = str(fastest["Driver"])
                    for r in results:
                        if r.driver_code == fl_code:
                            r.fastest_lap = True
                            break
        except Exception:
            logger.debug("Could not determine fastest lap holder")

        return results

    @staticmethod
    def _is_session_final(session: Any) -> bool:
        """Heuristic: consider a session final if results are available."""
        try:
            return session.results is not None and not session.results.empty
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Slug / code helpers (public for use by other services)
    # ------------------------------------------------------------------
    @staticmethod
    def team_slug(team_name: str) -> str:
        return _normalise_team_slug(team_name)

    @staticmethod
    def driver_cdn_code(
        abbreviation: str,
        first_name: str = "",
        last_name: str = "",
        number: int | None = None,
    ) -> str:
        return _driver_cdn_code(abbreviation, first_name, last_name, number)


# Global instance
f1_data = F1DataService()
