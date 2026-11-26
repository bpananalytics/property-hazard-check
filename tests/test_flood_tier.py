"""Owner: Brian (#4). Replace these placeholders with real expectations."""

import pytest

from hazards.scoring import flood_tier


@pytest.mark.xfail(reason="#4: flood mapping not implemented yet", strict=False)
@pytest.mark.parametrize("zone, subtype, expected", [
    ("VE", None, "TODO"),
    ("AE", None, "TODO"),
    ("X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD", "TODO"),
    ("X", "AREA OF MINIMAL FLOOD HAZARD", "TODO"),
    ("D", None, "TODO"),
    (None, None, "TODO"),
])
def test_flood_tier(zone, subtype, expected):
    assert flood_tier(zone, subtype) == expected
