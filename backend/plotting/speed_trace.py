"""Speed trace overlay — speed vs distance for one or more drivers."""

from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt

from backend.models.schemas import LapTelemetry
from backend.plotting.base import fig_to_buffer, get_team_color, setup_dark_theme


def render_speed_trace(laps: list[LapTelemetry]) -> BytesIO:
    """Render a speed-trace line chart and return it as a PNG buffer.

    Each driver's telemetry is plotted as speed (km/h) on the y-axis against
    distance (m) on the x-axis, using the driver's official team colour.

    Parameters
    ----------
    laps:
        One or more ``LapTelemetry`` objects whose ``telemetry`` lists will
        be plotted.

    Returns
    -------
    BytesIO
        In-memory PNG image ready to send.
    """
    setup_dark_theme()

    fig, ax = plt.subplots(figsize=(12, 5))

    for lap in laps:
        distances = [pt.distance for pt in lap.telemetry]
        speeds = [pt.speed for pt in lap.telemetry]
        color = get_team_color(lap.team_slug)

        label = lap.driver_code
        if lap.lap_number is not None:
            label = f"{lap.driver_code} (Lap {lap.lap_number})"

        ax.plot(
            distances,
            speeds,
            color=color,
            linewidth=1.4,
            label=label,
            alpha=0.95,
        )

    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title("Speed Trace", fontsize=14, fontweight="bold", pad=12)

    ax.legend(loc="lower right", framealpha=0.85)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    return fig_to_buffer(fig, dpi=150)
