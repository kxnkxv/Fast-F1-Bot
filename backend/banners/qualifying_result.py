"""Qualifying result banner — pole sitter feature + grid list."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from backend.models.schemas import SessionResult

from .components import (
    draw_gradient,
    draw_position_badge,
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
#  Helpers                                                                #
# ===================================================================== #

def _prepare_circular_photo(raw: bytes | None, size: int) -> Image.Image:
    """Load driver photo as a circle, or create placeholder."""
    if raw:
        photo = _renderer.load_image_from_bytes(raw)
    else:
        photo = Image.new("RGBA", (size, size), F1Colors.BG_CARD)
        d = ImageDraw.Draw(photo)
        cx, cy = size // 2, size // 2
        r = size // 3
        d.ellipse([cx - r, cy - r - 6, cx + r, cy + r - 6], fill=F1Colors.TEXT_MUTED)
        d.ellipse([cx - r // 2, cy - r * 2 + 4, cx + r // 2, cy - r + 4], fill=F1Colors.TEXT_MUTED)

    photo = photo.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(photo, (0, 0), mask)
    return out


# ===================================================================== #
#  Pole sitter feature block                                             #
# ===================================================================== #

def _draw_pole_sitter(
    img: Image.Image,
    result,
    photo_bytes: bytes | None,
    y_start: int,
) -> int:
    """Draw the pole sitter prominently.  Returns y below the block."""
    draw = ImageDraw.Draw(img)
    W = img.width

    # Card background
    card_x, card_y = 40, y_start
    card_w, card_h = W - 80, 200
    draw_rounded_rect(draw, (card_x, card_y, card_x + card_w, card_y + card_h), fill=F1Colors.BG_SURFACE, radius=16)

    # Team colour accent on left edge
    team_color = get_team_color(result.team_slug)
    draw.rectangle([card_x, card_y, card_x + 6, card_y + card_h], fill=team_color)

    # Photo
    photo_size = 130
    photo = _prepare_circular_photo(photo_bytes, photo_size)

    # Team ring
    ring_pad = 4
    ring = Image.new("RGBA", (photo_size + ring_pad * 2, photo_size + ring_pad * 2), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse([0, 0, ring.width - 1, ring.height - 1], fill=team_color)

    ring_x = card_x + 30
    ring_y = card_y + (card_h - ring.height) // 2
    paste_with_alpha(img, ring, (ring_x, ring_y))
    paste_with_alpha(img, photo, (ring_x + ring_pad, ring_y + ring_pad))

    # "POLE POSITION" label
    label_font = font_caption(14)
    label_x = ring_x + ring.width + 28
    label_y = card_y + 28
    draw.text((label_x, label_y), "POLE POSITION", font=label_font, fill=F1Colors.GOLD)

    # Driver name
    name_font = font_title(34)
    draw_text_with_shadow(draw, (label_x, label_y + 22), result.driver_name.upper(), name_font, F1Colors.TEXT)

    # Team
    team_font = font_body(18)
    draw.text((label_x, label_y + 62), result.team, font=team_font, fill=team_color)

    # Lap time
    time_text = result.time or "—"
    time_font = font_heading(28)
    bbox = draw.textbbox((0, 0), time_text, font=time_font)
    tw = bbox[2] - bbox[0]
    time_x = card_x + card_w - tw - 40
    time_y = card_y + card_h // 2 - 14
    draw_text_with_shadow(draw, (time_x, time_y), time_text, time_font, F1Colors.TEXT)

    # Position badge
    draw_position_badge(img, 1, (time_x - 58, time_y - 4), 48)

    return card_y + card_h + 12


# ===================================================================== #
#  Grid list                                                             #
# ===================================================================== #

def _draw_grid_row(
    img: Image.Image,
    result,
    y: int,
    row_index: int,
) -> None:
    """Draw a single grid row for positions 2+."""
    draw = ImageDraw.Draw(img)
    W = img.width
    margin = 48
    row_h = 34

    # Alternating background
    if row_index % 2 == 0:
        draw_rounded_rect(
            draw,
            (margin - 8, y, W - margin + 8, y + row_h),
            fill=F1Colors.BG_SURFACE,
            radius=4,
        )

    # Team stripe
    draw_team_stripe(draw, margin, y + 4, row_h - 8, result.team_slug, width=3)

    pos_font = font_body(16)
    name_font = font_body(16)
    detail_font = font_caption(14)

    # Position
    pos_text = f"P{result.position}"
    pos_color = {2: F1Colors.SILVER, 3: F1Colors.BRONZE}.get(result.position, F1Colors.TEXT_SECONDARY)
    draw.text((margin + 12, y + 6), pos_text, font=pos_font, fill=pos_color)

    # Driver code
    draw.text((margin + 65, y + 6), result.driver_code, font=name_font, fill=F1Colors.TEXT)

    # Full name
    draw.text((margin + 125, y + 6), result.driver_name, font=detail_font, fill=F1Colors.TEXT_SECONDARY)

    # Time / gap
    time_text = result.gap if result.position > 1 and result.gap else (result.time or "—")
    tbbox = draw.textbbox((0, 0), time_text, font=detail_font)
    tw = tbbox[2] - tbbox[0]
    draw.text((W - margin - tw, y + 6), time_text, font=detail_font, fill=F1Colors.TEXT_MUTED)


# ===================================================================== #
#  Public API                                                            #
# ===================================================================== #

def render_qualifying_result(
    result: SessionResult,
    driver_photos: dict[str, bytes] | None = None,
) -> BytesIO:
    """Render a qualifying banner and return it as a PNG BytesIO.

    Parameters
    ----------
    result:
        Qualifying session result.
    driver_photos:
        Mapping of driver code to raw photo bytes.
    """
    if driver_photos is None:
        driver_photos = {}

    img = _renderer.create_base("qualifying")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Background gradient
    draw_gradient(draw, (0, 0, W, H), F1Colors.BG_DARK, "#0C0C16", direction="vertical")

    # Header
    header_h = _renderer.add_header(
        img,
        result.event_name,
        f"Qualifying  •  {result.year}",
    )

    sorted_results = sorted(result.results, key=lambda r: r.position)

    # Pole sitter
    y_cursor = header_h + 6
    if sorted_results:
        pole = sorted_results[0]
        y_cursor = _draw_pole_sitter(
            img, pole, driver_photos.get(pole.driver_code), y_cursor,
        )

    # Grid rows (P2–P10)
    row_h = 34
    for i, res in enumerate(sorted_results[1:10]):
        _draw_grid_row(img, res, y_cursor + i * row_h, i)

    # Footer
    ft_font = font_caption(12)
    draw.text((W - 160, H - 20), "F1 Bot  •  Formula 1", font=ft_font, fill=F1Colors.TEXT_MUTED)

    return _renderer.to_bytes(img)
