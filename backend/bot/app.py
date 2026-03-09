"""Bot Application factory."""

from __future__ import annotations

import logging

from telegram import BotCommand
from telegram.ext import Application

from backend.bot.handlers import register_handlers
from backend.config import settings

logger = logging.getLogger(__name__)

# Commands to register with BotFather via set_my_commands
BOT_COMMANDS = [
    BotCommand("race", "Race results"),
    BotCommand("qualifying", "Qualifying results"),
    BotCommand("sprint", "Sprint results"),
    BotCommand("wdc", "Driver standings"),
    BotCommand("wcc", "Constructor standings"),
    BotCommand("calendar", "Season calendar"),
    BotCommand("next", "Next race"),
    BotCommand("driver", "Driver profile (e.g. /driver VER)"),
    BotCommand("speed", "Speed trace (e.g. /speed 2025 1 VER NOR)"),
    BotCommand("laps", "Lap comparison (e.g. /laps 2025 1 VER NOR)"),
    BotCommand("strategy", "Tire strategy"),
    BotCommand("favorites", "Manage favorite drivers & teams"),
    BotCommand("fav", "Quick favorites (e.g. /fav add VER)"),
    BotCommand("lang", "Change language (en/ru)"),
    BotCommand("app", "Open F1 web app"),
    BotCommand("help", "Show help"),
]


async def _post_init(application: Application) -> None:
    """Called after the Application is initialized — sets bot commands."""
    try:
        await application.bot.set_my_commands(BOT_COMMANDS)
        logger.info("Bot commands registered successfully")
    except Exception:
        logger.exception("Failed to set bot commands")


def create_bot() -> Application:
    """Build and return a fully configured Application instance."""
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .build()
    )

    register_handlers(application)

    logger.info("Bot application created")
    return application
