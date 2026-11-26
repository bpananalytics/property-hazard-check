"""Owner: Brian (#4). Flood zone -> tier, per config/scoring_rules.yaml."""

import pytest

from hazards.scoring import flood_tier


@pytest.mark.parametrize("zone, subtype, expected", [
    ("VE", None, "severe"),
    ("AE", "FLOODWAY", "severe"),
    ("AE", None, "high"),
    ("X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD", "moderate"),
    ("X", "AREA OF MINIMAL FLOOD HAZARD", "minimal"),
    ("D", None, "not_mapped"),
    ("X", None, "not_mapped"),
    (None, None, "not_mapped"),
])
def test_flood_tier(zone, subtype, expected):
    assert flood_tier(zone, subtype) == expected


def test_failed_lookup_is_unknown():
    assert flood_tier(None, None, error="FEMA timed out") == "unknown"
