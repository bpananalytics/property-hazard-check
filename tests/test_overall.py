from hazards.scoring import overall_tier


def test_worst_single_hazard_wins():
    assert overall_tier({"flood": "minimal", "wildfire": "high", "earthquake": "moderate"}) == ("high", [])


def test_partial_stays_partial_even_with_severe():
    assert overall_tier({"flood": "minimal", "wildfire": "not_mapped", "earthquake": "severe"}) == ("partial", ["wildfire"])


def test_partial_names_every_missing_hazard():
    assert overall_tier({"flood": "unknown", "wildfire": "not_mapped", "earthquake": "moderate"}) == ("partial", ["flood", "wildfire"])
