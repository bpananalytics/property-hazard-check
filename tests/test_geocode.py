from hazards.geocode import geocode, load_samples


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse(self.payload)


CENSUS_MATCH = {"result": {"addressMatches": [{
    "matchedAddress": "2227 PIEDMONT AVE, BERKELEY, CA, 94720",
    "coordinates": {"x": -122.25255, "y": 37.87082},
    "addressComponents": {"state": "CA"},
}]}}
NO_MATCH = {"result": {"addressMatches": []}}


def test_sample_address_uses_stored_coordinates_without_network():
    session = FakeSession(NO_MATCH)
    r = geocode("1 Ferry Building, San Francisco, CA 94111", session=session)
    assert r.source == "sample" and r.found and r.in_california
    assert session.calls == 0


def test_sample_match_ignores_case_and_punctuation():
    r = geocode("1 ferry building san francisco ca 94111", session=FakeSession(NO_MATCH))
    assert r.source == "sample"


def test_census_match():
    r = geocode("123 Some St, Berkeley, CA", samples={}, session=FakeSession(CENSUS_MATCH))
    assert r.source == "census" and r.found and r.in_california
    assert round(r.lat, 3) == 37.871


def test_no_match():
    r = geocode("nowhere", samples={}, session=FakeSession(NO_MATCH))
    assert not r.found and r.source == "none"


def test_reno_is_outside_california():
    r = geocode("1 E 1st St, Reno, NV 89501", session=FakeSession(NO_MATCH))
    assert r.found and not r.in_california


def test_every_sample_has_coordinates():
    rows = load_samples().values()
    assert len(rows) == 7
    assert all(row["lat"] and row["lon"] for row in rows)
