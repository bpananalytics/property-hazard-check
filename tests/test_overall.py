from hazards.scoring import compound_flag, overall_tier


def test_worst_single_hazard_wins():
    assert overall_tier({"flood": "minimal", "wildfire": "high", "earthquake": "moderate"}) == ("high", [])


def test_missing_data_gives_no_score_even_with_severe():
    assert overall_tier({"flood": "minimal", "wildfire": "not_mapped", "earthquake": "severe"})[0] == "no_score"


def test_failed_lookup_gives_no_score():
    assert overall_tier({"flood": "unknown", "wildfire": "high", "earthquake": "moderate"})[0] == "no_score"


def test_compound_flag():
    assert compound_flag({"flood": "high", "wildfire": "moderate", "earthquake": "severe"})
    assert not compound_flag({"flood": "high", "wildfire": "moderate", "earthquake": "moderate"})
