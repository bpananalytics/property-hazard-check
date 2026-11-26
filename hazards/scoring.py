"""Hazard tiers. Owner: Brian (#4 flood mapping, #6 scoring engine).
Tiers: "minimal", "moderate", "high", "severe", plus "unknown" (lookup failed)
and "not_mapped" (source has no class at this point).
Rules live in config/scoring_rules.yaml.
"""
from __future__ import annotations

# FEMA zones by tier (mirrors config/scoring_rules.yaml -> flood)
SEVERE_ZONES = {"V", "VE"}
HIGH_ZONES = {"A", "AE", "AH", "AO", "AR", "A99"}


def flood_tier(zone: str | None, subtype: str | None = None, error: str | None = None) -> str:
    """Map a FEMA zone (+ subtype) to a tier.

    "unknown" = lookup failed. "not_mapped" = FEMA gives no usable class here.
    """
    if error:
        return "unknown"                 # lookup failed
    if zone is None:
        return "not_mapped"              # no FEMA polygon at this point

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
        return "not_mapped"              # X, but can't tell which kind

    return "not_mapped"                  # D (undetermined), or any unrecognized code


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


def earthquake_tier(r) -> str:
    """Map an EarthquakeResult to a tier (config/scoring_rules.yaml -> earthquake).

    Fault zone -> severe. Liquefaction or landslide zone -> high.
    Unevaluated quadrangle -> not_mapped. Otherwise moderate (statewide shaking floor).
    A failed layer -> unknown, unless a fault zone already makes it severe.
    """
    if r.fault:
        return "severe"
    if r.errors:
        return "unknown"
    if r.liquefaction or r.landslide:
        return "high"
    if r.unevaluated:
        return "not_mapped"
    return "moderate"


TIER_ORDER = ["minimal", "moderate", "high", "severe"]


def overall_tier(tiers: dict[str, str]) -> tuple[str, list[str]]:
    """Roll hazard tiers up to one overall tier (config/scoring_rules.yaml -> overall).

    Returns (overall, missing). If any hazard is not_mapped or unknown, the
    overall is "no_score" (insufficient data) — no worst-of guess.
    Otherwise the overall is the worst single hazard.
    """
    missing = [h for h, t in tiers.items() if t in ("not_mapped", "unknown")]
    if missing:
        return "no_score", missing
    return max(tiers.values(), key=TIER_ORDER.index), []


def compound_flag(tiers: dict[str, str]) -> bool:
    """True when 2+ hazards are High or above (only meaningful with a full score)."""
    return sum(t in ("high", "severe") for t in tiers.values()) >= 2
