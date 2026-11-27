# Data source evaluation notes

One note per source in [`config/sources.yaml`](../config/sources.yaml). Researched November 2026.
"Last update" dates come from each layer's ArcGIS metadata or the publisher's catalog page on that date.

| Source | Publisher | Used for | Last update (checked Nov 2026) |
|---|---|---|---|
| Census Geocoder | US Census Bureau | Address → point | Rolling ("Current" benchmark) |
| NFHL flood zones | FEMA | Flood tier | Rolling, as new maps take effect |
| FHSZ 2025, LRA | CAL FIRE / State Fire Marshal | Wildfire tier (cities) | Map dated Mar 24, 2025; layer edited Feb 1, 2026 |
| FHSZ, SRA | CAL FIRE / State Fire Marshal | Wildfire tier (rural) | Effective Apr 1, 2024; layer edited May 4, 2026 |
| Alquist-Priolo fault zones | California Geological Survey | Earthquake: Severe | Layer edited Nov 19, 2025 |
| Liquefaction / landslide zones | California Geological Survey | Earthquake: High | Updated with new quadrangle releases |
| Unevaluated areas | California Geological Survey | Earthquake: Not mapped | Last modified Nov 20, 2025 |

---

## US Census Geocoder

- **Publisher:** US Census Bureau.
- **What it measures:** turns a one-line address into a point (lat/lon) using the address ranges in the Census Bureau's MAF/TIGER database — the same ranges used for censuses and surveys.
- **Coverage:** US street addresses. City-style addresses work best; new subdivisions, PO boxes, and some landmark addresses don't match.
- **Last update / cadence:** the app uses the `Public_AR_Current` benchmark. "Current" always points to the latest snapshot and changes as the underlying dataset changes, so there's no fixed date.
- **Key fields:** `matchedAddress` (the standardized address shown on the report), `coordinates.x` / `.y` (lon / lat), `addressComponents.state` (used for the California-only check). No match = empty `addressMatches`.
- **Known limits:**
  - Address-range interpolation: the point is estimated along the street segment, not the building or parcel centroid. Near a zone boundary, the point can land on the wrong side.
  - Some sample places (e.g. landmarks) don't match, which is why samples use stored coordinates.
  - No API key and no published rate limit, but no uptime guarantee either.

## FEMA National Flood Hazard Layer (NFHL)

- **Publisher:** Federal Emergency Management Agency (FEMA), National Flood Insurance Program.
- **What it measures:** the current *effective* regulatory flood zones — a compilation of Flood Insurance Rate Map (FIRM) databases plus Letters of Map Revision. Layer 28, `S_Fld_Haz_Ar`, holds the flood zone polygons.
- **Coverage:** areas where FEMA maps have been modernized (digital). Most urban areas in California are covered; some rural areas have only older paper maps, which show up here as no polygon or zone D.
- **Last update / cadence:** continuous. The NFHL is updated as new studies and map revisions reach their effective date. There's no single "as of" date; each community's map has its own effective date.
- **Key fields:**
  - `FLD_ZONE` — the zone code. A, AE, AH, AO, AR, A99 = 1% annual-chance flood (Special Flood Hazard Area); V, VE = coastal with wave action; X = outside the 1% area; D = possible but undetermined.
  - `ZONE_SUBTY` — distinguishes shaded X ("0.2 PCT ANNUAL CHANCE FLOOD HAZARD", the 500-year floodplain) from unshaded X ("AREA OF MINIMAL FLOOD HAZARD"), and marks regulatory floodways.
  - `SFHA_TF` — T/F: inside a Special Flood Hazard Area. This is what triggers mandatory flood insurance on federally backed mortgages.
- **Known limits:**
  - Regulatory maps, not risk models: they show where flood insurance rules apply, not every place that can flood. Many flood claims come from outside mapped high-risk zones.
  - Preliminary (not yet effective) maps aren't in this layer.
  - Zone D and missing polygons are mapped to **Not mapped**, never Minimal.

## CAL FIRE Fire Hazard Severity Zones — Local Responsibility Area (LRA), 2025

- **Publisher:** CAL FIRE, Office of the State Fire Marshal (OSFM).
- **What it measures:** fire hazard severity (Moderate, High, Very High) based on fuels, fire history, weather, and terrain — expected fire behavior, not the chance of a fire in a given year. LRA covers land where cities and counties are responsible for fire protection.
- **Coverage:** statewide LRA. Unlike the 2007–2011 maps, which only showed Very High in LRA, the 2025 maps classify all three levels. The LRA layer also includes explicit **NonWildland** polygons (`FHSZ = -3`).
- **Last update / cadence:** the layer is the map dated March 24, 2025 (Southern California; Northern and Central California were released earlier in 2025). Layer last edited February 1, 2026. Typically updated about every ten years.
- **Key fields:** `FHSZ` (numeric class; −3 = NonWildland), `FHSZ_Description` ("Moderate", "High", "Very High", "NonWildland"), `SRA` (responsibility area flag).
- **Known limits:**
  - **Local adoption dates vary.** OSFM issues *recommended* LRA maps; each city adopts them by ordinance (generally within 120 days) and may add zones or raise levels, but not lower them. Legal status at a given address depends on the local adoption date.
  - Hazard, not risk: doesn't account for home hardening, defensible space, or insurer wildfire scores.
  - NonWildland is scored **Minimal** (decision Nov 2026); insurers may still rate wildfire risk using their own models.

## CAL FIRE Fire Hazard Severity Zones — State Responsibility Area (SRA)

- **Publisher:** CAL FIRE, Office of the State Fire Marshal.
- **What it measures:** same three classes as LRA, for land where the state is responsible for wildfire protection (mostly rural and wildland areas).
- **Coverage:** statewide SRA. City addresses normally get no hit here; the app checks both layers and keeps the more severe class.
- **Last update / cadence:** SRA maps took effect April 1, 2024 (classes went through the Office of Administrative Law rulemaking, with public comments through Aug 9, 2023). Layer last edited May 4, 2026.
- **Key fields:** same as LRA, but prefixed (`xxFHSZSRA25_3_FHSZ_Description`, etc.); the code matches on the field-name suffix.
- **Known limits:** federal land (e.g. national forests) is in neither layer, so it comes back **Not mapped**.

## CGS Alquist-Priolo Earthquake Fault Zones

- **Publisher:** California Geological Survey (CGS), Department of Conservation.
- **What it measures:** regulatory zones around active faults where surface fault rupture is likely, under the Alquist-Priolo Earthquake Fault Zoning Act (1972). Zone status must be disclosed when a property is sold.
- **Coverage:** mapped quadrangles along active faults; CGS still releases new and revised zone maps (most recently Nov 2025).
- **Last update / cadence:** layer last edited November 19, 2025. Updated whenever CGS releases new or revised zone maps.
- **Key fields:** the app only checks whether the point falls in a zone (`OBJECTID` returned). `QUAD_NAME`, `ZN_RELEASED`, `ZN_REVISED` give the quadrangle and zone dates if you need them.
- **Known limits:**
  - CGS says the maps may not show every fault capable of surface rupture.
  - A fault zone maps rupture risk, not shaking. Shaking risk applies statewide, which is why the app has a **Moderate earthquake floor**.

## CGS Seismic Hazard Zones — liquefaction and landslide

- **Publisher:** California Geological Survey (Seismic Hazards Program).
- **What it measures:** areas where liquefaction or earthquake-induced landslides may occur during strong shaking, under the Seismic Hazards Mapping Act (1990). Developers in these zones may have to investigate and mitigate the hazard during permitting.
- **Coverage:** only evaluated quadrangles — mostly the Bay Area, Los Angeles, and other urban regions. Much of the state isn't evaluated yet (see next section).
- **Last update / cadence:** updated whenever CGS releases new quadrangle maps.
- **Key fields:** presence of a polygon at the point. `QUAD_NAME`, `RELEASED` give the source map.
- **Known limits:** CGS notes the maps may not show every area prone to liquefaction or landslides. A zone means a site investigation may be required, not that failure will happen.

## CGS Seismic Hazard Zones — unevaluated areas

- **Publisher:** California Geological Survey.
- **What it measures:** quadrangles CGS has *not yet evaluated* for liquefaction or landslides.
- **Coverage:** statewide.
- **Last update / cadence:** last modified November 20, 2025; shrinks as new quadrangles are mapped.
- **Key fields:** presence of a polygon at the point.
- **Known limits:** in these areas, "no liquefaction zone" means "not studied," not "no hazard." The app reports earthquake as **Not mapped** here instead of applying the Moderate floor.

---

## Sources

- Census Geocoder API docs: https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html
- FEMA NFHL: https://www.fema.gov/flood-maps/national-flood-hazard-layer
- CAL FIRE / OSFM Fire Hazard Severity Zones: https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- CGS EQ Zapp: https://www.conservation.ca.gov/cgs/sh/eqzapp
- CGS Seismic Hazards Program, unevaluated areas: https://catalog.data.gov/dataset/cgs-seismic-hazards-program-unevaluated-areas
- Layer metadata: each URL in `config/sources.yaml` with `?f=json`
