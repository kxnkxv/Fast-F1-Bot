"""Race result banner — podium display + top-10 results grid."""

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
#  Driver photo helpers                                                  #
# ===================================================================== #

def _prepare_photo(
    raw: bytes | None,
    size: tuple[int, int],
) -> Image.Image:
    """Resize a driver photo to *size* or produce a placeholder."""
    if raw:
        photo = _renderer.load_image_from_bytes(raw)
        photo = photo.resize(size, Image.LANCZOS)
        return photo
    # Placeholder silhouette
    ph = Image.new("RGBA", size, F1Colors.BG_CARD)
    d = ImageDraw.Draw(ph)
    cx, cy = size[0] // 2, size[1] // 2
    r = min(size) // 3
    d.ellipse([cx - r, cy - r - 10, cx + r, cy + r - 10], fill=F1Colors.TEXT_MUTED)
    d.ellipse([cx - r // 2, cy - r * 2 + 5, cx + r // 2, cy - r + 5], fill=F1Colors.TEXT_MUTED)
    return ph


def _make_circular(photo: Image.Image) -> Image.Image:
    """Crop an RGBA image into a circle using an alpha mask."""
    size = photo.size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size[0] - 1, size[1] - 1], fill=255)
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    result.paste(photo, (0, 0), mask)
    return result


# ===================================================================== #
#  Podium block                                                          #
# ===================================================================== #

def _draw_podium_driver(
    img: Image.Image,
    result,
    photo_bytes: bytes | None,
    center_x: int,
    y_top: int,
    photo_size: int,
    is_winner: bool = False,
) -> int:
    """Draw a single podium entry.  Returns the y below the block."""
    draw = ImageDraw.Draw(img)

    # Photo (circular)
    photo = _prepare_photo(photo_bytes, (photo_size, photo_size))
    photo = _make_circular(photo)

    # Team colour ring behind photo
    ring_pad = 4
    ring = Image.new("RGBA", (photo_size + ring_pad * 2, photo_size + ring_pad * 2), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse(
        [0, 0, ring.width - 1, ring.height - 1],
        fill=get_team_color(result.team_slug),
    )
    ring_x = center_x - ring.width // 2
    paste_with_alpha(img, ring, (ring_x, y_top))
    paste_with_alpha(img, photo, (ring_x + ring_pad, y_top + ring_pad))

    # Position badge
    badge_size = 40 if is_winner else 34
    draw_position_badge(img, result.position, (center_x - badge_size // 2, y_top + photo_size - badge_size // 3), badge_size)

    # Name
    name_font = font_heading(22) if is_winner else font_body(18)
    y_text = y_top + photo_size + ring_pad + 18
    bbox = draw.textbbox((0, 0), result.driver_code, font=name_font)
    tw = bbox[2] - bbox[0]
    draw_text_with_shadow(
        draw,
        (center_x - tw // 2, y_text),
        result.driver_code,
        name_font,
        F1Colors.TEXT,
    )

    # Driver full name (smaller)
    small_font = font_caption(14)
    short_name = result.driver_name
    bbox2 = draw.textbbox((0, 0), short_name, font=small_font)
    tw2 = bbox2[2] - bbox2[0]
    y_text += 26
    draw.text((center_x - tw2 // 2, y_text), short_name, font=small_font, fill=F1Colors.TEXT_SECONDARY)

    # Time / gap
    time_font = font_caption(14)
    time_text = result.time or ""
    bbox3 = draw.textbbox((0, 0), time_text, font=time_font)
    tw3 = bbox3[2] - bbox3[0]
    y_text += 20
    draw.text((center_x - tw3 // 2, y_text), time_text, font=time_font, fill=F1Colors.TEXT_MUTED)

    return y_text + 20


# ===================================================================== #
#  Results list (P4–P10)                                                 #
# ===================================================================== #

def _draw_results_list(
    img: Image.Image,
    results,
    y_start: int,
    favorite_drivers: set[str] | None = None,
) -> None:
    """Compact table for positions 4 through 10."""
    draw = ImageDraw.Draw(img)
    pos_font = font_body(16)
    name_font = font_body(16)
    detail_font = font_caption(14)
    row_h = 32
    margin_l = 48
    col_gap = img.width - margin_l * 2

    for i, res in enumerate(results):
        y = y_start + i * row_h

        # Background row (alternating)
        if i % 2 == 0:
            draw_rounded_rect(draw, (margin_l - 8, y - 2, img.width - margin_l + 8, y + row_h - 4), fill=F1Colors.BG_SURFACE, radius=4)

        # Team stripe
        draw_team_stripe(draw, margin_l, y + 2, row_h - 8, res.team_slug, width=3)

        # Position
        pos_text = f"{res.position}"
        draw.text((margin_l + 12, y + 4), pos_text, font=pos_font, fill=F1Colors.TEXT_SECONDARY)

        # Driver code (★ if favorite)
        is_fav = favorite_drivers and res.driver_code in favorite_drivers
        code_label = f"★ {res.driver_code}" if is_fav else res.driver_code
        code_color = "#FFD700" if is_fav else F1Colors.TEXT
        draw.text((margin_l + 50, y + 4), code_label, font=name_font, fill=code_color)

        # Driver name
        name_x = margin_l + (130 if is_fav else 110)
        draw.text((name_x, y + 4), res.driver_name, font=detail_font, fill=F1Colors.TEXT_SECONDARY)

        # Gap
        gap_text = res.gap or res.time or ""
        bbox = draw.textbbox((0, 0), gap_text, font=detail_font)
        gw = bbox[2] - bbox[0]
        draw.text((img.width - margin_l - gw, y + 4), gap_text, font=detail_font, fill=F1Colors.TEXT_MUTED)

        # Points
        if res.points > 0:
            pts = f"+{res.points:g} pts"
            pbbox = draw.textbbox((0, 0), pts, font=detail_font)
            pw = pbbox[2] - pbbox[0]
            draw.text((img.width - margin_l - gw - pw - 20, y + 4), pts, font=detail_font, fill=F1Colors.GREEN)

        # Fastest lap indicator
        if res.fastest_lap:
            fl_text = "FL"
            draw.text((img.width - margin_l - gw - 60, y + 4), fl_text, font=detail_font, fill=F1Colors.FASTEST_LAP)


# ===================================================================== #
#  Public API                                                            #
# ===================================================================== #

def render_race_result(
    result: SessionResult,
    driver_photos: dict[str, bytes] | None = None,
    favorite_drivers: set[str] | None = None,
) -> BytesIO:
    """Render a race result banner and return it as a PNG BytesIO.

    Parameters
    ----------
    result:
        Parsed session result containing at least the top‑10 drivers.
    driver_photos:
        Mapping of driver code → raw image bytes.  Missing entries
        produce placeholder silhouettes.
    favorite_drivers:
        Set of driver codes that should be highlighted with ★.
    """
    if driver_photos is None:
        driver_photos = {}
    if favorite_drivers is None:
        favorite_drivers = set()

    img = _renderer.create_base("race_result")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Background gradient
    draw_gradient(draw, (0, 0, W, H), F1Colors.BG_DARK, "#0A0A12", direction="vertical")

    # Header
    header_h = _renderer.add_header(
        img,
        f"{result.event_name}",
        f"{result.session_type}  •  {result.year}",
    )

    sorted_results = sorted(result.results, key=lambda r: r.position)

    # --- Podium ---
    if len(sorted_results) >= 3:
        podium = sorted_results[:3]
        podium_y = header_h + 8

        # P2 — left
        p2_cx = W // 4
        _draw_podium_driver(
            img, podium[1], driver_photos.get(podium[1].driver_code),
            p2_cx, podium_y + 22, 90,
        )

        # P1 — centre (larger, raised)
        p1_cx = W // 2
        bottom_y = _draw_podium_driver(
            img, podium[0], driver_photos.get(podium[0].driver_code),
            p1_cx, podium_y, 110, is_winner=True,
        )

        # P3 — right
        p3_cx = W * 3 // 4
        _draw_podium_driver(
            img, podium[2], driver_photos.get(podium[2].driver_code),
            p3_cx, podium_y + 22, 90,
        )
    else:
        bottom_y = header_h + 10

    # --- Divider ---
    divider_y = max(bottom_y + 4, header_h + 260)
    draw.line([(40, divider_y), (W - 40, divider_y)], fill=F1Colors.BG_CARD, width=1)

    # --- P4–P10 list ---
    rest = [r for r in sorted_results[3:10]]
    if rest:
        _draw_results_list(img, rest, divider_y + 8, favorite_drivers)

    # Footer branding line
    ft_font = font_caption(12)
    draw.text((W - 160, H - 20), "F1 Bot  •  Formula 1", font=ft_font, fill=F1Colors.TEXT_MUTED)

    return _renderer.to_bytes(img)
