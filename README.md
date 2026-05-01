# Local Government TAM + Competitive Dashboard

A reusable analysis of the U.S. local-government software market that
combines **TAM sizing** (entity counts and operating spend by state ×
population bucket) with **competitive penetration** (where the named
competitors actually have customers and where the white space is).

## Deliverables

All three live in `TAM/`:

| File | Purpose |
| --- | --- |
| `Local_Government_TAM.xlsx` | Source of truth. Summary tab (state × bucket grid for both count and $), 51 per-state tabs, Methodology, Competitor Summary, Competitor Penetration. |
| `Local_Government_TAM_Dashboard.html` | Single-file interactive dashboard. Four tabs: TAM Overview, Heatmaps, State & Names overlay, Competitive Penetration. Works at `file://`, no fetch, embedded JSON. |
| `Competitive_Landscape_Brief.docx` | Narrative brief: vendor profiles, threat assessment, heat-zone analysis, refinement suggestions. |

## How the pieces fit

```
   2022 Census of Governments
              │
              ▼
        build/data.py            (STATE_COUNTS, BUCKETS, distributions,
              │                   per-capita spend, cost factors, skews)
   ┌──────────┼─────────────────────────┐
   ▼          ▼                          ▼
build_workbook.py   build_dashboard_v2.py   add_competitor_tab.py
                    build_brief.py
                    build_names_data.py     +  competitors.py
```

## Build

```bash
pip install openpyxl geonamescache python-docx formulas
cd build
python3 build_workbook.py
python3 add_competitor_tab.py
python3 build_names_data.py     # pre-bakes counties/cities
python3 build_dashboard_v2.py
python3 build_brief.py
python3 recalc.py               # caches formula values into the workbook
python3 validate.py             # 24-check end-to-end validation
```

## Key design decisions

- **Population buckets** are configurable in one place
  (`BUCKETS` in `data.py`). Change them and everything downstream
  re-derives.
- **Skew profiles** (`urban_strong` / `urban_mild` / `balanced` /
  `rural_mild` / `rural_strong`) override a national baseline
  distribution, so urban states tilt larger and rural states tilt
  smaller without writing 50 distinct distributions.
- **Cost factor** (`STATE_COST_FACTOR`) scales per-capita spend by
  state, anchored to BEA Regional Price Parities. CA = 1.45, MS = 0.80,
  etc.
- **Spend math** is transparent:
  `entities × avg_bucket_pop × per_capita_spend × state_cost_factor`.
  Easy to defend, easy to override.
- **JSON is the bridge** between the Excel build and the HTML
  dashboard — the dashboard never recomputes; it renders pre-baked
  numbers.
- **Competitor estimates** are calibrated to land within ±15% of each
  vendor's published customer total. Directionally honest, not
  to-the-individual-customer accurate.

## Refresh cadence

- Census of Governments runs every 5 years (next 2027). When refreshing,
  update `STATE_COUNTS` in `data.py` and the `# refreshed YYYY-MM-DD`
  comment.
- Per-capita spend (Annual Survey of State and Local Govt Finances) is
  yearly; refresh `SPEND_PER_CAPITA` annually.
- Review competitor totals every 6 months; recalibrate `STATE_PENETRATION`
  in `competitors.py`.

## Adding a new competitor

Two edits in `competitors.py`:

1. Add a metadata block to `COMPETITORS`.
2. Add a per-state allocation to `STATE_PENETRATION` summing to ±15% of
   the published total.

Re-run `add_competitor_tab.py` and `build_dashboard_v2.py`.

## Known limitations

- Per-bucket population averages are coarse; very large cities pull the
  100K+ bucket up.
- Per-capita spend is uniform within each bucket (the cost factor is the
  only state-level lever).
- Per-state ranking is **directional**. States with many small munis
  (IL, MO, PA) tend to be over-ranked; states with few large munis
  (CA, NY) tend to be under-ranked. National total reconciles within
  spec; consume per-state TAM as a directional signal, not a precise
  ranking.
- Special districts vary wildly in budget (transit authorities >>>
  small water districts) — the flat $7.6M average is a simplification.
