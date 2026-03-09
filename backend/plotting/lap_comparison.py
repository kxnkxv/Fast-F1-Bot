"""Lap comparison chart — speed overlay with optional delta-time subplot."""

from __future__ import annotations

from io import BytesIO
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

from backend.models.schemas import LapTelemetry
from backend.plotting.base import fig_to_buffer, get_team_color, setup_dark_theme


def _compute_delta(
    ref: LapTelemetry,
    comp: LapTelemetry,
) -> tuple[list[float], list[float]]:
    """Compute cumulative time-delta between two drivers.

    Uses the trapezoidal approximation:  dt = ds / v  where *ds* is the
    distance increment and *v* is the average speed over that increment (in
    m/s).  The returned delta is ``comp - ref`` so positive values mean the
    comparison driver is *slower*.

    Returns ``(distances, deltas)`` aligned to the *reference* driver's
    distance array.
    """
    ref_pts = ref.telemetry
    comp_pts = comp.telemetry

    if len(ref_pts) < 2 or len(comp_pts) < 2:
        return [], []

    def _cumulative_time(pts: Sequence) -> tuple[np.ndarray, np.ndarray]:
        dist = np.array([p.distance for p in pts])
        speed_kmh = np.array([p.speed for p in pts])
        speed_ms = np.clip(speed_kmh / 3.6, a_min=1e-3, a_max=None)
        ds = np.diff(dist)
        avg_v = (speed_ms[:-1] + speed_ms[1:]) / 2.0
        dt = ds / avg_v
        cum_t = np.concatenate(([0.0], np.cumsum(dt)))
        return dist, cum_t

    ref_dist, ref_time = _cumulative_time(ref_pts)
    comp_dist, comp_time = _cumulative_time(comp_pts)

    # Interpolate comp time onto the ref distance grid
    comp_time_interp = np.interp(ref_dist, comp_dist, comp_time)
    delta = comp_time_interp - ref_time

    return ref_dist.tolist(), delta.tolist()


def render_lap_comparison(laps: list[LapTelemetry]) -> BytesIO:
    """Render a lap-comparison chart and return it as a PNG buffer.

    Layout:
    * **Top subplot** — speed vs distance for every driver in the list.
    * **Bottom subplot** (only when exactly 2 drivers) — cumulative
      time-delta (seconds) of the second driver relative to the first.

    Parameters
    ----------
    laps:
        One or more ``LapTelemetry`` objects.

    Returns
    -------
    BytesIO
        In-memory PNG image.
    """
    setup_dark_theme()

    show_delta = len(laps) == 2
    nrows = 2 if show_delta else 1
    height_ratios = [3, 1] if show_delta else [1]

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=1,
        figsize=(12, 8),
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios},
        squeeze=False,
    )
    ax_speed = axes[0, 0]

    # --- Speed overlay ---
    for lap in laps:
        distances = [pt.distance for pt in lap.telemetry]
        speeds = [pt.speed for pt in lap.telemetry]
        color = get_team_color(lap.team_slug)

        label = lap.driver_code
        if lap.lap_time is not None:
            label = f"{lap.driver_code}  {lap.lap_time}"

        ax_speed.plot(distances, speeds, color=color, linewidth=1.4, label=label, alpha=0.95)

    ax_speed.set_ylabel("Speed (km/h)")
    ax_speed.set_title("Lap Comparison", fontsize=14, fontweight="bold", pad=12)
    ax_speed.legend(loc="lower right", framealpha=0.85)
    ax_speed.set_xlim(left=0)
    ax_speed.set_ylim(bottom=0)

    # --- Delta subplot ---
    if show_delta:
        ax_delta = axes[1, 0]
        ref_lap, comp_lap = laps[0], laps[1]
        dists, deltas = _compute_delta(ref_lap, comp_lap)

        if dists:
            ref_color = get_team_color(ref_lap.team_slug)
            comp_color = get_team_color(comp_lap.team_slug)

            delta_arr = np.array(deltas)
            ax_delta.fill_between(
                dists,
                deltas,
                where=delta_arr >= 0,
                interpolate=True,
                color=comp_color,
                alpha=0.35,
                label=f"{comp_lap.driver_code} slower",
            )
            ax_delta.fill_between(
                dists,
                deltas,
                where=delta_arr < 0,
                interpolate=True,
                color=ref_color,
                alpha=0.35,
                label=f"{ref_lap.driver_code} slower",
            )
            ax_delta.plot(dists, deltas, color="#FFFFFF", linewidth=1.0, alpha=0.8)
            ax_delta.axhline(0, color="#FFFFFF", linewidth=0.6, alpha=0.4)

        ax_delta.set_xlabel("Distance (m)")
        ax_delta.set_ylabel("Delta (s)")
        ax_delta.legend(loc="lower right", fontsize=9, framealpha=0.85)
    else:
        ax_speed.set_xlabel("Distance (m)")

    return fig_to_buffer(fig, dpi=150)
