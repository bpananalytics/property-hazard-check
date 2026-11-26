"""One-off discovery: find and inspect candidate hazard layers.

Prints, for each candidate URL: layer name, last edit date, fields, and what
each sample point returns. Also searches ArcGIS Online for official items.
Used to choose the URLs in config/sources.yaml (Nov 2026). Run manually;
its candidate list is a record of what was tested. Always exits 0.
"""

import datetime as dt
import pathlib
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from arcgis import HEADERS, TIMEOUT, layer_info, point_query  # noqa: E402

POINTS = {  # approximate (lon, lat) of the sample places
    "memorial_stadium": (-122.2508, 37.8712),
    "joaquin_miller": (-122.1830, 37.8150),
    "palace_fine_arts": (-122.4484, 37.8029),
    "ferry_building": (-122.3937, 37.7955),
    "palo_alto_baylands": (-122.1056, 37.4597),
    "oakland_city_hall": (-122.2725, 37.8053),
}

CANDIDATES = {
    "fhsz_lra_2025_calfire": "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0",
    "fhsz_sra_2025_calfire": "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA25_3/FeatureServer/0",
    "fhsz_combined_calfire_org": "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZ_SRA_LRA_Combined/FeatureServer/0",
}

SAMPLE_ADDRESSES = [
    "2227 Piedmont Ave, Berkeley, CA 94720",
    "3300 Joaquin Miller Rd, Oakland, CA 94602",
    "3601 Lyon St, San Francisco, CA 94123",
    "1 Ferry Building, San Francisco, CA 94111",
    "2775 Embarcadero Rd, Palo Alto, CA 94303",
    "1 Frank H Ogawa Plaza, Oakland, CA 94612",
    "1 Frank H Ogawa Plz, Oakland, CA 94612",
    "1 E 1st St, Reno, NV 89501",
]

SEARCHES: list[str] = []


def ts(ms):
    return dt.datetime.utcfromtimestamp(ms / 1000).date().isoformat() if ms else "?"


def inspect(name: str, url: str) -> None:
    print(f"\n=== {name}\n{url}")
    try:
        info = layer_info(url)
    except Exception as e:
        print(f"  INFO ERROR: {e}")
        return
    edit = info.get("editingInfo", {}).get("lastEditDate")
    fields = [f["name"] for f in info.get("fields", [])]
    print(f"  name: {info.get('name')} | last edit: {ts(edit)}")
    print(f"  fields: {fields}")
    for pname, (lon, lat) in POINTS.items():
        try:
            rows = point_query(url, lon, lat)
            slim = [{k: v for k, v in r.items() if not k.lower().startswith(("shape", "objectid", "globalid"))} for r in rows][:3]
            print(f"  {pname:20s} {len(rows)} hit(s) {slim}")
        except Exception as e:
            print(f"  {pname:20s} ERROR {e}")


def search(q: str) -> None:
    print(f"\n### ArcGIS Online search: {q}")
    try:
        r = requests.get(
            "https://www.arcgis.com/sharing/rest/search",
            params={"q": q, "f": "json", "num": 15, "sortField": "modified", "sortOrder": "desc"},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        for it in r.json().get("results", []):
            print(f"  {ts(it.get('modified'))} | {it.get('owner')} | {it.get('title')} | {it.get('url')}")
    except Exception as e:
        print(f"  SEARCH ERROR: {e}")


def geocode_all() -> None:
    print("\n### Census geocoder: sample addresses")
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    for a in SAMPLE_ADDRESSES:
        try:
            r = requests.get(url, params={"address": a, "benchmark": "Public_AR_Current", "format": "json"}, headers=HEADERS, timeout=TIMEOUT)
            m = r.json()["result"]["addressMatches"]
            if m:
                c = m[0]["coordinates"]
                print(f"  {a:45s} -> {m[0]['matchedAddress']} ({c['y']:.5f}, {c['x']:.5f})")
            else:
                print(f"  {a:45s} -> NO MATCH")
        except Exception as e:
            print(f"  {a:45s} -> ERROR {e}")


if __name__ == "__main__":
    geocode_all()
    for n, u in CANDIDATES.items():
        inspect(n, u)
    for q in SEARCHES:
        search(q)
