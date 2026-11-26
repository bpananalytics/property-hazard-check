"""Address -> point, using the US Census Geocoder.

Sample addresses use stored coordinates (data/sample_addresses.csv) because
some of them don't match in the Census geocoder, and so demos never depend on it.
"""

from __future__ import annotations

import csv
import pathlib
import re
from dataclasses import dataclass

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
TIMEOUT = 15


@dataclass
class GeocodeResult:
    input_address: str
    matched_address: str | None
    lat: float | None
    lon: float | None
    state: str | None
    source: str            # "sample" | "census" | "none"

    @property
    def found(self) -> bool:
        return self.lat is not None and self.lon is not None

    @property
    def in_california(self) -> bool:
        return self.state == "CA"


def _norm(address: str) -> str:
    return re.sub(r"[^a-z0-9]", "", address.lower())


def load_samples(path: pathlib.Path = ROOT / "data" / "sample_addresses.csv") -> dict[str, dict]:
    with path.open(newline="") as f:
        return {_norm(row["address"]): row for row in csv.DictReader(f)}


def geocode(address: str, samples: dict[str, dict] | None = None, session=requests) -> GeocodeResult:
    address = address.strip()
    samples = load_samples() if samples is None else samples

    row = samples.get(_norm(address))
    if row and row.get("lat") and row.get("lon"):
        return GeocodeResult(address, row["address"], float(row["lat"]), float(row["lon"]), row["state"], "sample")

    r = session.get(
        CENSUS_URL,
        params={"address": address, "benchmark": "Public_AR_Current", "format": "json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    matches = r.json()["result"]["addressMatches"]
    if not matches:
        return GeocodeResult(address, None, None, None, None, "none")

    m = matches[0]
    c = m["coordinates"]
    state = m.get("addressComponents", {}).get("state")
    return GeocodeResult(address, m["matchedAddress"], float(c["y"]), float(c["x"]), state, "census")
