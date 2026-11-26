"""Owner: Brian (#4). Flood zone -> 4-tier rating: High / Moderate / Low / Unknown."""

import pytest

from hazards.scoring import flood_tier


@pytest.mark.xfail(reason="#4: flood mapping not implemented yet", strict=False)
@pytest.mark.parametrize("zone, subtype, expected", [
    ("VE", None, "High"),
    ("AE", None, "High"),
    ("X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD", "Moderate"),
    ("X", "AREA OF MINIMAL FLOOD HAZARD", "Low"),
    ("D", None, "Unknown"),
    (None, None, "Unknown"),
])
def test_flood_tier(zone, subtype, expected):
    assert flood_tier(zone, subtype) == expected
