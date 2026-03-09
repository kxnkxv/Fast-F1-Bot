"""Start, help, and app command handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from backend.bot.handlers.settings import get_user_lang
from backend.bot.keyboards import open_app_keyboard
from backend.config import settings
from backend.i18n import get_text

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — send welcome message with Open F1 App button."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        text = get_text("welcome", lang)
        keyboard = open_app_keyboard(settings.webapp_url)
        await update.message.reply_text(text, reply_markup=keyboard)
    except Exception:
        logger.exception("Error in /start command")
        if update.message:
            await update.message.reply_text("Welcome to F1 Bot! Something went wrong.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — send help text with available commands."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        text = get_text("help", lang)
        await update.message.reply_text(text)
    except Exception:
        logger.exception("Error in /help command")
        if update.message:
            await update.message.reply_text(
                "Available commands:\n"
                "/race - Race results\n"
                "/qualifying - Qualifying results\n"
                "/sprint - Sprint results\n"
                "/wdc - Driver standings\n"
                "/wcc - Constructor standings\n"
                "/calendar - Season calendar\n"
                "/next - Next race\n"
                "/driver CODE - Driver profile\n"
                "/speed - Speed trace\n"
                "/laps - Lap comparison\n"
                "/strategy - Tire strategy\n"
                "/lang - Change language\n"
                "/app - Open web app"
            )


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/app — send Open F1 App button."""
    try:
        lang = get_user_lang(update.effective_user.id if update.effective_user else None)
        text = get_text("open_app", lang)
        keyboard = open_app_keyboard(settings.webapp_url)
        await update.message.reply_text(text, reply_markup=keyboard)
    except Exception:
        logger.exception("Error in /app command")
        if update.message:
            await update.message.reply_text("Failed to open app. Please try again.")


def get_handlers() -> list[CommandHandler]:
    """Return handlers for this module."""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("app", app_command),
    ]
