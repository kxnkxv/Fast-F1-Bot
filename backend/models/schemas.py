from __future__ import annotations

from pydantic import BaseModel


class DriverResult(BaseModel):
    position: int
    driver_code: str
    driver_name: str
    team: str
    team_slug: str
    time: str | None = None
    gap: str | None = None
    points: float = 0
    grid_position: int | None = None
    status: str | None = None
    fastest_lap: bool = False


class SessionResult(BaseModel):
    year: int
    event_name: str
    event_round: int
    session_type: str
    country: str
    results: list[DriverResult]


class DriverStanding(BaseModel):
    position: int
    driver_code: str
    driver_name: str
    team: str
    team_slug: str
    points: float
    wins: int = 0


class ConstructorStanding(BaseModel):
    position: int
    team: str
    team_slug: str
    points: float
    wins: int = 0


class StandingsResponse(BaseModel):
    year: int
    drivers: list[DriverStanding] = []
    constructors: list[ConstructorStanding] = []


class EventInfo(BaseModel):
    round: int
    name: str
    country: str
    location: str
    date: str
    sessions: dict[str, str | None] = {}


class CalendarResponse(BaseModel):
    year: int
    events: list[EventInfo]
    next_event: EventInfo | None = None


class DriverProfile(BaseModel):
    code: str
    first_name: str
    last_name: str
    number: int | None = None
    team: str
    team_slug: str
    country: str | None = None
    season_points: float = 0
    season_wins: int = 0
    season_podiums: int = 0
    season_position: int | None = None
    results: list[DriverResult] = []


class TelemetryPoint(BaseModel):
    distance: float
    speed: float
    throttle: float | None = None
    brake: float | None = None
    gear: int | None = None
    drs: int | None = None


class LapTelemetry(BaseModel):
    driver_code: str
    team: str
    team_slug: str
    lap_number: int | None = None
    lap_time: str | None = None
    telemetry: list[TelemetryPoint]


class TelemetryResponse(BaseModel):
    year: int
    event_name: str
    session_type: str
    laps: list[LapTelemetry]


class TireStint(BaseModel):
    driver_code: str
    team_slug: str
    stint_number: int
    compound: str
    start_lap: int
    end_lap: int
    laps: int


class StrategyResponse(BaseModel):
    year: int
    event_name: str
    total_laps: int
    stints: list[TireStint]
