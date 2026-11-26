"""Wildfire class -> tier, per config/scoring_rules.yaml."""

import pytest

from hazards.scoring import wildfire_tier


@pytest.mark.parametrize("fhsz, error, expected", [
    ("Very High", None, "severe"),
    ("High", None, "high"),
    ("Moderate", None, "moderate"),
    ("NonWildland", None, "not_mapped"),
    (None, None, "not_mapped"),
    (None, "CAL FIRE timed out", "unknown"),
])
def test_wildfire_tier(fhsz, error, expected):
    assert wildfire_tier(fhsz, error) == expected


def test_not_mapped_is_never_minimal():
    assert wildfire_tier("NonWildland") != "minimal"
