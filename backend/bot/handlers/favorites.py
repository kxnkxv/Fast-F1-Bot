"""Favorites management handler with inline keyboard UI."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from backend.banners.design_system import TEAM_COLORS
from backend.bot.handlers.settings import get_user_lang
from backend.i18n import get_text
from backend.services.favorites import favorites_service

logger = logging.getLogger(__name__)

# Callback data prefixes
CB_FAV_MENU = "fav:menu"
CB_FAV_DRIVERS = "fav:drivers"
CB_FAV_TEAMS = "fav:teams"
CB_FAV_TOGGLE_DRIVER = "fav:td:"
CB_FAV_TOGGLE_TEAM = "fav:tt:"
CB_FAV_CLEAR = "fav:clear"
CB_FAV_CLEAR_CONFIRM = "fav:clear:yes"

# Known drivers for current season (updated from FastF1 at runtime if available)
KNOWN_DRIVERS: list[tuple[str, str]] = [
    ("VER", "Verstappen"),
    ("NOR", "Norris"),
    ("LEC", "Leclerc"),
    ("PIA", "Piastri"),
    ("SAI", "Sainz"),
    ("HAM", "Hamilton"),
    ("RUS", "Russell"),
    ("ALO", "Alonso"),
    ("STR", "Stroll"),
    ("GAS", "Gasly"),
    ("OCO", "Ocon"),
    ("TSU", "Tsunoda"),
    ("RIC", "Ricciardo"),
    ("HUL", "Hulkenberg"),
    ("MAG", "Magnussen"),
    ("ALB", "Albon"),
    ("BOT", "Bottas"),
    ("ZHO", "Zhou"),
    ("SAR", "Sargeant"),
    ("PER", "Perez"),
]

TEAM_DISPLAY_NAMES: dict[str, str] = {
    "redbullracing": "Red Bull",
    "mercedes": "Mercedes",
    "ferrari": "Ferrari",
    "mclaren": "McLaren",
    "astonmartin": "Aston Martin",
    "alpine": "Alpine",
    "williams": "Williams",
    "rb": "RB",
    "kicksauber": "Kick Sauber",
    "haasf1team": "Haas",
}


def _build_favorites_text(user_id: int, lang: str) -> str:
    """Build the favorites summary text."""
    fav = favorites_service.get(user_id)

    if fav.is_empty():
        return get_text("fav_empty", lang)

    lines = [get_text("fav_title", lang)]

    if fav.drivers:
        lines.append("")
        lines.append(get_text("fav_drivers_label", lang))
        for code in fav.drivers:
            name = next((n for c, n in KNOWN_DRIVERS if c == code), code)
            lines.append(f"  ★ {name} ({code})")

    if fav.teams:
        lines.append("")
        lines.append(get_text("fav_teams_label", lang))
        for slug in fav.teams:
            name = TEAM_DISPLAY_NAMES.get(slug, slug)
            lines.append(f"  ★ {name}")

    return "\n".join(lines)


def _main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Main favorites management keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("fav_btn_add_driver", lang),
                callback_data=CB_FAV_DRIVERS,
            ),
            InlineKeyboardButton(
                get_text("fav_btn_add_team", lang),
                callback_data=CB_FAV_TEAMS,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("fav_btn_clear", lang),
                callback_data=CB_FAV_CLEAR,
            ),
        ],
    ])


def _drivers_keyboard(user_id: int, lang: str) -> InlineKeyboardMarkup:
    """Grid of drivers with ✓ for favorites."""
    fav = favorites_service.get(user_id)
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for code, name in KNOWN_DRIVERS:
        mark = "✓ " if fav.has_driver(code) else ""
        row.append(
            InlineKeyboardButton(
                f"{mark}{code} {name}",
                callback_data=f"{CB_FAV_TOGGLE_DRIVER}{code}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            get_text("fav_btn_back", lang),
            callback_data=CB_FAV_MENU,
        )
    ])
    return InlineKeyboardMarkup(buttons)


def _teams_keyboard(user_id: int, lang: str) -> InlineKeyboardMarkup:
    """Grid of teams with ✓ for favorites."""
    fav = favorites_service.get(user_id)
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for slug, display_name in TEAM_DISPLAY_NAMES.items():
        mark = "✓ " if fav.has_team(slug) else ""
        row.append(
            InlineKeyboardButton(
                f"{mark}{display_name}",
                callback_data=f"{CB_FAV_TOGGLE_TEAM}{slug}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            get_text("fav_btn_back", lang),
            callback_data=CB_FAV_MENU,
        )
    ])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/favorites — show favorites with management menu."""
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    text = _build_favorites_text(user_id, lang)
    keyboard = _main_menu_keyboard(lang)
    await update.message.reply_text(text, reply_markup=keyboard)


async def fav_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/fav add|remove|clear [driver|team] [code] — quick favorites management."""
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    args = context.args or []

    if not args:
        # Same as /favorites
        text = _build_favorites_text(user_id, lang)
        keyboard = _main_menu_keyboard(lang)
        await update.message.reply_text(text, reply_markup=keyboard)
        return

    action = args[0].lower()

    if action == "clear":
        favorites_service.clear(user_id)
        await update.message.reply_text(get_text("fav_cleared", lang))
        return

    if action in ("add", "remove") and len(args) >= 2:
        if args[1].lower() == "team" and len(args) >= 3:
            slug = args[2].lower()
            # Try to match partial team name
            matched = _match_team(slug)
            if matched:
                if action == "add":
                    favorites_service.toggle_driver(user_id, "")  # noop trick
                    fav = favorites_service.get(user_id)
                    if not fav.has_team(matched):
                        favorites_service.toggle_team(user_id, matched)
                    name = TEAM_DISPLAY_NAMES.get(matched, matched)
                    await update.message.reply_text(
                        get_text("fav_team_added", lang, team=name)
                    )
                else:
                    fav = favorites_service.get(user_id)
                    if fav.has_team(matched):
                        favorites_service.toggle_team(user_id, matched)
                    name = TEAM_DISPLAY_NAMES.get(matched, matched)
                    await update.message.reply_text(
                        get_text("fav_team_removed", lang, team=name)
                    )
            else:
                await update.message.reply_text(
                    get_text("fav_team_not_found", lang, team=args[2])
                )
            return

        # Driver code
        code = args[1].upper()
        if action == "add":
            fav = favorites_service.get(user_id)
            if not fav.has_driver(code):
                favorites_service.toggle_driver(user_id, code)
            name = next((n for c, n in KNOWN_DRIVERS if c == code), code)
            await update.message.reply_text(
                get_text("fav_driver_added", lang, driver=f"{name} ({code})")
            )
        else:
            fav = favorites_service.get(user_id)
            if fav.has_driver(code):
                favorites_service.toggle_driver(user_id, code)
            name = next((n for c, n in KNOWN_DRIVERS if c == code), code)
            await update.message.reply_text(
                get_text("fav_driver_removed", lang, driver=f"{name} ({code})")
            )
        return

    await update.message.reply_text(get_text("fav_usage", lang))


def _match_team(query: str) -> str | None:
    """Match a partial team name/slug to a known team slug."""
    query = query.lower().replace(" ", "")
    for slug in TEAM_DISPLAY_NAMES:
        if query in slug or slug.startswith(query):
            return slug
    for slug, name in TEAM_DISPLAY_NAMES.items():
        if query in name.lower().replace(" ", ""):
            return slug
    return None


# ---------------------------------------------------------------------------
# Callback query handlers
# ---------------------------------------------------------------------------

async def _callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all favorites callback queries."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    data = query.data

    if data == CB_FAV_MENU:
        text = _build_favorites_text(user_id, lang)
        await query.edit_message_text(text, reply_markup=_main_menu_keyboard(lang))

    elif data == CB_FAV_DRIVERS:
        await query.edit_message_text(
            get_text("fav_select_drivers", lang),
            reply_markup=_drivers_keyboard(user_id, lang),
        )

    elif data == CB_FAV_TEAMS:
        await query.edit_message_text(
            get_text("fav_select_teams", lang),
            reply_markup=_teams_keyboard(user_id, lang),
        )

    elif data.startswith(CB_FAV_TOGGLE_DRIVER):
        code = data[len(CB_FAV_TOGGLE_DRIVER):]
        added = favorites_service.toggle_driver(user_id, code)
        name = next((n for c, n in KNOWN_DRIVERS if c == code), code)
        # Refresh the driver list
        await query.edit_message_text(
            get_text("fav_select_drivers", lang),
            reply_markup=_drivers_keyboard(user_id, lang),
        )

    elif data.startswith(CB_FAV_TOGGLE_TEAM):
        slug = data[len(CB_FAV_TOGGLE_TEAM):]
        added = favorites_service.toggle_team(user_id, slug)
        # Refresh the team list
        await query.edit_message_text(
            get_text("fav_select_teams", lang),
            reply_markup=_teams_keyboard(user_id, lang),
        )

    elif data == CB_FAV_CLEAR:
        await query.edit_message_text(
            get_text("fav_clear_confirm", lang),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("fav_btn_yes", lang),
                        callback_data=CB_FAV_CLEAR_CONFIRM,
                    ),
                    InlineKeyboardButton(
                        get_text("fav_btn_back", lang),
                        callback_data=CB_FAV_MENU,
                    ),
                ]
            ]),
        )

    elif data == CB_FAV_CLEAR_CONFIRM:
        favorites_service.clear(user_id)
        await query.edit_message_text(
            get_text("fav_cleared", lang),
            reply_markup=_main_menu_keyboard(lang),
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def get_handlers() -> list:
    """Return handlers for this module."""
    return [
        CommandHandler("favorites", favorites_command),
        CommandHandler("fav", fav_command),
        CallbackQueryHandler(_callback_handler, pattern=r"^fav:"),
    ]
