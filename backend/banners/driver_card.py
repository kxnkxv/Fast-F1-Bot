"""Driver profile card — portrait layout with photo, stats, and team branding."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from backend.models.schemas import DriverProfile

from .components import (
    draw_gradient,
    draw_rounded_rect,
    draw_stat_box,
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
#  Photo helpers                                                         #
# ===================================================================== #

def _prepare_driver_photo(raw: bytes | None, width: int, height: int) -> Image.Image:
    """Resize a driver headshot or create a placeholder silhouette."""
    if raw:
        photo = _renderer.load_image_from_bytes(raw)
        photo = photo.resize((width, height), Image.LANCZOS)
        return photo

    ph = Image.new("RGBA", (width, height), F1Colors.BG_SURFACE)
    d = ImageDraw.Draw(ph)
    cx, cy = width // 2, height // 2
    head_r = min(width, height) // 5
    d.ellipse([cx - head_r, cy - head_r * 2, cx + head_r, cy], fill=F1Colors.TEXT_MUTED)
    body_r = head_r * 2
    d.ellipse([cx - body_r, cy + 4, cx + body_r, cy + body_r * 2], fill=F1Colors.TEXT_MUTED)
    return ph


def _prepare_car_image(raw: bytes | None, width: int, height: int) -> Image.Image | None:
    """Resize a team car image if available."""
    if not raw:
        return None
    car = _renderer.load_image_from_bytes(raw)
    car = car.resize((width, height), Image.LANCZOS)
    return car


# ===================================================================== #
#  Drawing                                                               #
# ===================================================================== #

def render_driver_card(
    profile: DriverProfile,
    photo: bytes | None = None,
    car: bytes | None = None,
) -> BytesIO:
    """Render an 800x1000 driver profile card as a PNG BytesIO.

    Parameters
    ----------
    profile:
        Driver metadata and season stats.
    photo:
        Raw bytes for the driver headshot (PNG/JPEG).
    car:
        Raw bytes for the team car render.
    """
    img = _renderer.create_base("driver_card")
    draw = ImageDraw.Draw(img)
    W, H = img.size
    team_color = get_team_color(profile.team_slug)

    # ---- Background ---- #
    draw_gradient(draw, (0, 0, W, H), F1Colors.BG_DARK, "#0A0A12", direction="vertical")

    # Team colour accent bar at top
    draw.rectangle([0, 0, W, 6], fill=team_color)

    # Subtle team colour glow behind photo area
    glow = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    from .components import _hex_to_rgba  # local import to avoid circular at module level

    tc_rgba = _hex_to_rgba(team_color, 35)
    for row in range(300):
        alpha = int(35 * (1 - row / 300))
        c = (*tc_rgba[:3], alpha)
        gd.line([(0, row), (W, row)], fill=c)
    paste_with_alpha(img, glow, (0, 0))

    # ---- Driver photo ---- #
    photo_w, photo_h = 280, 320
    photo_img = _prepare_driver_photo(photo, photo_w, photo_h)
    photo_x = (W - photo_w) // 2
    photo_y = 30

    # Clip photo with rounded corners
    mask = Image.new("L", (photo_w, photo_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, photo_w - 1, photo_h - 1], radius=20, fill=255)
    clipped = Image.new("RGBA", (photo_w, photo_h), (0, 0, 0, 0))
    clipped.paste(photo_img, (0, 0), mask)

    paste_with_alpha(img, clipped, (photo_x, photo_y))

    # Team colour border at bottom of photo
    draw.rectangle([photo_x, photo_y + photo_h, photo_x + photo_w, photo_y + photo_h + 4], fill=team_color)

    # ---- Driver number (large, faded, behind name area) ---- #
    if profile.number is not None:
        num_font = load_font(120, "bold")
        num_text = str(profile.number)
        nbbox = draw.textbbox((0, 0), num_text, font=num_font)
        nw = nbbox[2] - nbbox[0]
        draw.text(
            (W - nw - 30, photo_y + photo_h - 50),
            num_text,
            font=num_font,
            fill=(*_hex_to_rgba(F1Colors.BG_DARK)[:3], 80),
        )

    # ---- Name block ---- #
    y_cursor = photo_y + photo_h + 24

    # First name (lighter)
    first_font = font_heading(24)
    draw.text((50, y_cursor), profile.first_name.upper(), font=first_font, fill=F1Colors.TEXT_SECONDARY)
    fbbox = draw.textbbox((0, 0), profile.first_name.upper(), font=first_font)
    y_cursor += fbbox[3] - fbbox[1] + 2

    # Last name (bold, large)
    last_font = font_title(40)
    draw_text_with_shadow(draw, (50, y_cursor), profile.last_name.upper(), last_font, F1Colors.TEXT)
    lbbox = draw.textbbox((0, 0), profile.last_name.upper(), font=last_font)
    y_cursor += lbbox[3] - lbbox[1] + 8

    # Team name in team colour
    team_font = font_body(18)
    draw.text((50, y_cursor), profile.team, font=team_font, fill=team_color)
    y_cursor += 28

    # Country
    if profile.country:
        country_font = font_caption(15)
        draw.text((50, y_cursor), profile.country, font=country_font, fill=F1Colors.TEXT_MUTED)
        y_cursor += 24

    # Driver number (compact, beside name)
    if profile.number is not None:
        num_compact_font = font_heading(22)
        num_label = f"#{profile.number}"
        nlbbox = draw.textbbox((0, 0), num_label, font=num_compact_font)
        nlw = nlbbox[2] - nlbbox[0]
        draw.text((W - nlw - 50, photo_y + photo_h + 28), num_label, font=num_compact_font, fill=team_color)

    # ---- Stats grid ---- #
    y_cursor += 16
    draw.line([(50, y_cursor), (W - 50, y_cursor)], fill=F1Colors.BG_CARD, width=1)
    y_cursor += 20

    stat_w, stat_h = 155, 76
    gap = (W - 100 - stat_w * 4) // 3
    stats = [
        ("Points", f"{profile.season_points:g}"),
        ("Wins", str(profile.season_wins)),
        ("Podiums", str(profile.season_podiums)),
        ("Position", f"P{profile.season_position}" if profile.season_position else "—"),
    ]

    for i, (label, value) in enumerate(stats):
        sx = 50 + i * (stat_w + gap)
        draw_stat_box(img, (sx, y_cursor), (stat_w, stat_h), label, value, accent_color=team_color)

    y_cursor += stat_h + 20

    # ---- Team car ---- #
    car_img = _prepare_car_image(car, W - 100, 140)
    if car_img is not None:
        car_y = max(y_cursor, H - 170)
        paste_with_alpha(img, car_img, (50, car_y))

    # Footer
    ft_font = font_caption(12)
    draw.text((W - 160, H - 20), "F1 Bot  •  Formula 1", font=ft_font, fill=F1Colors.TEXT_MUTED)

    return _renderer.to_bytes(img)
