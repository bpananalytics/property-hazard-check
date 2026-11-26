"""FEMA flood zone lookup (National Flood Hazard Layer) for one point."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import yaml

from scripts.arcgis import point_query

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _flood_url() -> str:
    return yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())["flood"]["url"]


@dataclass
class FloodResult:
    zone: str | None          # FLD_ZONE, e.g. "AE", "VE", "X", "D"; None = no polygon at this point
    subtype: str | None       # ZONE_SUBTY, e.g. "0.2 PCT ANNUAL CHANCE FLOOD HAZARD"
    sfha: bool | None         # SFHA_TF: inside a Special Flood Hazard Area
    error: str | None = None  # set when the lookup failed
    raw: dict = field(default_factory=dict)


def lookup_flood(lat: float, lon: float, query=None) -> FloodResult:
    query = query or point_query
    try:
        rows = query(_flood_url(), lon, lat, out_fields="FLD_ZONE,ZONE_SUBTY,SFHA_TF")
    except Exception as e:  # network, timeout, or ArcGIS error
        return FloodResult(None, None, None, error=str(e))
    if not rows:
        return FloodResult(None, None, None)
    r = rows[0]
    sfha = {"T": True, "F": False}.get(r.get("SFHA_TF"))
    return FloodResult(r.get("FLD_ZONE"), r.get("ZONE_SUBTY"), sfha, raw=r)
