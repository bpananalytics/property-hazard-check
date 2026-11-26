"""Property Hazard Check — Streamlit entry point."""

import streamlit as st

from hazards.flood import lookup_flood
from hazards.geocode import geocode
from hazards.scoring import flood_tier

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
        if f.error:
            st.warning("FEMA flood data is unavailable right now. Tier: unknown.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Tier", flood_tier(f.zone, f.subtype).capitalize())
            c2.metric("FEMA zone", f.zone or "Not mapped")
            if f.subtype:
                st.caption(f.subtype.capitalize())
        st.info("Wildfire and earthquake checks are coming next.")

st.divider()
st.caption("Not insurance advice. Results come from public hazard maps; insurers use their own models.")
