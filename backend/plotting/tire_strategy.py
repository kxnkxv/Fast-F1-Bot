"""Tire strategy chart — horizontal bars coloured by compound."""

from __future__ import annotations

from collections import OrderedDict
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from backend.models.schemas import StrategyResponse, TireStint
from backend.plotting.base import COMPOUND_COLORS, fig_to_buffer, setup_dark_theme

# Edge colour drawn around each stint bar for visual separation
_STINT_EDGE_COLOR = "#15151E"


def _compound_color(compound: str) -> str:
    """Resolve a compound name to its display colour."""
    return COMPOUND_COLORS.get(compound.upper(), "#888888")


def render_strategy(strategy: StrategyResponse) -> BytesIO:
    """Render a tire-strategy bar chart and return it as a PNG buffer.

    Each driver gets a single horizontal row.  Stints are drawn as
    adjacent bars whose width equals the stint length (in laps) and
    whose colour corresponds to the tire compound.

    Parameters
    ----------
    strategy:
        A ``StrategyResponse`` containing all stints for every driver.

    Returns
    -------
    BytesIO
        In-memory PNG image.
    """
    setup_dark_theme()

    # Group stints by driver, preserving first-seen order
    driver_stints: OrderedDict[str, list[TireStint]] = OrderedDict()
    for stint in strategy.stints:
        driver_stints.setdefault(stint.driver_code, []).append(stint)

    drivers = list(driver_stints.keys())
    n_drivers = len(drivers)

    fig_height = max(4, 0.55 * n_drivers + 2)
    fig, ax = plt.subplots(figsize=(12, fig_height))

    bar_height = 0.7
    compounds_seen: set[str] = set()

    for idx, driver in enumerate(drivers):
        stints = sorted(driver_stints[driver], key=lambda s: s.start_lap)
        for stint in stints:
            compound_upper = stint.compound.upper()
            color = _compound_color(compound_upper)
            compounds_seen.add(compound_upper)

            ax.barh(
                y=idx,
                width=stint.laps,
                left=stint.start_lap,
                height=bar_height,
                color=color,
                edgecolor=_STINT_EDGE_COLOR,
                linewidth=1.2,
                alpha=0.92,
            )

            # Stint label centred inside the bar
            mid_x = stint.start_lap + stint.laps / 2.0
            text_color = "#000000" if compound_upper in ("HARD", "INTERMEDIATE") else "#FFFFFF"
            if stint.laps >= 4:
                ax.text(
                    mid_x,
                    idx,
                    compound_upper[0],
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color=text_color,
                )

    # Y-axis: driver codes
    ax.set_yticks(range(n_drivers))
    ax.set_yticklabels(drivers, fontsize=10)
    ax.invert_yaxis()

    # X-axis
    ax.set_xlabel("Lap")
    ax.set_xlim(left=0, right=strategy.total_laps + 1)

    ax.set_title(
        f"{strategy.event_name} {strategy.year} — Tire Strategy",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )

    # Legend for compounds actually used
    legend_order = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    patches = [
        Patch(facecolor=COMPOUND_COLORS[c], edgecolor=_STINT_EDGE_COLOR, label=c.title())
        for c in legend_order
        if c in compounds_seen
    ]
    if patches:
        ax.legend(
            handles=patches,
            loc="upper right",
            framealpha=0.85,
            fontsize=9,
        )

    return fig_to_buffer(fig, dpi=150)
