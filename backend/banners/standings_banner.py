"""Championship standings banner — drivers or constructors top-10 bar chart."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from backend.models.schemas import StandingsResponse

from .components import (
    draw_gradient,
    draw_progress_bar,
    draw_rounded_rect,
    draw_team_stripe,
    draw_text_with_shadow,
    paste_with_alpha,
)
from .design_system import (
    F1Colors,
    get_team_color,
    load_font,
    font_title,
    font_heading,
    font_body,
    font_caption,
)
from .renderer import BannerRenderer

_renderer = BannerRenderer()


# ===================================================================== #
#  Row renderers                                                         #
# ===================================================================== #

def _draw_driver_row(
    img: Image.Image,
    entry,
    y: int,
    max_points: float,
    row_index: int,
) -> None:
    """Draw a single driver standings row with progress bar."""
    draw = ImageDraw.Draw(img)
    W = img.width
    margin = 48
    row_h = 56

    # Card background
    card_y = y
    draw_rounded_rect(
        draw,
        (margin - 8, card_y, W - margin + 8, card_y + row_h),
        fill=F1Colors.BG_SURFACE if row_index % 2 == 0 else F1Colors.BG_DARK,
        radius=6,
    )

    team_color = get_team_color(entry.team_slug)

    # Team stripe
    draw_team_stripe(draw, margin, card_y + 8, row_h - 16, entry.team_slug, width=4)

    # Position
    pos_font = font_heading(22)
    pos_text = str(entry.position)
    pos_colors = {1: F1Colors.GOLD, 2: F1Colors.SILVER, 3: F1Colors.BRONZE}
    pos_color = pos_colors.get(entry.position, F1Colors.TEXT_SECONDARY)
    draw.text((margin + 16, card_y + 14), pos_text, font=pos_font, fill=pos_color)

    # Driver code
    code_font = font_heading(20)
    draw.text((margin + 56, card_y + 15), entry.driver_code, font=code_font, fill=F1Colors.TEXT)

    # Full name
    name_font = font_caption(14)
    draw.text((margin + 56, card_y + 38), entry.driver_name, font=name_font, fill=F1Colors.TEXT_MUTED)

    # Team
    team_font = font_caption(13)
    draw.text((margin + 200, card_y + 38), entry.team, font=team_font, fill=team_color)

    # Progress bar
    bar_x = margin + 350
    bar_w = W - margin - bar_x - 120
    bar_y = card_y + 18
    bar_h = 16
    ratio = entry.points / max_points if max_points > 0 else 0
    draw_progress_bar(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), ratio, team_color)

    # Points (numeric, right-aligned)
    pts_font = font_heading(20)
    pts_text = f"{entry.points:g}"
    pbbox = draw.textbbox((0, 0), pts_text, font=pts_font)
    pw = pbbox[2] - pbbox[0]
    draw.text((W - margin - pw, card_y + 14), pts_text, font=pts_font, fill=F1Colors.TEXT)

    # Wins badge
    if entry.wins > 0:
        wins_font = font_caption(12)
        wins_text = f"{entry.wins}W"
        wbbox = draw.textbbox((0, 0), wins_text, font=wins_font)
        ww = wbbox[2] - wbbox[0]
        draw.text((W - margin - pw - ww - 14, card_y + 18), wins_text, font=wins_font, fill=F1Colors.GREEN)


def _draw_constructor_row(
    img: Image.Image,
    entry,
    y: int,
    max_points: float,
    row_index: int,
) -> None:
    """Draw a single constructor standings row with progress bar."""
    draw = ImageDraw.Draw(img)
    W = img.width
    margin = 48
    row_h = 56

    # Card background
    card_y = y
    draw_rounded_rect(
        draw,
        (margin - 8, card_y, W - margin + 8, card_y + row_h),
        fill=F1Colors.BG_SURFACE if row_index % 2 == 0 else F1Colors.BG_DARK,
        radius=6,
    )

    team_color = get_team_color(entry.team_slug)

    # Team stripe (thicker for constructors)
    draw_team_stripe(draw, margin, card_y + 8, row_h - 16, entry.team_slug, width=6)

    # Position
    pos_font = font_heading(22)
    pos_text = str(entry.position)
    pos_colors = {1: F1Colors.GOLD, 2: F1Colors.SILVER, 3: F1Colors.BRONZE}
    pos_color = pos_colors.get(entry.position, F1Colors.TEXT_SECONDARY)
    draw.text((margin + 16, card_y + 14), pos_text, font=pos_font, fill=pos_color)

    # Team name (prominent)
    name_font = font_heading(20)
    draw.text((margin + 56, card_y + 15), entry.team, font=name_font, fill=F1Colors.TEXT)

    # Progress bar
    bar_x = margin + 350
    bar_w = W - margin - bar_x - 120
    bar_y = card_y + 18
    bar_h = 18
    ratio = entry.points / max_points if max_points > 0 else 0
    draw_progress_bar(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), ratio, team_color)

    # Points (numeric, right-aligned)
    pts_font = font_heading(20)
    pts_text = f"{entry.points:g}"
    pbbox = draw.textbbox((0, 0), pts_text, font=pts_font)
    pw = pbbox[2] - pbbox[0]
    draw.text((W - margin - pw, card_y + 14), pts_text, font=pts_font, fill=F1Colors.TEXT)

    # Wins badge
    if entry.wins > 0:
        wins_font = font_caption(12)
        wins_text = f"{entry.wins}W"
        wbbox = draw.textbbox((0, 0), wins_text, font=wins_font)
        ww = wbbox[2] - wbbox[0]
        draw.text((W - margin - pw - ww - 14, card_y + 18), wins_text, font=wins_font, fill=F1Colors.GREEN)


# ===================================================================== #
#  Leader highlight                                                      #
# ===================================================================== #

def _draw_leader_highlight(
    img: Image.Image,
    name: str,
    points: float,
    team_color: str,
    y: int,
    label: str = "CHAMPIONSHIP LEADER",
) -> int:
    """Draw a prominent leader block.  Returns y below it."""
    draw = ImageDraw.Draw(img)
    W = img.width
    margin = 48
    card_h = 70

    draw_rounded_rect(
        draw,
        (margin - 8, y, W - margin + 8, y + card_h),
        fill=F1Colors.BG_SURFACE,
        radius=10,
    )
    # Team accent left edge
    draw.rectangle([margin - 8, y, margin, y + card_h], fill=team_color)

    # Label
    lbl_font = font_caption(13)
    draw.text((margin + 14, y + 8), label, font=lbl_font, fill=F1Colors.TEXT_MUTED)

    # Name
    name_font = font_heading(26)
    draw_text_with_shadow(draw, (margin + 14, y + 26), name.upper(), name_font, F1Colors.TEXT)

    # Points
    pts_font = font_title(32)
    pts_text = f"{points:g} PTS"
    pbbox = draw.textbbox((0, 0), pts_text, font=pts_font)
    pw = pbbox[2] - pbbox[0]
    draw.text((W - margin - pw - 16, y + 18), pts_text, font=pts_font, fill=team_color)

    return y + card_h + 12


# ===================================================================== #
#  Public API                                                            #
# ===================================================================== #

def render_standings(
    standings: StandingsResponse,
    mode: str = "drivers",
    favorite_drivers: set[str] | None = None,
    favorite_teams: set[str] | None = None,
) -> BytesIO:
    """Render a championship standings banner as a PNG BytesIO.

    Parameters
    ----------
    standings:
        Full standings data (drivers + constructors lists).
    mode:
        ``"drivers"`` or ``"constructors"``.
    """
    img = _renderer.create_base("standings")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Background
    draw_gradient(draw, (0, 0, W, H), F1Colors.BG_DARK, "#0C0C16", direction="vertical")

    is_drivers = mode == "drivers"
    title = f"{standings.year} Drivers' Championship" if is_drivers else f"{standings.year} Constructors' Championship"

    header_h = _renderer.add_header(img, title)
    y_cursor = header_h + 8

    if is_drivers:
        entries = sorted(standings.drivers, key=lambda e: e.position)[:10]
        max_pts = entries[0].points if entries else 1

        # Leader highlight
        if entries:
            leader = entries[0]
            y_cursor = _draw_leader_highlight(
                img,
                leader.driver_name,
                leader.points,
                get_team_color(leader.team_slug),
                y_cursor,
            )

        # Rows
        row_h = 56
        for i, entry in enumerate(entries):
            _draw_driver_row(img, entry, y_cursor + i * row_h, max_pts, i)
    else:
        entries = sorted(standings.constructors, key=lambda e: e.position)[:10]
        max_pts = entries[0].points if entries else 1

        # Leader highlight
        if entries:
            leader = entries[0]
            y_cursor = _draw_leader_highlight(
                img,
                leader.team,
                leader.points,
                get_team_color(leader.team_slug),
                y_cursor,
                label="LEADING CONSTRUCTOR",
            )

        # Rows
        row_h = 56
        for i, entry in enumerate(entries):
            _draw_constructor_row(img, entry, y_cursor + i * row_h, max_pts, i)

    # Footer
    ft_font = font_caption(12)
    draw.text((W - 160, H - 20), "F1 Bot  •  Formula 1", font=ft_font, fill=F1Colors.TEXT_MUTED)

    return _renderer.to_bytes(img)
