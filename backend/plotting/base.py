"""Base plotting utilities for the F1 dark theme."""

from __future__ import annotations

from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from backend.banners.design_system import TEAM_COLORS

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Tire compound palette
# ---------------------------------------------------------------------------
COMPOUND_COLORS: dict[str, str] = {
    "SOFT": "#FF3333",
    "MEDIUM": "#FFC300",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET": "#0067FF",
}

# ---------------------------------------------------------------------------
# Dark theme constants
# ---------------------------------------------------------------------------
_BG_COLOR = "#15151E"
_SURFACE_COLOR = "#1F1F2E"
_TEXT_COLOR = "#FFFFFF"
_GRID_COLOR = "#2A2A3C"
_GRID_ALPHA = 0.6


def setup_dark_theme() -> None:
    """Configure matplotlib rcParams for the F1 dark theme."""
    plt.rcParams.update(
        {
            # Background
            "figure.facecolor": _BG_COLOR,
            "axes.facecolor": _SURFACE_COLOR,
            "savefig.facecolor": _BG_COLOR,
            # Text
            "text.color": _TEXT_COLOR,
            "axes.labelcolor": _TEXT_COLOR,
            "xtick.color": _TEXT_COLOR,
            "ytick.color": _TEXT_COLOR,
            # Grid
            "axes.grid": True,
            "grid.color": _GRID_COLOR,
            "grid.alpha": _GRID_ALPHA,
            "grid.linestyle": "--",
            "grid.linewidth": 0.5,
            # Axes edges
            "axes.edgecolor": _GRID_COLOR,
            "axes.linewidth": 0.8,
            # Legend
            "legend.facecolor": _SURFACE_COLOR,
            "legend.edgecolor": _GRID_COLOR,
            "legend.fontsize": 10,
            "legend.framealpha": 0.9,
            # Font
            "font.family": "sans-serif",
            "font.size": 11,
            # Figure layout
            "figure.autolayout": True,
        }
    )


def fig_to_buffer(fig: Figure, dpi: int = 150) -> BytesIO:
    """Render a matplotlib *fig* to a PNG BytesIO buffer, then close it."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


_DEFAULT_TEAM_COLOR = "#888888"


def get_team_color(team_slug: str) -> str:
    """Return the hex colour for a team, falling back to grey."""
    return TEAM_COLORS.get(team_slug, _DEFAULT_TEAM_COLOR)
