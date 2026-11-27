# Property Hazard Check

Enter a California address and get a one-page report on its **flood, wildfire, and earthquake** exposure — plus what each hazard means for insurance.

> **Status:** In development (MVP). See the [project board](../../projects) and [milestones](../../milestones).

> **Not insurance advice.** Results come from public hazard maps. Insurers use their own models.

**Live app:** https://property-hazard-check.streamlit.app/

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How it works

1. **Geocode** the address to a point (US Census Geocoder).
2. **Check the cache** for a previous result.
3. **Look up hazard zones** at that point from public data sources.
4. **Score** each hazard (Minimal / Moderate / High / Severe) and roll up to an overall tier.
5. **Report** the tiers, raw zone codes, and insurance implications.

## Data sources

| Hazard | Source | Notes |
|---|---|---|
| Geocoding | US Census Geocoder | Free, no API key |
| Flood | FEMA National Flood Hazard Layer (NFHL) | Flood zone codes (A, AE, V, X…) |
| Wildfire | CAL FIRE Fire Hazard Severity Zones (2025) | Moderate / High / Very High |
| Earthquake | California Geological Survey (CGS) | Alquist-Priolo fault zones, liquefaction, landslide zones |

Endpoints live in [`config/sources.yaml`](config/sources.yaml).

## Scoring

Rules live in [`config/scoring_rules.yaml`](config/scoring_rules.yaml) — versioned, and shown on every report.

- **Overall tier = worst single hazard** (one severe hazard is enough to cause insurance trouble) — only when every hazard has a tier. Otherwise the overall is **No Score** (insufficient data); no guessing.
- **Compound flag** when 2+ hazards are High or above (scored reports only).
- **No data is never Minimal.** Two labels, kept separate:
  - **Not mapped** — the source has no class at this point (e.g. no CAL FIRE polygon, FEMA zone D). CAL FIRE "NonWildland" counts as Minimal.
  - **Unknown** — the lookup failed.
  Either one means the overall is **No Score**.
- Earthquake has a **Moderate floor**: CGS zones map ground failure, not shaking.

## Sample addresses

Public places used for demos and tests: [`data/sample_addresses.csv`](data/sample_addresses.csv).

## Reliability

- Pre-loaded cache for sample addresses (demos work even if a source is down).
- Daily health check via GitHub Actions; alerts on failure.
- Every result stores its fetch date and is shown as "Data as of …".

## Limitations

- California only.
- Public hazard zones ≠ insurer risk models.
- 2025 local fire zones were adopted by cities on different dates.

## Roadmap (post-MVP)

- dbt + BigQuery pipeline replacing live lookups
- Historical wildfire perimeters
- Side-by-side address comparison
