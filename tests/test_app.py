"""Smoke tests for the page, with network lookups stubbed out."""

from streamlit.testing.v1 import AppTest


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
    assert any(m.value == "VE" for m in at.metric)


def test_outside_california_warning():
    at = run("1 E 1st St, Reno, NV 89501")
    assert not at.exception
    assert "outside California" in at.warning[0].value
