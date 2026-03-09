"""Telemetry plot handlers: speed trace, lap comparison, tire strategy."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import telemetry_keyboard
from backend.config import settings
from backend.i18n import get_text
from backend.models.enums import SessionType
from backend.plotting.lap_comparison import render_lap_comparison
from backend.plotting.speed_trace import render_speed_trace
from backend.plotting.tire_strategy import render_strategy
from backend.services.telemetry_svc import telemetry_service

logger = logging.getLogger(__name__)


async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/speed year round DR1 [DR2] — speed trace plot."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        args = context.args or []

        if len(args) < 3:
            await update.message.reply_text(
                get_text("speed_usage", lang)
            )
            return

        try:
            year = int(args[0])
            event = int(args[1])
        except ValueError:
            await update.message.reply_text(
                get_text("speed_usage", lang)
            )
            return

        drivers = [a.upper() for a in args[2:]]
        session_type = SessionType.RACE

        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        telemetry = await telemetry_service.get_speed_trace(
            year, event, session_type, drivers
        )

        plot = render_speed_trace(telemetry.laps)
        keyboard = telemetry_keyboard(year, event, session_type, settings.webapp_url)

        await update.message.reply_photo(photo=plot, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /speed command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_telemetry", lang))


async def laps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/laps year round DR1 [DR2] — lap comparison plot."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        args = context.args or []

        if len(args) < 3:
            await update.message.reply_text(
                get_text("laps_usage", lang)
            )
            return

        try:
            year = int(args[0])
            event = int(args[1])
        except ValueError:
            await update.message.reply_text(
                get_text("laps_usage", lang)
            )
            return

        drivers = [a.upper() for a in args[2:]]
        session_type = SessionType.RACE

        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        telemetry = await telemetry_service.get_lap_comparison(
            year, event, session_type, drivers
        )

        plot = render_lap_comparison(telemetry.laps)
        keyboard = telemetry_keyboard(year, event, session_type, settings.webapp_url)

        await update.message.reply_photo(photo=plot, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /laps command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_telemetry", lang))


async def strategy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/strategy [year] [round] — tire strategy plot."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        args = context.args or []

        year = settings.current_season
        event: int | str = "latest"

        if args:
            try:
                year = int(args[0])
            except ValueError:
                pass
        if len(args) >= 2:
            try:
                event = int(args[1])
            except ValueError:
                event = args[1]

        session_type = SessionType.RACE

        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        strategy = await telemetry_service.get_tire_strategy(year, event, session_type)

        plot = render_strategy(strategy)
        event_id = event if isinstance(event, int) else 0
        keyboard = telemetry_keyboard(year, event_id, session_type, settings.webapp_url)

        await update.message.reply_photo(photo=plot, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /strategy command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_telemetry", lang))


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [
        CommandHandler("speed", speed_command),
        CommandHandler("laps", laps_command),
        CommandHandler("strategy", strategy_command),
    ]
