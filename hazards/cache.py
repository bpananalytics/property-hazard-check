"""Baseline result cache (data/cache.json), committed to the repo.

Holds hazard lookups for the sample addresses so demos work even when a
source is down. Entries never expire and the app never writes to it;
refresh by running the "Build cache" workflow by hand (scripts/build_cache.py).
"""

from __future__ import annotations

import json
import pathlib

from hazards.earthquake import EarthquakeResult
from hazards.flood import FloodResult
from hazards.geocode import _norm
from hazards.wildfire import WildfireResult

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "data" / "cache.json"


def load_cache(path: pathlib.Path = CACHE_PATH) -> dict[str, dict]:
    """Address key -> cached entry. Missing file = empty cache."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def lookup(address: str | None) -> dict | None:
    """Cached entry for an address, or None."""
    if not address:
        return None
    return load_cache().get(_norm(address))


def to_entry(address: str, fetched: str, f: FloodResult, w: WildfireResult, e: EarthquakeResult) -> dict:
    return {
        "address": address,
        "fetched": fetched,
        "flood": {"zone": f.zone, "subtype": f.subtype, "sfha": f.sfha},
        "wildfire": {"fhsz": w.fhsz, "area": w.area},
        "earthquake": {"fault": e.fault, "liquefaction": e.liquefaction,
                       "landslide": e.landslide, "unevaluated": e.unevaluated},
    }


def to_results(entry: dict) -> tuple[FloodResult, WildfireResult, EarthquakeResult]:
    return (
        FloodResult(**entry["flood"]),
        WildfireResult(**entry["wildfire"]),
        EarthquakeResult(**entry["earthquake"]),
    )


def key(address: str) -> str:
    return _norm(address)
