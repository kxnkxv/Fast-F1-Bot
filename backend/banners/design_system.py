"""F1 Banner Design System — colours, team palette, typography, and sizing."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_FONTS_DIR = _ASSETS_DIR / "fonts"


# ===================================================================== #
#  Colour palette                                                        #
# ===================================================================== #
class F1Colors:
    """Core brand / UI colours used across every banner."""

    RED = "#E10600"
    BG_DARK = "#15151E"
    BG_SURFACE = "#1F1F2E"
    BG_CARD = "#2A2A3C"
    TEXT = "#FFFFFF"
    TEXT_SECONDARY = "#A0A0A0"
    TEXT_MUTED = "#666666"
    GOLD = "#FFD700"
    SILVER = "#C0C0C0"
    BRONZE = "#CD7F32"
    GREEN = "#00D747"
    FASTEST_LAP = "#A855F7"


TEAM_COLORS: dict[str, str] = {
    "mercedes": "#27F4D2",
    "ferrari": "#E8002D",
    "mclaren": "#FF8000",
    "redbullracing": "#3671C6",
    "astonmartin": "#006F62",
    "alpine": "#0090FF",
    "williams": "#005AFF",
    "rb": "#6692FF",
    "kicksauber": "#52E252",
    "haasf1team": "#B6BABD",
}

# Fallback if a team slug is not found
_DEFAULT_TEAM_COLOR = "#888888"


def get_team_color(team_slug: str) -> str:
    """Return the hex colour for a team, with a safe fallback."""
    return TEAM_COLORS.get(team_slug, _DEFAULT_TEAM_COLOR)


# ===================================================================== #
#  Banner sizes                                                          #
# ===================================================================== #
BANNER_SIZES: dict[str, tuple[int, int]] = {
    "race_result": (1200, 630),
    "qualifying": (1200, 630),
    "next_race": (1200, 630),
    "driver_card": (800, 1000),
    "standings": (1200, 800),
}


# ===================================================================== #
#  Font loading                                                          #
# ===================================================================== #

# The preferred font family shipped with the project
_PREFERRED_FONTS = [
    "TitilliumWeb-Bold.ttf",
    "TitilliumWeb-SemiBold.ttf",
    "TitilliumWeb-Regular.ttf",
    "TitilliumWeb-Light.ttf",
]

# System‐wide fallback candidates (order of preference)
_FALLBACK_FONT_NAMES = [
    "DejaVuSans-Bold.ttf",
    "DejaVuSans.ttf",
    "Arial Bold.ttf",
    "Arial.ttf",
    "Helvetica.ttf",
    "FreeSans.ttf",
]

_FALLBACK_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype",
    "/usr/share/fonts",
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    "C:\\Windows\\Fonts",
]


def _find_system_font() -> str | None:
    """Search common OS paths for a usable TrueType font file."""
    for directory in _FALLBACK_DIRS:
        if not os.path.isdir(directory):
            continue
        for name in _FALLBACK_FONT_NAMES:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                return candidate
    return None


@lru_cache(maxsize=32)
def load_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font at the requested *size* and *weight*.

    Resolution order:
    1. Titillium Web files in ``backend/banners/assets/fonts/``.
    2. Common system fonts (DejaVu Sans, Arial, Helvetica, …).
    3. Pillow's built‑in bitmap default (last resort).

    Parameters
    ----------
    size:
        Font size in pixels.
    weight:
        One of ``"bold"``, ``"semibold"``, ``"regular"``, ``"light"``.
    """
    weight_map: dict[str, str] = {
        "bold": "TitilliumWeb-Bold.ttf",
        "semibold": "TitilliumWeb-SemiBold.ttf",
        "regular": "TitilliumWeb-Regular.ttf",
        "light": "TitilliumWeb-Light.ttf",
    }

    # 1. Project-bundled font
    filename = weight_map.get(weight, "TitilliumWeb-Bold.ttf")
    font_path = _FONTS_DIR / filename
    if font_path.is_file():
        return ImageFont.truetype(str(font_path), size)

    # Also try any Titillium Web variant present
    for name in _PREFERRED_FONTS:
        candidate = _FONTS_DIR / name
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)

    # 2. System fallback
    sys_font = _find_system_font()
    if sys_font is not None:
        return ImageFont.truetype(sys_font, size)

    # 3. Ultimate fallback — Pillow default bitmap font (no sizing)
    return ImageFont.load_default()


# Convenience aliases
def font_title(size: int = 42) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_font(size, "bold")


def font_heading(size: int = 28) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_font(size, "semibold")


def font_body(size: int = 20) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_font(size, "regular")


def font_caption(size: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_font(size, "light")
