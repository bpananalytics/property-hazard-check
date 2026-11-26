"""California Geological Survey (CGS) earthquake zone lookup for one point.

Four layers: Alquist-Priolo fault zones, liquefaction zones, landslide zones,
and Seismic Hazard Zone "unevaluated areas" (quadrangles CGS hasn't mapped
for liquefaction/landslide yet).
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import yaml

from scripts.arcgis import point_query

ROOT = pathlib.Path(__file__).resolve().parents[1]

LAYERS = {
    "fault": "earthquake_fault",
    "liquefaction": "earthquake_liquefaction",
    "landslide": "earthquake_landslide",
    "unevaluated": "earthquake_unevaluated",
}


def _urls() -> dict[str, str]:
    cfg = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())
    return {name: cfg[key]["url"] for name, key in LAYERS.items()}


@dataclass
class EarthquakeResult:
    fault: bool | None           # in an Alquist-Priolo fault zone; None = that lookup failed
    liquefaction: bool | None
    landslide: bool | None
    unevaluated: bool | None     # in a quadrangle CGS hasn't evaluated
    errors: dict = field(default_factory=dict)   # layer name -> error message

    @property
    def zones(self) -> list[str]:
        return [n for n in ("fault", "liquefaction", "landslide") if getattr(self, n)]


def lookup_earthquake(lat: float, lon: float, query=None) -> EarthquakeResult:
    query = query or point_query
    found: dict[str, bool | None] = {}
    errors: dict[str, str] = {}
    for name, url in _urls().items():
        try:
            found[name] = bool(query(url, lon, lat, out_fields="OBJECTID"))
        except Exception as e:  # network, timeout, or ArcGIS error
            found[name] = None
            errors[name] = str(e)
    return EarthquakeResult(**found, errors=errors)
