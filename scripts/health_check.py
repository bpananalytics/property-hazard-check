"""Daily health check: every data source answers, with the fields we rely on.

Reads config/sources.yaml. For each source with a test point, runs a point query
and checks that the required fields come back. Exits 1 if any source fails.
"""

import pathlib
import sys

import requests
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from arcgis import HEADERS, TIMEOUT, point_query  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def check_geocoder(cfg: dict) -> str:
    params = dict(cfg["params"], address=cfg["test_address"])
    r = requests.get(cfg["url"], params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    matches = r.json()["result"]["addressMatches"]
    if not matches:
        raise RuntimeError("no match for test address")
    c = matches[0]["coordinates"]
    return f"{matches[0]['matchedAddress']} -> ({c['y']:.5f}, {c['x']:.5f})"


def check_layer(cfg: dict) -> str:
    lon, lat = cfg["test_point"]
    rows = point_query(cfg["url"], lon, lat)
    if cfg.get("expect_hit", True) and not rows:
        raise RuntimeError("test point returned no features")
    missing = [f for f in cfg.get("fields", []) if rows and f not in rows[0]]
    if missing:
        raise RuntimeError(f"missing fields: {missing}")
    shown = {f: rows[0].get(f) for f in cfg.get("fields", [])} if rows else "no features"
    return f"{len(rows)} feature(s): {shown}"


def main() -> int:
    sources = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())
    failures = 0
    for name, cfg in sources.items():
        if str(cfg.get("url", "")).startswith("TODO"):
            print(f"SKIP  {name}: URL not set")
            continue
        try:
            detail = check_geocoder(cfg) if name == "geocoder" else check_layer(cfg)
            print(f"OK    {name}: {detail}")
        except Exception as e:  # report every source, then fail at the end
            failures += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
