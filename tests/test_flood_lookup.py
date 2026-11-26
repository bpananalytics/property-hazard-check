from hazards.flood import lookup_flood


def fake_query(rows=None, exc=None):
    def q(url, lon, lat, out_fields="*"):
        if exc:
            raise exc
        return rows
    return q


def test_coastal_zone():
    r = lookup_flood(37.4597, -122.1056, query=fake_query([{"FLD_ZONE": "VE", "ZONE_SUBTY": None, "SFHA_TF": "T"}]))
    assert r.zone == "VE" and r.sfha is True and r.error is None


def test_minimal_zone():
    r = lookup_flood(37.8, -122.27, query=fake_query([{"FLD_ZONE": "X", "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD", "SFHA_TF": "F"}]))
    assert r.zone == "X" and r.sfha is False


def test_no_polygon_at_point():
    r = lookup_flood(0, 0, query=fake_query([]))
    assert r.zone is None and r.error is None


def test_source_down_is_reported_not_raised():
    r = lookup_flood(0, 0, query=fake_query(exc=TimeoutError("FEMA timed out")))
    assert r.zone is None and "timed out" in r.error
