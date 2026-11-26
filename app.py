"""Property Hazard Check — Streamlit entry point."""

import streamlit as st

from hazards.flood import lookup_flood
from hazards.geocode import geocode
from hazards.earthquake import lookup_earthquake
from hazards.scoring import earthquake_tier, flood_tier, wildfire_tier
from hazards.wildfire import lookup_wildfire

TIER_LABELS = {
    "minimal": "Minimal", "moderate": "Moderate", "high": "High",
    "severe": "Severe", "not_mapped": "Not mapped", "unknown": "Unknown",
}

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

        with st.spinner("Checking FEMA flood zone…"):
            f = lookup_flood(g.lat, g.lon)
        st.markdown("#### Flood")
        f_tier = flood_tier(f.zone, f.subtype, f.error)
        if f_tier == "unknown":
            st.warning("FEMA flood data is unavailable right now. Tier: unknown.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Tier", TIER_LABELS[f_tier])
            c2.metric("FEMA zone", f.zone or "No polygon")
            if f.subtype:
                st.caption(f.subtype.capitalize())
            if f_tier == "not_mapped":
                st.caption(
                    "No FEMA flood class here. "
                    "Lenders and insurers may still require a flood determination."
                )
        with st.spinner("Checking CAL FIRE hazard zone…"):
            w = lookup_wildfire(g.lat, g.lon)
        st.markdown("#### Wildfire")
        w_tier = wildfire_tier(w.fhsz, w.error)
        if w_tier == "unknown":
            st.warning("CAL FIRE data is unavailable right now. Tier: unknown.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Tier", TIER_LABELS[w_tier])
            c2.metric("CAL FIRE class", w.fhsz or "No polygon")
            if w_tier == "not_mapped":
                st.caption(
                    "Not in a CAL FIRE fire hazard zone. "
                    "Insurers may still rate wildfire risk using their own models."
                )
            elif w.area:
                st.caption(f"{'State' if w.area == 'SRA' else 'Local'} Responsibility Area")

        with st.spinner("Checking CGS earthquake zones…"):
            e = lookup_earthquake(g.lat, g.lon)
        st.markdown("#### Earthquake")
        e_tier = earthquake_tier(e)
        if e_tier == "unknown":
            st.warning("CGS earthquake data is unavailable right now. Tier: unknown.")
        else:
            zone_names = {"fault": "Fault zone", "liquefaction": "Liquefaction", "landslide": "Landslide"}
            c1, c2 = st.columns(2)
            c1.metric("Tier", TIER_LABELS[e_tier])
            c2.metric("CGS zones", ", ".join(zone_names[z] for z in e.zones) or "None")
            if e_tier == "not_mapped":
                st.caption(
                    "CGS hasn't evaluated this area for liquefaction or landslide. "
                    "Earthquake shaking risk still applies statewide."
                )
            elif e_tier == "moderate":
                st.caption("Not in a mapped CGS zone. Moderate floor: shaking risk applies statewide.")

        if {f_tier, w_tier, e_tier} & {"unknown", "not_mapped"}:
            st.caption("Report is partial: one or more hazards have no tier.")

st.divider()
st.caption("Not insurance advice. Results come from public hazard maps; insurers use their own models.")
