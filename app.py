"""Property Hazard Check — Streamlit entry point."""

import datetime as dt
from concurrent.futures import ThreadPoolExecutor
import html
import pathlib
import zoneinfo

import streamlit as st
import yaml

from hazards import cache
from hazards.earthquake import lookup_earthquake
from hazards.flood import lookup_flood
from hazards.geocode import geocode, load_samples
from hazards.scoring import compound_flag, earthquake_tier, flood_tier, overall_tier, wildfire_tier
from hazards.wildfire import lookup_wildfire

RULES = yaml.safe_load((pathlib.Path(__file__).parent / "config" / "scoring_rules.yaml").read_text())
MESSAGES = RULES["insurance_messages"]

TIER_LABELS = {
    "minimal": "Minimal", "moderate": "Moderate", "high": "High",
    "severe": "Severe", "not_mapped": "Not mapped", "unknown": "Unknown",
}
ZONE_NAMES = {"fault": "Fault zone", "liquefaction": "Liquefaction", "landslide": "Landslide"}
HIGH_PLUS = ("high", "severe")

# Official address-lookup maps, linked when a source is unavailable.
OFFICIAL_MAPS = {
    "Flood": ("FEMA Flood Map Service Center", "https://msc.fema.gov/portal/home"),
    "Wildfire": ("CAL FIRE fire hazard severity zones", "https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones"),
    "Earthquake": ("CGS EQ Zapp", "https://www.conservation.ca.gov/cgs/sh/eqzapp"),
}

# Sample buttons: role in data/sample_addresses.csv -> button label (California samples only).
SAMPLE_LABELS = {
    "fault_zone": "Fault zone", "wildfire": "Wildfire", "flood": "Coastal flood",
    "liquefaction": "Liquefaction", "multi_hazard": "Multi-hazard", "low_risk_control": "Low risk",
}

# Overall card colors by tier: (background, text). Translucent so they work in light and dark mode.
OVERALL_COLORS = {
    "minimal": ("rgba(33, 150, 83, 0.12)", "#2e8b57"),
    "moderate": ("rgba(230, 170, 30, 0.16)", "#b7791f"),
    "high": ("rgba(230, 110, 40, 0.16)", "#d0601e"),
    "severe": ("rgba(220, 50, 50, 0.14)", "#d33a3a"),
    "no_score": ("rgba(128, 128, 128, 0.12)", "#808080"),
}


def overall_card(overall: str, worst: str | None, compound: bool, missing: list[str]) -> None:
    """Colored card at the top of the report: overall tier + why."""
    bg, fg = OVERALL_COLORS[overall]
    label = "No Score" if overall == "no_score" else TIER_LABELS[overall]
    if overall == "no_score":
        why = f"Insufficient data: no tier for {', '.join(missing)}. See the cards below."
    else:
        why = f"Worst single hazard: {worst}."
        if compound:
            why += " Compound risk: 2 or more hazards are High or above."
    st.markdown(
        f'<div style="background:{bg};border-radius:8px;padding:12px 16px;margin-bottom:8px;">'
        f'<div style="font-size:0.8rem;color:{fg};">Overall</div>'
        f'<div style="font-size:1.6rem;font-weight:600;color:{fg};line-height:1.2;">{label}</div>'
        f'<div style="font-size:0.85rem;color:{fg};">{html.escape(why)}</div></div>',
        unsafe_allow_html=True,
    )


def hazard_card(title, source, tier, code_label, code_value, notes=(), insurance=None):
    """One hazard card: tier, raw source code, insurance message (High+), notes."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if tier == "unknown":
            name, url = OFFICIAL_MAPS[title]
            st.warning(f"{source} didn't respond, so this hazard has no tier. Try again later, "
                       f"or check the official map: [{name}]({url})")
            return
        st.metric("Tier", TIER_LABELS[tier])
        st.caption(f"{code_label}: {code_value}")
        if insurance and tier in HIGH_PLUS:
            st.info(f"**Insurance:** {insurance}")
        for note in notes:
            if note:
                st.caption(note)


def set_query(address: str) -> None:
    st.session_state.address_input = address
    st.session_state.query = address


st.set_page_config(page_title="Property Hazard Check", page_icon="🛡️", layout="centered")
st.session_state.setdefault("query", None)

st.title("Property hazard check")
st.write(
    "Enter a California address to see its flood, wildfire, and earthquake exposure "
    "— and what each means for insurance."
)

with st.form("search"):
    st.text_input("Address", placeholder="2775 Embarcadero Rd, Palo Alto, CA 94303", key="address_input")
    if st.form_submit_button("Check address"):
        st.session_state.query = st.session_state.address_input

samples = [r for r in load_samples().values() if r["role"] in SAMPLE_LABELS]
samples.sort(key=lambda r: list(SAMPLE_LABELS).index(r["role"]))
st.caption("Try a sample:")
for col, row in zip(st.columns(len(samples)), samples):
    col.button(SAMPLE_LABELS[row["role"]], key=f"sample_{row['role']}", on_click=set_query,
               args=(row["address"],), use_container_width=True)

address = (st.session_state.query or "").strip()
if address:
    with st.spinner("Looking up address…"):
        try:
            g = geocode(address)
        except Exception:
            g = None
    if g is None:
        st.error("The address service (US Census Geocoder) didn't respond. "
                 "Try again in a moment, or try one of the samples, which work offline.")
    elif not g.found:
        st.error("Address not found. Check the spelling and include the city and ZIP, "
                 "or try one of the samples.")
    elif not g.in_california:
        st.warning(f"{g.matched_address} is outside California. This tool covers California only.")
    else:
        cached = cache.lookup(g.matched_address)
        if cached:
            f, w, e = cache.to_results(cached)
            as_of = f"Data as of {cached['fetched']} (cached)"
        else:
            with st.spinner("Checking FEMA, CAL FIRE, and CGS hazard maps…"):
                # Run the three sources at once; each one handles its own failure.
                with ThreadPoolExecutor(max_workers=3) as pool:
                    jobs = [pool.submit(fn, g.lat, g.lon) for fn in (lookup_flood, lookup_wildfire, lookup_earthquake)]
                    f, w, e = (j.result() for j in jobs)
            today = dt.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date().isoformat()
            as_of = f"Data as of {today} (live lookup)"

        f_tier = flood_tier(f.zone, f.subtype, f.error)
        w_tier = wildfire_tier(w.fhsz, w.error)
        e_tier = earthquake_tier(e)
        tiers = {"flood": f_tier, "wildfire": w_tier, "earthquake": e_tier}
        overall = overall_tier(tiers)

        st.subheader(g.matched_address)
        st.caption(f"{as_of} · {g.lat:.5f}, {g.lon:.5f} · location from {g.source}")

        worst = None
        if overall != "no_score":
            worst = next(name for name, t in tiers.items() if t == overall)
            if worst == "earthquake" and e.zones:
                worst += f" ({ZONE_NAMES[e.zones[0]].lower()})"
        missing = [name for name, t in tiers.items() if t in ("not_mapped", "unknown")]
        overall_card(overall, worst, overall != "no_score" and compound_flag(tiers), missing)

        area = {"SRA": "State Responsibility Area", "LRA": "Local Responsibility Area"}.get(w.area)
        c1, c2, c3 = st.columns(3)   # stack on narrow (mobile) screens
        with c1:
            hazard_card(
                "Flood", "FEMA", f_tier, "FEMA zone", f.zone or "No polygon",
                notes=[f.subtype.capitalize() if f.subtype else None,
                       MESSAGES["flood_not_mapped"] if f_tier == "not_mapped" else None],
                insurance=MESSAGES["flood_high_plus"],
            )
        with c2:
            hazard_card(
                "Wildfire", "CAL FIRE", w_tier, "CAL FIRE class", w.fhsz or "No polygon",
                notes=[{"not_mapped": MESSAGES["wildfire_not_mapped"],
                        "minimal": MESSAGES["wildfire_nonwildland"]}.get(w_tier, area)],
                insurance=MESSAGES["wildfire_high_plus"],
            )
        with c3:
            hazard_card(
                "Earthquake", "CGS earthquake", e_tier, "CGS zones",
                ", ".join(ZONE_NAMES[z] for z in e.zones) or "None",
                notes=[{"not_mapped": MESSAGES["earthquake_not_mapped"],
                        "moderate": MESSAGES["earthquake_moderate_floor"]}.get(e_tier)],
                insurance=MESSAGES["earthquake_high_plus"],
            )

st.divider()
with st.expander("How scoring works"):
    st.markdown(
        """
- **Tiers:** each hazard gets Minimal, Moderate, High, or Severe from public hazard maps —
  FEMA flood zones, CAL FIRE Fire Hazard Severity Zones (2025), and California Geological Survey earthquake zones.
- **Overall = worst single hazard.** One severe hazard is enough to cause insurance trouble.
- **Compound risk** is flagged when 2 or more hazards are High or above.
- **No data is never Minimal.** *Not mapped* means the source has no class at this point;
  *Unknown* means the lookup failed. Either one makes the overall **No Score**.
  CAL FIRE "NonWildland" is CAL FIRE's own non-wildland class and counts as Minimal.
- **Earthquake floor:** CGS zones map ground failure, not shaking, so anywhere outside a zone is
  at least Moderate.
- Sample addresses come from a baseline cache; other addresses are looked up live.

Full rules: [`config/scoring_rules.yaml`](https://github.com/bpananalytics/property-hazard-check/blob/main/config/scoring_rules.yaml)
"""
    )
st.caption(
    f"Rules {RULES['version']} · Not insurance advice. Results come from public hazard maps; "
    "insurers use their own models."
)
