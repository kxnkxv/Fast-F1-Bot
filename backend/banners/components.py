"""Reusable drawing primitives for F1 banners."""

from __future__ import annotations

from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

from .design_system import (
    F1Colors,
    get_team_color,
    load_font,
    font_title,
    font_heading,
    font_body,
)


# ===================================================================== #
#  Colour helpers                                                        #
# ===================================================================== #

def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """Convert a hex colour string to an RGBA tuple."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, alpha)


def _lerp_color(
    c1: tuple[int, ...], c2: tuple[int, ...], t: float
) -> tuple[int, ...]:
    """Linearly interpolate between two colour tuples."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ===================================================================== #
#  Gradient fill                                                         #
# ===================================================================== #

def draw_gradient(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    color_start: str,
    color_end: str,
    direction: str = "vertical",
) -> None:
    """Fill *box* with a linear gradient between two hex colours.

    Parameters
    ----------
    direction:
        ``"vertical"`` (top→bottom) or ``"horizontal"`` (left→right).
    """
    x0, y0, x1, y1 = box
    c1 = _hex_to_rgba(color_start)
    c2 = _hex_to_rgba(color_end)

    if direction == "vertical":
        span = max(y1 - y0, 1)
        for y in range(y0, y1):
            t = (y - y0) / span
            fill = _lerp_color(c1, c2, t)
            draw.line([(x0, y), (x1, y)], fill=fill)
    else:
        span = max(x1 - x0, 1)
        for x in range(x0, x1):
            t = (x - x0) / span
            fill = _lerp_color(c1, c2, t)
            draw.line([(x, y0), (x, y1)], fill=fill)


# ===================================================================== #
#  Rounded rectangle                                                     #
# ===================================================================== #

def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str | tuple[int, ...],
    radius: int = 12,
    outline: str | tuple[int, ...] | None = None,
    outline_width: int = 1,
) -> None:
    """Draw a rectangle with rounded corners.

    Uses Pillow's built‑in ``rounded_rectangle`` when available (10.x+),
    otherwise falls back to a manual arc‑based approach.
    """
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=outline_width)
    else:
        # Manual fallback for older Pillow
        x0, y0, x1, y1 = box
        d = radius * 2
        draw.pieslice([x0, y0, x0 + d, y0 + d], 180, 270, fill=fill)
        draw.pieslice([x1 - d, y0, x1, y0 + d], 270, 360, fill=fill)
        draw.pieslice([x0, y1 - d, x0 + d, y1], 90, 180, fill=fill)
        draw.pieslice([x1 - d, y1 - d, x1, y1], 0, 90, fill=fill)
        draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
        draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)


# ===================================================================== #
#  Team colour stripe                                                    #
# ===================================================================== #

def draw_team_stripe(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    height: int,
    team_slug: str,
    width: int = 4,
) -> None:
    """Draw a thin vertical stripe in the team's brand colour."""
    color = get_team_color(team_slug)
    draw.rectangle([x, y, x + width, y + height], fill=color)


# ===================================================================== #
#  Text with drop shadow                                                 #
# ===================================================================== #

def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str | tuple[int, ...] = F1Colors.TEXT,
    shadow_color: str | tuple[int, ...] = "#000000",
    shadow_offset: tuple[int, int] = (2, 2),
) -> None:
    """Render *text* with a simple drop shadow for depth."""
    sx, sy = xy[0] + shadow_offset[0], xy[1] + shadow_offset[1]
    draw.text((sx, sy), text, font=font, fill=shadow_color)
    draw.text(xy, text, font=font, fill=fill)


# ===================================================================== #
#  Position badge (P1 gold / P2 silver / P3 bronze)                      #
# ===================================================================== #

_PODIUM_COLORS: dict[int, str] = {
    1: F1Colors.GOLD,
    2: F1Colors.SILVER,
    3: F1Colors.BRONZE,
}


def draw_position_badge(
    img: Image.Image,
    position: int,
    xy: tuple[int, int],
    size: int = 48,
) -> None:
    """Draw a circular position badge (gold/silver/bronze for P1–P3)."""
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)

    bg_color = _PODIUM_COLORS.get(position, F1Colors.BG_CARD)
    text_color = "#000000" if position <= 3 else F1Colors.TEXT

    # Circle
    bd.ellipse([0, 0, size - 1, size - 1], fill=bg_color)

    # Position text
    font_size = max(size // 3, 10)
    fnt = load_font(font_size, "bold")
    label = f"P{position}"
    bbox = bd.textbbox((0, 0), label, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - bbox[1]  # compensate for font ascent offset
    bd.text((tx, ty), label, font=fnt, fill=text_color)

    paste_with_alpha(img, badge, xy)


# ===================================================================== #
#  Alpha‑aware composite                                                 #
# ===================================================================== #

def paste_with_alpha(
    base: Image.Image,
    overlay: Image.Image,
    position: tuple[int, int],
) -> None:
    """Paste *overlay* onto *base* at *position*, respecting alpha."""
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    base.paste(overlay, position, overlay)


# ===================================================================== #
#  Standard F1 header strip                                              #
# ===================================================================== #

def create_f1_header(
    width: int,
    title: str,
    subtitle: str | None = None,
    height: int | None = None,
) -> Image.Image:
    """Return an RGBA image containing the standard F1 header.

    Layout:
    - 5 px red accent bar at the very top
    - Title text in bold white
    - Optional subtitle in secondary colour
    """
    title_font = font_title(36)
    sub_font = font_body(20)

    # Compute height if not specified
    if height is None:
        h = 5 + 20 + 36 + 10  # red bar + padding + title line‑height + padding
        if subtitle:
            h += 24 + 8
        height = h + 10

    header = Image.new("RGBA", (width, height), _hex_to_rgba(F1Colors.BG_DARK))
    hd = ImageDraw.Draw(header)

    # Red accent bar
    hd.rectangle([0, 0, width, 5], fill=F1Colors.RED)

    # Title
    y_cursor = 18
    draw_text_with_shadow(hd, (32, y_cursor), title.upper(), title_font, F1Colors.TEXT, "#000000", (2, 2))

    # Subtitle
    if subtitle:
        bbox = hd.textbbox((0, 0), title.upper(), font=title_font)
        y_cursor += bbox[3] - bbox[1] + 8
        hd.text((32, y_cursor), subtitle, font=sub_font, fill=F1Colors.TEXT_SECONDARY)

    return header


# ===================================================================== #
#  Misc helpers                                                          #
# ===================================================================== #

def draw_divider(
    draw: ImageDraw.ImageDraw,
    y: int,
    width: int,
    color: str = F1Colors.BG_CARD,
    margin: int = 32,
) -> None:
    """Draw a thin horizontal divider line."""
    draw.line([(margin, y), (width - margin, y)], fill=color, width=1)


def draw_stat_box(
    img: Image.Image,
    xy: tuple[int, int],
    size: tuple[int, int],
    label: str,
    value: str,
    accent_color: str = F1Colors.RED,
) -> None:
    """Draw a small stat card (label + value) inside a rounded box."""
    box_img = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(box_img)

    draw_rounded_rect(bd, (0, 0, size[0] - 1, size[1] - 1), fill=F1Colors.BG_CARD, radius=8)

    # Accent bar at top of box
    bd.rectangle([0, 0, size[0] - 1, 3], fill=accent_color)

    val_font = load_font(28, "bold")
    lbl_font = load_font(13, "regular")

    # Value (centered)
    vbox = bd.textbbox((0, 0), value, font=val_font)
    vw = vbox[2] - vbox[0]
    bd.text(((size[0] - vw) // 2, 14), value, font=val_font, fill=F1Colors.TEXT)

    # Label (centered, below value)
    lbox = bd.textbbox((0, 0), label, font=lbl_font)
    lw = lbox[2] - lbox[0]
    bd.text(((size[0] - lw) // 2, 50), label.upper(), font=lbl_font, fill=F1Colors.TEXT_SECONDARY)

    paste_with_alpha(img, box_img, xy)


def draw_progress_bar(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    ratio: float,
    fill_color: str,
    bg_color: str = F1Colors.BG_CARD,
    radius: int = 4,
) -> None:
    """Draw a horizontal progress bar filled to *ratio* (0.0–1.0)."""
    x0, y0, x1, y1 = box
    draw_rounded_rect(draw, (x0, y0, x1, y1), fill=bg_color, radius=radius)
    fill_width = int((x1 - x0) * min(max(ratio, 0), 1))
    if fill_width > 0:
        draw_rounded_rect(
            draw,
            (x0, y0, x0 + fill_width, y1),
            fill=fill_color,
            radius=radius,
        )
