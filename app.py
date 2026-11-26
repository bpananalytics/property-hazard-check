"""Property Hazard Check — Streamlit entry point."""

import pathlib

import streamlit as st
import yaml

from hazards.earthquake import lookup_earthquake
from hazards.flood import lookup_flood
from hazards.geocode import geocode
from hazards.scoring import compound_flag, earthquake_tier, flood_tier, overall_tier, wildfire_tier
from hazards.wildfire import lookup_wildfire

RULES = yaml.safe_load((pathlib.Path(__file__).parent / "config" / "scoring_rules.yaml").read_text())
MESSAGES = RULES["insurance_messages"]

TIER_LABELS = {
    "minimal": "Minimal", "moderate": "Moderate", "high": "High",
    "severe": "Severe", "not_mapped": "Not mapped", "unknown": "Unknown",
}
ZONE_NAMES = {"fault": "Fault zone", "liquefaction": "Liquefaction", "landslide": "Landslide"}


def hazard_section(title, source, tier, code_label, code_value, notes=()):
    """One hazard block: tier + raw source code, or an 'unavailable' warning."""
    st.markdown(f"#### {title}")
    if tier == "unknown":
        st.warning(f"{source} data is unavailable right now. Tier: unknown.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Tier", TIER_LABELS[tier])
    c2.metric(code_label, code_value)
    for note in notes:
        if note:
            st.caption(note)

st.set_page_config(page_title="Property Hazard Check", page_icon="🛡️", layout="centered")

st.title("Property hazard check")
st.write(
    "Enter a California address to see its flood, wildfire, and earthquake exposure "
    "— and what each means for insurance."
)

with st.form("search"):
    address = st.text_input("Address", placeholder="2775 Embarcadero Rd, Palo Alto, CA 94303")
    submitted = st.form_submit_button("Check address")

if submitted and address.strip():
    with st.spinner("Looking up address…"):
        try:
            g = geocode(address)
        except Exception:
            g = None
    if g is None:
        st.error("The address service didn't respond. Try again in a moment.")
    elif not g.found:
        st.error("Address not found. Check the spelling, or include city and ZIP.")
    elif not g.in_california:
        st.warning(f"{g.matched_address} is outside California. This tool covers California only.")
    else:
        st.subheader(g.matched_address)
        st.caption(f"{g.lat:.5f}, {g.lon:.5f} · location from {g.source}")
        overall_slot = st.empty()   # filled after all lookups, shown at the top

        with st.spinner("Checking FEMA flood zone…"):
            f = lookup_flood(g.lat, g.lon)
        f_tier = flood_tier(f.zone, f.subtype, f.error)
        hazard_section(
            "Flood", "FEMA", f_tier, "FEMA zone", f.zone or "No polygon",
            notes=[f.subtype.capitalize() if f.subtype else None,
                   MESSAGES["flood_not_mapped"] if f_tier == "not_mapped" else None],
        )

        with st.spinner("Checking CAL FIRE hazard zone…"):
            w = lookup_wildfire(g.lat, g.lon)
        w_tier = wildfire_tier(w.fhsz, w.error)
        area = {"SRA": "State Responsibility Area", "LRA": "Local Responsibility Area"}.get(w.area)
        hazard_section(
            "Wildfire", "CAL FIRE", w_tier, "CAL FIRE class", w.fhsz or "No polygon",
            notes=[MESSAGES["wildfire_not_mapped"] if w_tier == "not_mapped" else area],
        )

        with st.spinner("Checking CGS earthquake zones…"):
            e = lookup_earthquake(g.lat, g.lon)
        e_tier = earthquake_tier(e)
        hazard_section(
            "Earthquake", "CGS earthquake", e_tier, "CGS zones",
            ", ".join(ZONE_NAMES[z] for z in e.zones) or "None",
            notes=[{"not_mapped": MESSAGES["earthquake_not_mapped"],
                    "moderate": MESSAGES["earthquake_moderate_floor"]}.get(e_tier)],
        )

        tiers = {"flood": f_tier, "wildfire": w_tier, "earthquake": e_tier}
        overall = overall_tier(tiers)
        with overall_slot.container():
            if overall == "no_score":
                st.metric("Overall", "No Score")
                st.caption("Insufficient data")
            else:
                st.metric("Overall", TIER_LABELS[overall])
                if compound_flag(tiers):
                    st.warning("Compound risk: 2 or more hazards are High or above.")
            st.divider()

st.divider()
st.caption("Not insurance advice. Results come from public hazard maps; insurers use their own models.")
