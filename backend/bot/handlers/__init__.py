"""Handler registration for the F1 Telegram bot."""

from __future__ import annotations

from telegram.ext import Application

from backend.bot.handlers import (
    driver,
    results,
    schedule,
    settings,
    standings,
    start,
    telemetry,
)
from backend.bot.handlers.error import error_handler


def register_handlers(app: Application) -> None:
    """Register all command handlers and the global error handler."""
    # Start / help / app
    for handler in start.get_handlers():
        app.add_handler(handler)

    # Results (race, qualifying, sprint)
    for handler in results.get_handlers():
        app.add_handler(handler)

    # Standings (wdc, wcc)
    for handler in standings.get_handlers():
        app.add_handler(handler)

    # Schedule (calendar, next)
    for handler in schedule.get_handlers():
        app.add_handler(handler)

    # Driver profile
    for handler in driver.get_handlers():
        app.add_handler(handler)

    # Telemetry (speed, laps, strategy)
    for handler in telemetry.get_handlers():
        app.add_handler(handler)

    # Settings (lang)
    for handler in settings.get_handlers():
        app.add_handler(handler)

    # Global error handler
    app.add_error_handler(error_handler)
