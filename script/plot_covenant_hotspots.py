#!/usr/bin/env python
"""Render an interactive hotspot map (with time slider) from notebook_final_output.csv."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import List, Optional

import folium
import pandas as pd
from folium import Popup, Tooltip
from folium.plugins import HeatMap, HeatMapWithTime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "output" / "notebook_final_output.csv"
OUTPUT_FILE = PROJECT_ROOT / "output" / "covenant_hotspots.html"

# Colors
CIRCLE_COLOR = "#c0392b"  # muted red
FILL_OPACITY = 0.28


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_csv(path)
    df = df[df["geo_latitude"].notnull() & df["geo_longitude"].notnull()]

    # Parse deed year for time slider; fall back to NaT if missing
    df["year"] = pd.to_datetime(df["deed_date"], errors="coerce").dt.year

    # Prepare plotting coordinates with slight offsets for overlapping points
    return add_plot_coords(df)


def add_plot_coords(df: pd.DataFrame, offset_meters: float = 60.0) -> pd.DataFrame:
    """Add plot_lat/plot_lon columns; nudge duplicates so circles don't fully overlap."""
    df = df.copy()
    df["plot_lat"] = df["geo_latitude"]
    df["plot_lon"] = df["geo_longitude"]

    deg_per_meter_lat = 1 / 111_320  # rough

    grouped = df.groupby(["geo_latitude", "geo_longitude"])
    for (_, _), idx in grouped.groups.items():
        indices = list(idx)
        n = len(indices)
        if n <= 1:
            continue
        for i, row_idx in enumerate(indices):
            angle = 2 * math.pi * i / n
            lat = df.at[row_idx, "geo_latitude"]
            lon = df.at[row_idx, "geo_longitude"]
            cos_lat = math.cos(math.radians(lat)) or 1e-6
            delta_lat = offset_meters * deg_per_meter_lat * math.sin(angle)
            delta_lon = offset_meters * deg_per_meter_lat * math.cos(angle) / cos_lat
            df.at[row_idx, "plot_lat"] = lat + delta_lat
            df.at[row_idx, "plot_lon"] = lon + delta_lon

    return df


def build_heatmap_series(df: pd.DataFrame) -> tuple[list[list[list[float]]], list[str]]:
    """
    Return cumulative data and labels for HeatMapWithTime.
    Once a point appears in a year, it stays in later frames (avoids blinking).
    Unknown years are appended at the end as a final frame.
    """
    known_years: List[int] = sorted(y for y in df["year"].dropna().unique())
    heat_data: list[list[list[float]]] = []
    labels: list[str] = []
    cumulative: list[list[float]] = []

    for year in known_years:
        year_points = df[df["year"] == year][["plot_lat", "plot_lon"]].values.tolist()
        cumulative += year_points
        heat_data.append(list(cumulative))
        labels.append(str(int(year)))

    unknown_subset = df[df["year"].isna()]
    if not unknown_subset.empty:
        cumulative += unknown_subset[["plot_lat", "plot_lon"]].values.tolist()
        heat_data.append(list(cumulative))
        labels.append("Unknown")

    return heat_data, labels


def add_circles(df: pd.DataFrame, fmap: folium.Map) -> None:
    def safe_val(v: Optional[str]) -> str:
        return "N/A" if pd.isna(v) else str(v)

    for row in df.itertuples():
        radius_m = (
            float(row.geo_cluster_radius_miles) * 1609.34
            if hasattr(row, "geo_cluster_radius_miles")
            and pd.notnull(row.geo_cluster_radius_miles)
            else 400
        )

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.45;">
            <b>Deed ID:</b> {row.deed_id}<br/>
            <b>Date:</b> {safe_val(getattr(row, 'deed_date', None))}<br/>
            <b>Geo Address:</b> {safe_val(getattr(row, 'geo_address', None))}<br/>
            <b>City:</b> {safe_val(getattr(row, 'city', None))}<br/>
            <b>Grantors:</b> {safe_val(getattr(row, 'grantors', None))}<br/>
            <b>Grantees:</b> {safe_val(getattr(row, 'grantees', None))}<br/>
            <b>Plan Book/Page:</b> {safe_val(getattr(row, 'plan_books', None))} / {safe_val(getattr(row, 'plan_pages', None))}<br/>
            <b>Lot Numbers:</b> {safe_val(getattr(row, 'lot_numbers', None))}<br/>
            <b>Geo Town:</b> {safe_val(getattr(row, 'geo_town', None))}<br/>
            <b>Geo Radius (miles):</b> {safe_val(getattr(row, 'geo_cluster_radius_miles', None))}
        </div>
        """

        tooltip_text = (
            f"Deed {row.deed_id} | {safe_val(getattr(row, 'deed_date', None))} | "
            f"{safe_val(getattr(row, 'geo_address', None))} | {safe_val(getattr(row, 'city', None))}"
        )

        folium.Circle(
            location=[row.plot_lat, row.plot_lon],
            radius=radius_m,
            color=CIRCLE_COLOR,
            weight=1.4,
            fill=True,
            fill_opacity=FILL_OPACITY,
            fill_color=CIRCLE_COLOR,
            tooltip=Tooltip(tooltip_text),
            popup=Popup(popup_html, max_width=360),
        ).add_to(fmap)


def make_map(df: pd.DataFrame) -> folium.Map:
    center = [df["geo_latitude"].mean(), df["geo_longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron", control_scale=True)

    # Static heatmap layer
    heat_data = df[["plot_lat", "plot_lon"]].values.tolist()
    if heat_data:
        static_layer = folium.FeatureGroup(name="Static Hotspots", show=False, overlay=True)
        HeatMap(
            data=heat_data,
            radius=45,
            blur=25,
            gradient={
                "0.10": "#fff3bf",
                "0.25": "#fdc777",
                "0.45": "#f07c4a",
                "0.65": "#d73027",
                "0.90": "#9b0000",
                "1.0": "#5a0000",
            },
            min_opacity=0.3,
            max_opacity=0.6,
        ).add_to(static_layer)
        static_layer.add_to(fmap)

    # Time slider heatmap layer - blur must be 0-1 for heatmap.js
    time_data, labels = build_heatmap_series(df)
    if time_data:
        HeatMapWithTime(
            data=time_data,
            index=labels,
            radius=45,
            blur=0.85,  # Must be decimal 0-1, not integer
            auto_play=False,
            max_opacity=0.6,
            min_opacity=0.3,
            gradient={
                "0.10": "#fff3bf",
                "0.25": "#fdc777",
                "0.45": "#f07c4a",
                "0.65": "#d73027",
                "0.90": "#9b0000",
                "1.0": "#5a0000",
            },
            display_index=True,
            min_speed=1,
            max_speed=12,
            speed_step=1,
        ).add_to(fmap)

    # Add layer control
    folium.LayerControl(position="topright", collapsed=False).add_to(fmap)

    return fmap


def main() -> None:
    df = load_data(DATA_FILE)
    if df.empty:
        raise ValueError("No rows with coordinates (and restrictive covenants) to plot.")

    fmap = make_map(df)
    fmap.save(str(OUTPUT_FILE))
    print(f"Saved map to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
