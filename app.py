"""Property Hazard Check — Streamlit entry point."""

import streamlit as st

st.set_page_config(page_title="Property Hazard Check", page_icon="🛡️", layout="centered")

st.title("Property hazard check")
st.write(
    "Enter a California address to see its flood, wildfire, and earthquake exposure "
    "— and what each means for insurance."
)

address = st.text_input("Address", placeholder="2775 Embarcadero Rd, Palo Alto, CA 94303")
if st.button("Check address", disabled=not address):
    st.info("Hazard lookups are coming soon. This is the first deployed version.")

st.divider()
st.caption("Not insurance advice. Results come from public hazard maps; insurers use their own models.")
