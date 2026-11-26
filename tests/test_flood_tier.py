"""Owner: Brian (#4). Flood zone -> tier, per config/scoring_rules.yaml."""

import pytest

from hazards.scoring import flood_tier


@pytest.mark.parametrize("zone, subtype, expected", [
    ("VE", None, "severe"),
    ("AE", "FLOODWAY", "severe"),
    ("AE", None, "high"),
    ("X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD", "moderate"),
    ("X", "AREA OF MINIMAL FLOOD HAZARD", "minimal"),
    ("D", None, "unknown"),
    (None, None, "unknown"),
])
def test_flood_tier(zone, subtype, expected):
    assert flood_tier(zone, subtype) == expected
