"""Smoke tests for the page, with network lookups stubbed out."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture(autouse=True)
def no_cache(monkeypatch):
    """Live-lookup tests stub the sources, so keep the committed cache out of the way."""
    import hazards.cache as cache
    monkeypatch.setattr(cache, "load_cache", lambda *a, **k: {})


def run(address):
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    at.text_input[0].input(address)
    at.button[0].click()
    return at.run()


def test_page_loads():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "Property hazard check"


def test_sample_address_shows_flood_section(monkeypatch):
    import hazards.flood as flood
    monkeypatch.setattr(flood, "point_query", lambda *a, **k: [{"FLD_ZONE": "VE", "ZONE_SUBTY": None, "SFHA_TF": "T"}])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any(c.value == "FEMA zone: VE" for c in at.caption)


def test_outside_california_warning():
    at = run("1 E 1st St, Reno, NV 89501")
    assert not at.exception
    assert "outside California" in at.warning[0].value


def _stub_all(monkeypatch, wildfire_rows):
    import hazards.earthquake as earthquake
    import hazards.flood as flood
    import hazards.wildfire as wildfire
    monkeypatch.setattr(flood, "point_query", lambda *a, **k: [{"FLD_ZONE": "X", "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD", "SFHA_TF": "F"}])
    monkeypatch.setattr(wildfire, "point_query", lambda url, *a, **k: wildfire_rows if "FHSALRA25" in url else [])
    monkeypatch.setattr(earthquake, "point_query", lambda url, *a, **k: [{"OBJECTID": 1}] if "Alquist" in url else [])


def test_nonwildland_is_minimal_and_overall_scores(monkeypatch):
    _stub_all(monkeypatch, [{"FHSZ": -3, "FHSZ_Description": "NonWildland"}])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any(c.value == "CAL FIRE class: NonWildland" for c in at.caption)
    assert any("Overall" in m.value and ">Severe<" in m.value for m in at.markdown)


def test_no_wildfire_polygon_gives_no_score(monkeypatch):
    _stub_all(monkeypatch, [])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any(m.value == "Not mapped" for m in at.metric)
    assert any("Overall" in m.value and ">No Score<" in m.value for m in at.markdown)
    assert any("Insufficient data" in m.value for m in at.markdown)


def test_earthquake_section_shows_fault_zone(monkeypatch):
    import hazards.earthquake as earthquake
    monkeypatch.setattr(earthquake, "point_query", lambda url, *a, **k: [{"OBJECTID": 1}] if "Alquist" in url else [])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any(c.value == "CGS zones: Fault zone" for c in at.caption)


def test_high_plus_tier_shows_insurance_message(monkeypatch):
    import hazards.flood as flood
    monkeypatch.setattr(flood, "point_query", lambda *a, **k: [{"FLD_ZONE": "VE", "ZONE_SUBTY": None, "SFHA_TF": "T"}])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any("Flood insurance is typically required" in i.value for i in at.info)


def test_minimal_tier_has_no_insurance_message(monkeypatch):
    import hazards.flood as flood
    monkeypatch.setattr(flood, "point_query", lambda *a, **k: [{"FLD_ZONE": "X", "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD", "SFHA_TF": "F"}])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert not any("Flood insurance is typically required" in i.value for i in at.info)


def test_cached_sample_works_when_sources_are_down(monkeypatch):
    import hazards.cache as cache
    import scripts.arcgis as arcgis
    from hazards.earthquake import EarthquakeResult
    from hazards.flood import FloodResult
    from hazards.wildfire import WildfireResult

    def down(*a, **k):
        raise RuntimeError("source down")
    for mod in ("hazards.flood", "hazards.wildfire", "hazards.earthquake"):
        monkeypatch.setattr(f"{mod}.point_query", down)
    addr = "2775 Embarcadero Rd, Palo Alto, CA 94303"
    entry = cache.to_entry(addr, "2026-11-26", FloodResult("VE", None, True),
                           WildfireResult("NonWildland", "LRA"), EarthquakeResult(False, False, False, False))
    monkeypatch.setattr(cache, "load_cache", lambda *a, **k: {cache.key(addr): entry})
    at = run(addr)
    assert not at.exception
    assert any(c.value == "FEMA zone: VE" for c in at.caption)
    assert any("Data as of 2026-11-26 (cached)" in c.value for c in at.caption)


def test_live_lookup_shows_data_as_of_today(monkeypatch):
    import hazards.flood as flood
    monkeypatch.setattr(flood, "point_query", lambda *a, **k: [{"FLD_ZONE": "VE", "ZONE_SUBTY": None, "SFHA_TF": "T"}])
    at = run("2775 Embarcadero Rd, Palo Alto, CA 94303")
    assert not at.exception
    assert any("(live lookup)" in c.value for c in at.caption)


def test_sample_button_runs_the_report(monkeypatch):
    import hazards.cache as cache
    from hazards.earthquake import EarthquakeResult
    from hazards.flood import FloodResult
    from hazards.wildfire import WildfireResult
    addr = "2227 Piedmont Ave, Berkeley, CA 94720"
    entry = cache.to_entry(addr, "2026-11-26", FloodResult("X", "AREA OF MINIMAL FLOOD HAZARD", False),
                           WildfireResult("NonWildland", "LRA"), EarthquakeResult(True, False, False, False))
    monkeypatch.setattr(cache, "load_cache", lambda *a, **k: {cache.key(addr): entry})
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    next(b for b in at.button if b.label == "Fault zone").click()
    at.run()
    assert not at.exception
    assert at.text_input[0].value == addr
    assert any(">Severe<" in m.value and "earthquake (fault zone)" in m.value for m in at.markdown)
    assert any("Standard policies exclude earthquake damage" in i.value for i in at.info)


def test_footer_shows_rules_version_and_methodology():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert any(c.value.startswith("Rules v1") for c in at.caption)
    assert at.expander[0].label == "How scoring works"
