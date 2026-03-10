"""Calendar service — season schedule and next-event lookup via FastF1."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import fastf1

from backend.cache.dedup import deduplicated_call
from backend.cache.manager import TTL_CALENDAR, cache
from backend.models.schemas import CalendarResponse, EventInfo

logger = logging.getLogger(__name__)

# Session keys that FastF1 exposes on an event row.
_SESSION_KEYS: list[str] = [
    "Session1",
    "Session2",
    "Session3",
    "Session4",
    "Session5",
]
_SESSION_DATE_KEYS: list[str] = [
    "Session1Date",
    "Session2Date",
    "Session3Date",
    "Session4Date",
    "Session5Date",
]


class CalendarService:
    """Provides the full season calendar and next-event lookup."""

    # ------------------------------------------------------------------
    # Full calendar
    # ------------------------------------------------------------------
    async def get_calendar(self, year: int) -> CalendarResponse:
        """Return every event in the *year* season."""
        cache_key = cache.make_key("calendar", year)
        cached = await cache.get(cache_key)
        if cached is not None:
            return CalendarResponse(**cached)

        async def _fetch() -> CalendarResponse:
            events = await self._load_events(year)
            next_evt = self._find_next_event(events)
            response = CalendarResponse(
                year=year,
                events=events,
                next_event=next_evt,
            )
            await cache.set(
                cache_key,
                response.model_dump(),
                ttl=TTL_CALENDAR,
            )
            return response

        return await deduplicated_call(cache_key, _fetch)

    # ------------------------------------------------------------------
    # Next event
    # ------------------------------------------------------------------
    async def get_next_event(self, year: int) -> EventInfo | None:
        """Return the next upcoming event, or ``None`` if the season is over."""
        calendar = await self.get_calendar(year)
        return self._find_next_event(calendar.events)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _load_events(self, year: int) -> list[EventInfo]:
        """Load the event schedule from FastF1 in a worker thread."""

        def _blocking() -> list[dict[str, Any]]:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
            rows: list[dict[str, Any]] = []
            for _, row in schedule.iterrows():
                # Build session name → datetime string mapping
                sessions: dict[str, str | None] = {}
                for skey, dkey in zip(_SESSION_KEYS, _SESSION_DATE_KEYS):
                    session_name = row.get(skey)
                    session_date = row.get(dkey)
                    if session_name and str(session_name) not in ("None", "nan", ""):
                        dt_str: str | None = None
                        if session_date is not None and str(session_date) not in ("NaT", "nan", ""):
                            dt_str = str(session_date)
                        sessions[str(session_name)] = dt_str

                # Event-level date (use the last session date as event date)
                event_date_raw = row.get("Session5Date") or row.get("EventDate")
                event_date_str = ""
                if event_date_raw is not None and str(event_date_raw) not in ("NaT", "nan", ""):
                    event_date_str = str(event_date_raw)

                round_number = row.get("RoundNumber")
                try:
                    round_number = int(round_number)
                except (TypeError, ValueError):
                    round_number = 0

                rows.append(
                    {
                        "round": round_number,
                        "name": str(row.get("EventName", "")),
                        "country": str(row.get("Country", "")),
                        "location": str(row.get("Location", "")),
                        "date": event_date_str,
                        "sessions": sessions,
                    }
                )
            return rows

        raw = await asyncio.to_thread(_blocking)

        events: list[EventInfo] = []
        for r in raw:
            if r["round"] == 0:
                # Skip testing rows that may have round 0
                continue
            events.append(EventInfo(**r))
        return events

    async def get_last_event_round(self, year: int) -> int | None:
        """Return the round number of the most recently completed event."""
        calendar = await self.get_calendar(year)
        last = self._find_last_event(calendar.events)
        return last.round if last else None

    @staticmethod
    def _find_last_event(events: list[EventInfo]) -> EventInfo | None:
        """Return the most recent event whose date is in the past."""
        now = datetime.now(tz=timezone.utc)
        last: EventInfo | None = None
        for event in events:
            if not event.date:
                continue
            try:
                event_dt = datetime.fromisoformat(event.date)
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                if event_dt <= now:
                    last = event
            except (ValueError, TypeError):
                continue
        return last

    @staticmethod
    def _find_next_event(events: list[EventInfo]) -> EventInfo | None:
        """Return the first event whose date is in the future."""
        now = datetime.now(tz=timezone.utc)
        for event in events:
            if not event.date:
                continue
            try:
                event_dt = datetime.fromisoformat(event.date)
                # Ensure timezone-aware comparison
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                if event_dt > now:
                    return event
            except (ValueError, TypeError):
                logger.debug("Unparseable event date: %s", event.date)
                continue
        return None


# Global instance
calendar_service = CalendarService()
