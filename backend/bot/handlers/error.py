"""Global error handler for the F1 Telegram bot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a generic message to the user."""
    logger.error("Unhandled exception while processing an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "An unexpected error occurred. Please try again later."
            )
        except Exception:
            logger.error("Failed to send error message to user", exc_info=True)
