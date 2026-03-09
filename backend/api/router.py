"""Root API router — aggregates all sub-routers under the /api prefix."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.routes.calendar import router as calendar_router
from backend.api.routes.drivers import router as drivers_router
from backend.api.routes.results import router as results_router
from backend.api.routes.standings import router as standings_router
from backend.api.routes.telemetry import router as telemetry_router

api_router = APIRouter(prefix="/api")

api_router.include_router(results_router)
api_router.include_router(standings_router)
api_router.include_router(calendar_router)
api_router.include_router(drivers_router)
api_router.include_router(telemetry_router)
