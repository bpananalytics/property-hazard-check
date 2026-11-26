from hazards.wildfire import lookup_wildfire

LRA_URL_PART = "FHSALRA25"


def fake_query(lra=None, sra=None, lra_exc=None, sra_exc=None):
    def q(url, lon, lat, out_fields="*"):
        is_lra = LRA_URL_PART in url
        exc = lra_exc if is_lra else sra_exc
        if exc:
            raise exc
        return (lra if is_lra else sra) or []
    return q


def test_city_zone():
    r = lookup_wildfire(37.81, -122.19, query=fake_query(lra=[{"FHSZ": 3, "FHSZ_Description": "Very High", "SRA": "LRA"}]))
    assert r.fhsz == "Very High" and r.area == "LRA" and r.error is None


def test_rural_zone_with_prefixed_fields():
    row = {"xxFHSZSRA25_3_FHSZ": 2, "xxFHSZSRA25_3_FHSZ_Description": "High", "xxFHSZSRA25_3_SRA": "SRA"}
    r = lookup_wildfire(38.9, -120.5, query=fake_query(sra=[row]))
    assert r.fhsz == "High" and r.area == "SRA"


def test_nonwildland_is_returned_as_its_own_class():
    r = lookup_wildfire(37.80, -122.27, query=fake_query(lra=[{"FHSZ": -3, "FHSZ_Description": "NonWildland"}]))
    assert r.fhsz == "NonWildland" and r.error is None


def test_most_severe_hit_wins():
    r = lookup_wildfire(0, 0, query=fake_query(
        lra=[{"FHSZ_Description": "NonWildland"}],
        sra=[{"xxFHSZSRA25_3_FHSZ_Description": "Moderate"}],
    ))
    assert r.fhsz == "Moderate" and r.area == "SRA"


def test_no_polygon_in_either_layer():
    r = lookup_wildfire(0, 0, query=fake_query())
    assert r.fhsz is None and r.error is None


def test_one_layer_down_and_no_hit_is_an_error():
    r = lookup_wildfire(0, 0, query=fake_query(sra_exc=TimeoutError("CAL FIRE timed out")))
    assert r.fhsz is None and "timed out" in r.error


def test_one_layer_down_but_other_hit_still_returns_zone():
    r = lookup_wildfire(0, 0, query=fake_query(lra=[{"FHSZ_Description": "High"}], sra_exc=TimeoutError("x")))
    assert r.fhsz == "High" and r.error is None
