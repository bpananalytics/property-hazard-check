"""Hazard tiers. Owner: Brian (#4 flood mapping, #6 scoring engine).

Tiers: "minimal", "moderate", "high", "severe", or "unknown".
Rules live in config/scoring_rules.yaml.
"""

from __future__ import annotations


def flood_tier(zone: str | None, subtype: str | None) -> str:
    """Map a FEMA zone (+ subtype) to a tier.

    TODO (Brian, #4): implement using config/scoring_rules.yaml, then
    replace the placeholder tests in tests/test_flood_tier.py.
    Cases the real data has shown so far (see PR #13):
      VE (Palo Alto Baylands), D (Ferry Building),
      X + "AREA OF MINIMAL FLOOD HAZARD" (most samples).
    """
    return "unknown"
