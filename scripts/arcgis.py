"""Small helpers for querying ArcGIS REST layers by point."""

import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "property-hazard-check/0.1 (portfolio project)"}


def layer_info(url: str) -> dict:
    r = requests.get(url, params={"f": "json"}, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def point_query(url: str, lon: float, lat: float, out_fields: str = "*") -> list[dict]:
    """Return attributes of every polygon in the layer that contains the point."""
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "false",
        "f": "json",
    }
    r = requests.get(f"{url}/query", params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return [f["attributes"] for f in data.get("features", [])]
