"""User settings handlers (language preference)."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from backend.models.enums import Language

logger = logging.getLogger(__name__)

# In-memory language preferences: user_id -> language code
_user_languages: dict[int, str] = {}

SUPPORTED_LANGUAGES = {lang.value for lang in Language}


def get_user_lang(user_id: int | None) -> str:
    """Return the language preference for a user, defaulting to 'en'."""
    if user_id is None:
        return "en"
    return _user_languages.get(user_id, "en")


def set_user_lang(user_id: int, lang: str) -> None:
    """Set the language preference for a user."""
    _user_languages[user_id] = lang


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/lang en|ru — change language preference."""
    try:
        if not context.args or len(context.args) < 1:
            current = get_user_lang(update.effective_user.id if update.effective_user else None)
            await update.message.reply_text(
                f"Current language: {current}\n"
                f"Usage: /lang {' | '.join(sorted(SUPPORTED_LANGUAGES))}"
            )
            return

        lang = context.args[0].lower().strip()
        if lang not in SUPPORTED_LANGUAGES:
            await update.message.reply_text(
                f"Unsupported language: {lang}\n"
                f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            )
            return

        user_id = update.effective_user.id if update.effective_user else None
        if user_id is None:
            await update.message.reply_text("Could not identify user.")
            return

        set_user_lang(user_id, lang)
        await update.message.reply_text(f"Language set to: {lang}")

    except Exception:
        logger.exception("Error in /lang command")
        if update.message:
            await update.message.reply_text("Failed to change language. Please try again.")


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [CommandHandler("lang", lang_command)]
