"""Inline keyboard factories for the F1 Telegram bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def webapp_button(url: str, text: str = "Open F1 App") -> InlineKeyboardMarkup:
    """Single WebApp button."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))]]
    )


def results_keyboard(
    year: int,
    event: int | str,
    session: str,
    webapp_url: str,
) -> InlineKeyboardMarkup:
    """'View in App' button pointing to the results page."""
    url = f"{webapp_url}/#/results/{year}/{event}/{session}"
    return webapp_button(url, text="View in App")


def standings_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """'View in App' button pointing to the standings page."""
    url = f"{webapp_url}/#/standings"
    return webapp_button(url, text="View in App")


def calendar_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """'View in App' button pointing to the calendar / home page."""
    url = f"{webapp_url}/#/"
    return webapp_button(url, text="View in App")


def driver_keyboard(
    year: int,
    driver_code: str,
    webapp_url: str,
) -> InlineKeyboardMarkup:
    """'View in App' button pointing to the driver profile page."""
    url = f"{webapp_url}/#/driver/{year}/{driver_code}"
    return webapp_button(url, text="View in App")


def telemetry_keyboard(
    year: int,
    event: int | str,
    session: str,
    webapp_url: str,
) -> InlineKeyboardMarkup:
    """'View in App' button pointing to the telemetry page."""
    url = f"{webapp_url}/#/telemetry/{year}/{event}/{session}"
    return webapp_button(url, text="View in App")


def open_app_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Main 'Open F1 App' button."""
    return webapp_button(webapp_url, text="Open F1 App")
