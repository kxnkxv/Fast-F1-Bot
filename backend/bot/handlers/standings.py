"""WDC and WCC standings handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from backend.banners.standings_banner import render_standings
from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import standings_keyboard
from backend.config import settings
from backend.i18n import get_text
from backend.services.favorites import favorites_service
from backend.services.standings import standings_service

logger = logging.getLogger(__name__)


def _parse_year(args: list[str]) -> int:
    """Parse optional [year] argument, defaulting to current season."""
    if args:
        try:
            return int(args[0])
        except ValueError:
            pass
    return settings.current_season


async def wdc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/wdc [year] — driver championship standings."""
    try:
        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        year = _parse_year(context.args or [])
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        standings = await standings_service.get_driver_standings(year)

        if not standings.drivers:
            await update.message.reply_text(get_text("no_standings", lang))
            return

        user_id = update.effective_user.id if update.effective_user else 0
        fav = favorites_service.get(user_id)
        banner = render_standings(standings, mode="drivers",
                                  favorite_drivers=set(fav.drivers),
                                  favorite_teams=set(fav.teams))
        keyboard = standings_keyboard(settings.webapp_url)

        await update.message.reply_photo(photo=banner, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /wdc command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_standings", lang))


async def wcc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/wcc [year] — constructor championship standings."""
    try:
        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        year = _parse_year(context.args or [])
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        standings = await standings_service.get_constructor_standings(year)

        if not standings.constructors:
            await update.message.reply_text(get_text("no_standings", lang))
            return

        user_id = update.effective_user.id if update.effective_user else 0
        fav = favorites_service.get(user_id)
        banner = render_standings(standings, mode="constructors",
                                  favorite_drivers=set(fav.drivers),
                                  favorite_teams=set(fav.teams))
        keyboard = standings_keyboard(settings.webapp_url)

        await update.message.reply_photo(photo=banner, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /wcc command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_standings", lang))


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [
        CommandHandler("wdc", wdc_command),
        CommandHandler("wcc", wcc_command),
    ]
