"""Main entry point — FastAPI application with Telegram bot running in the background."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `from backend.xxx` works
# regardless of whether we're invoked as `python backend/main.py` or `python -m backend.main`.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from telegram.ext import Application

from backend.api.router import api_router
from backend.cache.manager import cache
from backend.config import settings
from backend.services.calendar_svc import calendar_service
from backend.services.f1_data import f1_data
from backend.services.standings import standings_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Background warmup task
# ---------------------------------------------------------------------------
async def _warmup_cache() -> None:
    """Pre-load calendar and standings into cache so first requests are fast."""
    year = settings.current_season
    try:
        logger.info("Cache warmup: loading calendar for %d", year)
        await calendar_service.get_calendar(year)
    except Exception:
        logger.warning("Cache warmup: calendar failed", exc_info=True)

    try:
        logger.info("Cache warmup: loading driver standings for %d", year)
        await standings_service.get_driver_standings(year)
    except Exception:
        logger.warning("Cache warmup: driver standings failed", exc_info=True)

    try:
        logger.info("Cache warmup: loading constructor standings for %d", year)
        await standings_service.get_constructor_standings(year)
    except Exception:
        logger.warning("Cache warmup: constructor standings failed", exc_info=True)

    logger.info("Cache warmup complete")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown of all subsystems."""
    bot: Application | None = None
    warmup_task: asyncio.Task | None = None

    # ---- Startup ----
    # 1. FastF1 disk cache
    f1_data.enable_cache()

    # 2. Redis / memory cache
    cache._redis_url = settings.redis_url
    await cache.connect()

    # 3. Telegram bot (non-blocking polling)
    if settings.telegram_bot_token:
        try:
            from backend.bot.app import create_bot

            bot = create_bot()
            await bot.initialize()
            await bot.start()
            await bot.updater.start_polling(drop_pending_updates=True)
            logger.info("Telegram bot started polling")
        except Exception:
            logger.warning("Telegram bot failed to start", exc_info=True)
            bot = None
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot disabled")

    # 4. Background cache warmup
    warmup_task = asyncio.create_task(_warmup_cache())

    yield

    # ---- Shutdown ----
    # Cancel warmup if still running
    if warmup_task and not warmup_task.done():
        warmup_task.cancel()
        try:
            await warmup_task
        except asyncio.CancelledError:
            pass

    # Stop bot
    if bot is not None:
        try:
            if bot.updater and bot.updater.running:
                await bot.updater.stop()
            await bot.stop()
            await bot.shutdown()
            logger.info("Telegram bot stopped")
        except Exception:
            logger.warning("Error stopping Telegram bot", exc_info=True)

    # Close cache
    await cache.close()
    logger.info("Cache closed")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="F1 Telegram Bot API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve webapp static files (SPA)
# ---------------------------------------------------------------------------
_webapp_dist = Path(__file__).resolve().parent / "static"
if _webapp_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_webapp_dist), html=True), name="webapp")
    logger.info("Serving webapp from %s", _webapp_dist)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.effective_port,
        reload=True,
    )
