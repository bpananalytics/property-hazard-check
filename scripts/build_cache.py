"""Rebuild data/cache.json from live lookups for every California sample address.

Run by hand only (the "Build cache" GitHub workflow). A sample whose lookup
fails keeps its previous cache entry, so a source outage never wipes the cache.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import zoneinfo

from hazards import cache
from hazards.earthquake import lookup_earthquake
from hazards.flood import lookup_flood
from hazards.geocode import load_samples
from hazards.wildfire import lookup_wildfire


def main() -> int:
    today = dt.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date().isoformat()
    entries = cache.load_cache()
    updated, kept = [], []

    for row in load_samples().values():
        if row["state"] != "CA":
            continue
        lat, lon = float(row["lat"]), float(row["lon"])
        f, w, e = lookup_flood(lat, lon), lookup_wildfire(lat, lon), lookup_earthquake(lat, lon)
        if f.error or w.error or e.errors:
            kept.append(row["address"])
            continue
        entries[cache.key(row["address"])] = cache.to_entry(row["address"], today, f, w, e)
        updated.append(row["address"])

    cache.CACHE_PATH.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n")
    print(f"Updated {len(updated)}: {updated}")
    print(f"Kept previous (lookup failed) {len(kept)}: {kept}")
    return 0 if updated else 1


if __name__ == "__main__":
    sys.exit(main())
