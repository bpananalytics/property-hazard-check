"""Hazard tiers. Owner: Brian (#4 flood mapping, #6 scoring engine).
Tiers: "minimal", "moderate", "high", "severe", or "unknown".
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
