"""Driver profile handler."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from backend.banners.driver_card import render_driver_card
from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import driver_keyboard
from backend.config import settings
from backend.i18n import get_text
from backend.services.assets import asset_service
from backend.services.driver_svc import driver_service
from backend.services.f1_data import _driver_cdn_code

logger = logging.getLogger(__name__)


async def driver_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/driver CODE — driver card banner."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)

        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                get_text("driver_usage", lang)
            )
            return

        driver_code = context.args[0].upper().strip()
        if len(driver_code) != 3:
            await update.message.reply_text(
                get_text("driver_invalid_code", lang, code=driver_code)
            )
            return

        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)

        year = settings.current_season
        profile = await driver_service.get_driver_profile(year, driver_code)

        # Fetch driver photo and car image (best effort)
        photo: bytes | None = None
        car: bytes | None = None
        cdn_code = _driver_cdn_code(driver_code)
        try:
            photo = await asset_service.get_driver_photo(
                year, profile.team_slug, cdn_code, size=600
            )
        except Exception:
            logger.debug("Could not fetch photo for %s", driver_code)
        try:
            car = await asset_service.get_team_car(
                year, profile.team_slug, size=512
            )
        except Exception:
            logger.debug("Could not fetch car image for %s", profile.team_slug)

        banner = render_driver_card(profile, photo, car)
        keyboard = driver_keyboard(year, driver_code, settings.webapp_url)

        await update.message.reply_photo(photo=banner, reply_markup=keyboard)

    except Exception:
        logger.exception("Error in /driver command")
        if update.message:
            lang = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(get_text("error_driver", lang))


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [CommandHandler("driver", driver_command)]
