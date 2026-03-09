"""Race, qualifying, and sprint result handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from backend.banners.qualifying_result import render_qualifying_result
from backend.banners.race_result import render_race_result
from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import results_keyboard
from backend.config import settings
from backend.i18n import get_text
from backend.models.enums import SessionType
from backend.models.schemas import SessionResult
from backend.services.assets import asset_service
from backend.services.f1_data import f1_data, _driver_cdn_code

logger = logging.getLogger(__name__)


def _parse_year_round(args: list[str]) -> tuple[int, int | str]:
    """Parse optional [year] [round] from command arguments.

    Returns (year, event) where event is either a round number or 'latest'.
    """
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

    return year, event


async def _fetch_photos(year: int, results: list) -> dict[str, bytes]:
    """Fetch driver photos for the top results."""
    photos: dict[str, bytes] = {}
    for r in results[:10]:
        try:
            cdn_code = _driver_cdn_code(r.driver_code)
            photo = await asset_service.get_driver_photo(
                year, r.team_slug, cdn_code, size=440
            )
            if photo:
                photos[r.driver_code] = photo
        except Exception:
            logger.debug("Could not fetch photo for %s", r.driver_code)
    return photos


async def _send_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session_type: str,
    render_func,
) -> None:
    """Common logic: load results, render banner, send photo."""
    try:
        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        args = context.args or []
        year, event = _parse_year_round(args)
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        driver_results = await f1_data.load_results(year, event, session_type)

        if not driver_results:
            await update.message.reply_text(
                get_text("no_results", lang, session=session_type)
            )
            return

        # Build SessionResult
        first = driver_results[0]
        session_result = SessionResult(
            year=year,
            event_name=str(event),
            event_round=event if isinstance(event, int) else 0,
            session_type=session_type,
            country="",
            results=driver_results,
        )

        photos = await _fetch_photos(year, driver_results)
        banner = render_func(session_result, photos)

        event_id = event if isinstance(event, int) else 0
        keyboard = results_keyboard(year, event_id, session_type, settings.webapp_url)

        await update.message.reply_photo(photo=banner, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in %s command", session_type)
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(
                get_text("error_results", lang, session=session_type)
            )


async def race_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/race [year] [round] — race results banner."""
    await _send_result(update, context, SessionType.RACE, render_race_result)


async def qualifying_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/qualifying [year] [round] — qualifying results banner."""
    await _send_result(update, context, SessionType.QUALIFYING, render_qualifying_result)


async def sprint_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sprint [year] [round] — sprint results banner."""
    await _send_result(update, context, SessionType.SPRINT, render_race_result)


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [
        CommandHandler("race", race_command),
        CommandHandler("qualifying", qualifying_command),
        CommandHandler("sprint", sprint_command),
    ]
