"""Hazard tiers. Owner: Brian (#4 flood mapping, #6 scoring engine).
Tiers: "minimal", "moderate", "high", "severe", plus "unknown" (lookup failed)
and "not_mapped" (source has no class at this point).
Rules live in config/scoring_rules.yaml.
"""
from __future__ import annotations

# FEMA zones by tier (mirrors config/scoring_rules.yaml -> flood)
SEVERE_ZONES = {"V", "VE"}
HIGH_ZONES = {"A", "AE", "AH", "AO", "AR", "A99"}


def flood_tier(zone: str | None, subtype: str | None = None) -> str:
    """Map a FEMA zone (+ subtype) to a tier."""
    if zone is None:
        return "unknown"                 # unmapped / no FEMA data

    zone = zone.strip().upper()          # " ae " -> "AE"
    sub = (subtype or "").upper()

    if zone in SEVERE_ZONES or "FLOODWAY" in sub:
        return "severe"                  # coastal wave zone, or floodway

    if zone in HIGH_ZONES:
        return "high"

    if zone == "X":
        if "0.2 PCT" in sub:
            return "moderate"            # shaded X
        if "MINIMAL" in sub:
            return "minimal"             # unshaded X
        return "unknown"                 # X, but can't tell which kind

    return "unknown"                     # D, or any unrecognized code


# CAL FIRE class by tier (mirrors config/scoring_rules.yaml -> wildfire)
WILDFIRE_TIERS = {"Very High": "severe", "High": "high", "Moderate": "moderate"}


def wildfire_tier(fhsz: str | None, error: str | None = None) -> str:
    """Map a CAL FIRE FHSZ class to a tier.

    "unknown" = lookup failed. "not_mapped" = no CAL FIRE zone here
    (NonWildland or no polygon); we don't assign a tier we don't have.
    """
    if error:
        return "unknown"
    return WILDFIRE_TIERS.get((fhsz or "").strip(), "not_mapped")
