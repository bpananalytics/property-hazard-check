"""CAL FIRE Fire Hazard Severity Zone (2025) lookup for one point.

Two layers: Local Responsibility Area (cities) and State Responsibility Area
(rural). The LRA layer also has explicit "NonWildland" polygons (FHSZ -3).
A point in neither layer has no CAL FIRE class (e.g. federal land).
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import yaml

from scripts.arcgis import point_query

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Higher number = more severe. NonWildland ranks below every zone.
_RANK = {"NonWildland": 0, "Moderate": 1, "High": 2, "Very High": 3}


def _urls() -> tuple[str, str]:
    cfg = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())
    return cfg["wildfire"]["url"], cfg["wildfire_sra"]["url"]


@dataclass
class WildfireResult:
    fhsz: str | None             # "Moderate", "High", "Very High", "NonWildland"; None = no polygon
    area: str | None             # "LRA" or "SRA"
    error: str | None = None     # set when the lookup failed
    raw: dict = field(default_factory=dict)


def _get(row: dict, name: str):
    """Read a field by name; the SRA layer prefixes its field names."""
    for key, value in row.items():
        if key == name or key.endswith(f"_{name}"):
            return value
    return None


def lookup_wildfire(lat: float, lon: float, query=None) -> WildfireResult:
    query = query or point_query
    hits: list[tuple[str, str, dict]] = []
    errors: list[str] = []

    for area, url in zip(("LRA", "SRA"), _urls()):
        try:
            rows = query(url, lon, lat, out_fields="*")
        except Exception as e:  # network, timeout, or ArcGIS error
            errors.append(f"{area}: {e}")
            continue
        for r in rows:
            desc = _get(r, "FHSZ_Description")
            if desc in _RANK:
                hits.append((desc, area, r))

    if hits:
        desc, area, raw = max(hits, key=lambda h: _RANK[h[0]])
        return WildfireResult(desc, area, raw=raw)
    if errors:
        # A failed layer could have held a zone, so we can't say "no polygon".
        return WildfireResult(None, None, error="; ".join(errors))
    return WildfireResult(None, None)
