import pytest

from hazards.earthquake import EarthquakeResult, lookup_earthquake
from hazards.scoring import earthquake_tier


def fake_query(hits=(), fail=()):
    def q(url, lon, lat, out_fields="*"):
        for name in fail:
            if name in url:
                raise TimeoutError(f"{name} timed out")
        return [{"OBJECTID": 1}] if any(h in url for h in hits) else []
    return q


def test_lookup_flags_each_layer():
    r = lookup_earthquake(0, 0, query=fake_query(hits=["Liquefaction"]))
    assert r.liquefaction is True and r.fault is False and r.zones == ["liquefaction"] and not r.errors


def test_lookup_reports_failed_layer():
    r = lookup_earthquake(0, 0, query=fake_query(fail=["Landslide"]))
    assert r.landslide is None and "landslide" in r.errors


def er(fault=False, liq=False, land=False, uneval=False, errors=None):
    return EarthquakeResult(fault, liq, land, uneval, errors or {})


@pytest.mark.parametrize("result, expected", [
    (er(fault=True), "severe"),
    (er(fault=True, errors={"landslide": "x"}), "severe"),
    (er(liq=True), "high"),
    (er(land=True), "high"),
    (er(uneval=True), "not_mapped"),
    (er(), "moderate"),
    (er(errors={"liquefaction": "x"}), "unknown"),
])
def test_earthquake_tier(result, expected):
    assert earthquake_tier(result) == expected
