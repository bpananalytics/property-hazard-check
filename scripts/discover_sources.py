"""One-off discovery: find and inspect candidate hazard layers.

Prints, for each candidate URL: layer name, last edit date, fields, and what
each sample point returns. Also searches ArcGIS Online for official items.
Used to choose the URLs in config/sources.yaml. Always exits 0.
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
    "flood_fema_nfhl": "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28",
    "cgs_fault": "https://services2.arcgis.com/zr3KAIbsRSUyARHG/ArcGIS/rest/services/CGS_Alquist_Priolo_Fault_Zones/FeatureServer/0",
    "cgs_liquefaction": "https://services2.arcgis.com/zr3KAIbsRSUyARHG/ArcGIS/rest/services/CGS_Liquefaction_Zones/FeatureServer/0",
    "cgs_landslide_a": "https://services2.arcgis.com/zr3KAIbsRSUyARHG/ArcGIS/rest/services/CGS_Landslide_Zones/FeatureServer/0",
    "cgs_landslide_b": "https://gis.conservation.ca.gov/server/rest/services/Base/LegislativeDistrictsDashboard/FeatureServer/9",
    "fhsz_lra_2025_a": "https://services.arcgis.com/yq3FgOI44hYHAFVZ/ArcGIS/rest/services/FHSZ_LRA_25/FeatureServer/0",
    "fhsz_sra_a": "https://services1.arcgis.com/P5Mv5GY5S66M8Z1Q/ArcGIS/rest/services/High_FHSZ/FeatureServer/0",
}

SEARCHES = [
    'title:"Fire Hazard Severity Zones" AND type:"Feature Service"',
    'title:"FHSZ" AND type:"Feature Service" AND owner:*calfire*',
    'title:"Landslide Zones" AND type:"Feature Service" AND title:CGS',
]


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


if __name__ == "__main__":
    for n, u in CANDIDATES.items():
        inspect(n, u)
    for q in SEARCHES:
        search(q)
