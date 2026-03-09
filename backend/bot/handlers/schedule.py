"""Calendar and next-race handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from backend.banners.next_race import render_next_race
from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import calendar_keyboard
from backend.config import settings
from backend.i18n import get_text
from backend.services.calendar_svc import calendar_service

logger = logging.getLogger(__name__)


def _parse_year(args: list[str]) -> int:
    """Parse optional [year] argument, defaulting to current season."""
    if args:
        try:
            return int(args[0])
        except ValueError:
            pass
    return settings.current_season


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/calendar [year] — formatted text list of events."""
    try:
        year = _parse_year(context.args or [])
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        calendar = await calendar_service.get_calendar(year)

        if not calendar.events:
            await update.message.reply_text(get_text("no_calendar", lang))
            return

        lines: list[str] = [get_text("calendar_title", lang, year=year)]
        for ev in calendar.events:
            lines.append(f"  R{ev.round:02d}  {ev.date}  {ev.name} ({ev.country})")

        text = "\n".join(lines)
        keyboard = calendar_keyboard(settings.webapp_url)

        await update.message.reply_text(text, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /calendar command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_calendar", lang))


async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/next — next race banner."""
    try:
        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        year = settings.current_season
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        event = await calendar_service.get_next_event(year)

        if event is None:
            await update.message.reply_text(get_text("no_next_event", lang))
            return

        banner = render_next_race(event, year)
        keyboard = calendar_keyboard(settings.webapp_url)

        await update.message.reply_photo(photo=banner, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /next command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_next", lang))


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [
        CommandHandler("calendar", calendar_command),
        CommandHandler("next", next_command),
    ]
