import json

from hazards import cache
from hazards.earthquake import EarthquakeResult
from hazards.flood import FloodResult
from hazards.wildfire import WildfireResult


def test_round_trip(tmp_path):
    f = FloodResult("AE", None, True)
    w = WildfireResult("High", "SRA")
    e = EarthquakeResult(True, False, None, False)
    entry = cache.to_entry("1 Main St, Oakland, CA", "2026-11-26", f, w, e)
    path = tmp_path / "cache.json"
    path.write_text(json.dumps({cache.key(entry["address"]): entry}))
    loaded = cache.load_cache(path)[cache.key("1 MAIN ST OAKLAND CA")]
    f2, w2, e2 = cache.to_results(loaded)
    assert (f2.zone, f2.sfha, w2.fhsz, w2.area) == ("AE", True, "High", "SRA")
    assert (e2.fault, e2.landslide, e2.errors) == (True, None, {})
    assert loaded["fetched"] == "2026-11-26"


def test_missing_file_is_empty_cache(tmp_path):
    assert cache.load_cache(tmp_path / "nope.json") == {}


def test_lookup_none_address():
    assert cache.lookup(None) is None
