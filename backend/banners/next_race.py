"""Next race banner — event preview with session schedule."""

from __future__ import annotations

from datetime import datetime, date
from io import BytesIO

from PIL import Image, ImageDraw

from backend.models.schemas import EventInfo

from .components import (
    draw_gradient,
    draw_rounded_rect,
    draw_text_with_shadow,
    paste_with_alpha,
)
from .design_system import (
    F1Colors,
    load_font,
    font_title,
    font_heading,
    font_body,
    font_caption,
)
from .renderer import BannerRenderer

_renderer = BannerRenderer()


# ===================================================================== #
#  Session label mapping                                                 #
# ===================================================================== #

_SESSION_LABELS: dict[str, str] = {
    "fp1": "Free Practice 1",
    "fp2": "Free Practice 2",
    "fp3": "Free Practice 3",
    "qualifying": "Qualifying",
    "sprint_qualifying": "Sprint Qualifying",
    "sprint_shootout": "Sprint Shootout",
    "sprint": "Sprint",
    "race": "Race",
}

_SESSION_ORDER = ["fp1", "fp2", "fp3", "sprint_qualifying", "sprint_shootout", "sprint", "qualifying", "race"]


# ===================================================================== #
#  Countdown helper                                                      #
# ===================================================================== #

def _compute_countdown(event_date_str: str) -> str:
    """Return a human‑friendly countdown string (e.g. '5 days')."""
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return ""

    delta = (event_date - date.today()).days
    if delta < 0:
        return "Completed"
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    return f"In {delta} days"


def _format_session_time(dt_str: str | None) -> str:
    """Parse an ISO‑ish datetime string and return a friendly time."""
    if not dt_str:
        return "TBC"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%a %d %b  %H:%M")
    except (ValueError, TypeError):
        return dt_str


# ===================================================================== #
#  Drawing                                                               #
# ===================================================================== #

def _draw_countdown_badge(
    img: Image.Image,
    text: str,
    x: int,
    y: int,
) -> None:
    """Draw the countdown pill badge."""
    draw = ImageDraw.Draw(img)
    fnt = font_heading(20)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 20, 8
    pill_w, pill_h = tw + pad_x * 2, th + pad_y * 2
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    draw_rounded_rect(pd, (0, 0, pill_w - 1, pill_h - 1), fill=F1Colors.RED, radius=pill_h // 2)
    pd.text((pad_x, pad_y - bbox[1]), text.upper(), font=fnt, fill=F1Colors.TEXT)
    paste_with_alpha(img, pill, (x, y))


def _draw_session_row(
    draw: ImageDraw.ImageDraw,
    y: int,
    label: str,
    time_str: str,
    width: int,
    is_race: bool = False,
) -> None:
    """Draw one session schedule row."""
    margin = 80
    label_font = font_body(18) if is_race else font_body(16)
    time_font = font_body(16)

    label_color = F1Colors.TEXT if is_race else F1Colors.TEXT_SECONDARY
    draw.text((margin, y), label, font=label_font, fill=label_color)

    tbbox = draw.textbbox((0, 0), time_str, font=time_font)
    tw = tbbox[2] - tbbox[0]
    draw.text((width - margin - tw, y), time_str, font=time_font, fill=F1Colors.TEXT_MUTED)

    if is_race:
        # Red dot indicator
        draw.ellipse([margin - 18, y + 6, margin - 8, y + 16], fill=F1Colors.RED)


# ===================================================================== #
#  Public API                                                            #
# ===================================================================== #

def render_next_race(
    event: EventInfo,
    year: int,
) -> BytesIO:
    """Render a "next race" preview banner and return it as a PNG BytesIO.

    Parameters
    ----------
    event:
        Upcoming event metadata.
    year:
        Championship year.
    """
    img = _renderer.create_base("next_race")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Background gradient
    draw_gradient(draw, (0, 0, W, H), F1Colors.BG_DARK, "#0C0C16", direction="vertical")

    # Red accent bar at top
    draw.rectangle([0, 0, W, 5], fill=F1Colors.RED)

    # ---- Event title block ---- #
    y_cursor = 32

    # Round pill
    round_text = f"ROUND {event.round}"
    round_font = font_caption(14)
    rbbox = draw.textbbox((0, 0), round_text, font=round_font)
    rw = rbbox[2] - rbbox[0]
    draw_rounded_rect(draw, (50, y_cursor, 50 + rw + 20, y_cursor + 26), fill=F1Colors.RED, radius=13)
    draw.text((60, y_cursor + 4), round_text, font=round_font, fill=F1Colors.TEXT)

    y_cursor += 40

    # Event name (large)
    title_font = font_title(44)
    draw_text_with_shadow(
        draw, (50, y_cursor), event.name.upper(), title_font, F1Colors.TEXT,
    )
    title_bbox = draw.textbbox((0, 0), event.name.upper(), font=title_font)
    y_cursor += title_bbox[3] - title_bbox[1] + 10

    # Country + Location
    loc_font = font_body(20)
    location_text = f"{event.location}  •  {event.country}"
    draw.text((50, y_cursor), location_text, font=loc_font, fill=F1Colors.TEXT_SECONDARY)
    y_cursor += 30

    # Date
    date_font = font_body(18)
    draw.text((50, y_cursor), event.date, font=date_font, fill=F1Colors.TEXT_MUTED)

    # Countdown badge (right side)
    countdown = _compute_countdown(event.date)
    if countdown:
        _draw_countdown_badge(img, countdown, W - 250, 40)

    # ---- Divider ---- #
    y_cursor += 40
    draw.line([(50, y_cursor), (W - 50, y_cursor)], fill=F1Colors.BG_CARD, width=1)
    y_cursor += 16

    # ---- Session schedule ---- #
    schedule_title_font = font_heading(20)
    draw.text((50, y_cursor), "SESSION SCHEDULE", font=schedule_title_font, fill=F1Colors.TEXT_SECONDARY)
    y_cursor += 34

    # Sort sessions in canonical order
    ordered_keys: list[str] = []
    for key in _SESSION_ORDER:
        if key in event.sessions:
            ordered_keys.append(key)
    # Add any unknown keys at the end
    for key in event.sessions:
        if key not in ordered_keys:
            ordered_keys.append(key)

    row_h = 36
    for key in ordered_keys:
        label = _SESSION_LABELS.get(key, key.replace("_", " ").title())
        time_str = _format_session_time(event.sessions.get(key))
        is_race = key == "race"
        _draw_session_row(draw, y_cursor, label, time_str, W, is_race=is_race)
        y_cursor += row_h

    # ---- Year badge (bottom right) ---- #
    year_font = font_title(72)
    year_text = str(year)
    ybbox = draw.textbbox((0, 0), year_text, font=year_font)
    yw = ybbox[2] - ybbox[0]
    draw.text((W - yw - 50, H - 90), year_text, font=year_font, fill=F1Colors.BG_CARD)

    # Footer
    ft_font = font_caption(12)
    draw.text((W - 160, H - 20), "F1 Bot  •  Formula 1", font=ft_font, fill=F1Colors.TEXT_MUTED)

    return _renderer.to_bytes(img)
