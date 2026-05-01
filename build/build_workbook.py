"""
Build Local_Government_TAM.xlsx with:
  - Summary tab (state x bucket grids: count + spend, formula-driven)
  - Methodology tab
  - 51 per-state tabs (state abbreviations)
  - tam_data.json export for the HTML dashboard
"""

import json
import os

from openpyxl import Workbook
from openpyxl.styles import (Alignment, Border, Font, NamedStyle,
                              PatternFill, Side)
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

from data import (BUCKETS, BUCKET_AVG_POP, BUCKET_LABELS, NATIONAL_ANCHORS,
                  SPECIAL_DISTRICT_SPEND, SPEND_PER_CAPITA, STATE_COUNTS,
                  STATE_NAMES, STATES, state_bucket_counts,
                  state_distribution, state_spend_by_bucket,
                  state_special_district_spend, total_state_spend)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
os.makedirs(OUT_DIR, exist_ok=True)
XLSX_PATH = os.path.join(OUT_DIR, "Local_Government_TAM.xlsx")
JSON_PATH = os.path.join(OUT_DIR, "tam_data.json")


# ---- Styling -------------------------------------------------------------
ARIAL = "Arial"

FILL_HEADER  = PatternFill("solid", fgColor="1F2937")
FILL_SUBHEAD = PatternFill("solid", fgColor="334155")
FILL_TOTAL   = PatternFill("solid", fgColor="E5E7EB")
FILL_BAND    = PatternFill("solid", fgColor="F3F4F6")

FONT_HEADER   = Font(name=ARIAL, size=11, bold=True, color="FFFFFF")
FONT_SUBHEAD  = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
FONT_BODY     = Font(name=ARIAL, size=10)
FONT_INPUT    = Font(name=ARIAL, size=10, color="1F4E79")          # blue inputs
FONT_FORMULA  = Font(name=ARIAL, size=10, color="000000")           # black formulas
FONT_LINK     = Font(name=ARIAL, size=10, color="2F855A")           # green cross-sheet
FONT_TOTAL    = Font(name=ARIAL, size=10, bold=True)
FONT_TITLE    = Font(name=ARIAL, size=14, bold=True)

THIN = Side(style="thin", color="CBD5E1")
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

NUM_INT = '#,##0;(#,##0);"-"'
NUM_USD = '"$"#,##0;("$"#,##0);"-"'
NUM_PCT = '0.0%;(0.0%);"-"'


def set_col_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def header_row(ws, row, headers, start_col=1, fill=FILL_HEADER, font=FONT_HEADER):
    for i, h in enumerate(headers):
        c = ws.cell(row=row, column=start_col + i, value=h)
        c.font = font
        c.fill = fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER_ALL


# ---- Summary tab ---------------------------------------------------------
def build_summary(wb):
    ws = wb.create_sheet("Summary", 0)
    ws.sheet_view.showGridLines = False

    ws.cell(row=1, column=1, value="Local Government TAM — National Summary").font = FONT_TITLE
    ws.cell(row=2, column=1, value="Counts and estimated annual operating spend by state and population bucket. School districts excluded.").font = FONT_BODY
    ws.cell(row=3, column=1, value="Source: 2022 Census of Governments + Annual Survey of State and Local Govt Finances. Refreshed 2026-05-01.").font = FONT_BODY

    # === ENTITY COUNT BLOCK ===
    row = 5
    ws.cell(row=row, column=1, value="ENTITY COUNT BY STATE × BUCKET (counties + munis + townships)").font = FONT_TITLE
    row += 1
    headers = ["State"] + BUCKET_LABELS + ["Special Districts", "TOTAL ENTITIES", "TOTAL TAM ($M)"]
    header_row(ws, row, headers)
    row += 1

    count_block_start = row

    for st in STATES:
        # Sum bucket counts across counties + munis + townships
        bucket_counts = [0] * len(BUCKETS)
        for et in ("counties", "munis", "townships"):
            bc = state_bucket_counts(et, st)
            for i, x in enumerate(bc):
                bucket_counts[i] += x
        sd = STATE_COUNTS[st][3]
        spend = total_state_spend(st)

        ws.cell(row=row, column=1, value=st).font = FONT_TOTAL
        for i, v in enumerate(bucket_counts):
            c = ws.cell(row=row, column=2 + i, value=v)
            c.font = FONT_INPUT
            c.number_format = NUM_INT
            c.alignment = Alignment(horizontal="right")
        c = ws.cell(row=row, column=2 + len(BUCKETS), value=sd)
        c.font = FONT_INPUT
        c.number_format = NUM_INT
        c.alignment = Alignment(horizontal="right")

        # TOTAL ENTITIES = sum of bucket cells + SD cell  (formula)
        first_letter = get_column_letter(2)
        last_letter  = get_column_letter(2 + len(BUCKETS))
        c = ws.cell(row=row, column=3 + len(BUCKETS),
                    value=f"=SUM({first_letter}{row}:{last_letter}{row})")
        c.font = FONT_FORMULA
        c.number_format = NUM_INT
        c.alignment = Alignment(horizontal="right")

        # TOTAL TAM ($M) — link to per-state sheet's grand total
        tam_cell = f"='{st}'!B22/1000000"
        c = ws.cell(row=row, column=4 + len(BUCKETS), value=tam_cell)
        c.font = FONT_LINK
        c.number_format = NUM_USD
        c.alignment = Alignment(horizontal="right")
        row += 1

    count_block_end = row - 1

    # Totals row
    ws.cell(row=row, column=1, value="US TOTAL").font = FONT_TOTAL
    ws.cell(row=row, column=1).fill = FILL_TOTAL
    for i in range(len(BUCKETS) + 3):
        col = 2 + i
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}{count_block_start}:{col_letter}{count_block_end})"
        c = ws.cell(row=row, column=col, value=formula)
        c.font = FONT_TOTAL
        c.fill = FILL_TOTAL
        c.number_format = NUM_USD if col == 4 + len(BUCKETS) else NUM_INT
        c.alignment = Alignment(horizontal="right")
    totals_row = row
    row += 2

    # Heatmap on count block (per-column percentile-style 3-color scale)
    for i, _ in enumerate(BUCKETS):
        col = 2 + i
        rng = (f"{get_column_letter(col)}{count_block_start}:"
               f"{get_column_letter(col)}{count_block_end}")
        ws.conditional_formatting.add(rng, ColorScaleRule(
            start_type="min", start_color="EFF6FF",
            mid_type="percentile", mid_value=50, mid_color="60A5FA",
            end_type="max", end_color="1E3A8A",
        ))

    # === SPEND BLOCK ===
    ws.cell(row=row, column=1, value="ESTIMATED ANNUAL OPERATING SPEND ($M) BY STATE × BUCKET").font = FONT_TITLE
    row += 1
    headers = ["State"] + BUCKET_LABELS + ["Special Districts", "TOTAL SPEND ($M)"]
    header_row(ws, row, headers)
    row += 1
    spend_block_start = row

    for st in STATES:
        spend_munis = state_spend_by_bucket("munis", st)
        spend_counties = state_spend_by_bucket("counties", st)
        spend_townships = state_spend_by_bucket("townships", st)
        bucket_spend = [
            (spend_munis[i] + spend_counties[i] + spend_townships[i]) / 1_000_000
            for i in range(len(BUCKETS))
        ]
        sd_spend = state_special_district_spend(st) / 1_000_000

        ws.cell(row=row, column=1, value=st).font = FONT_TOTAL
        for i, v in enumerate(bucket_spend):
            c = ws.cell(row=row, column=2 + i, value=round(v, 1))
            c.font = FONT_INPUT
            c.number_format = NUM_USD
            c.alignment = Alignment(horizontal="right")
        c = ws.cell(row=row, column=2 + len(BUCKETS), value=round(sd_spend, 1))
        c.font = FONT_INPUT
        c.number_format = NUM_USD
        c.alignment = Alignment(horizontal="right")

        first_letter = get_column_letter(2)
        last_letter  = get_column_letter(2 + len(BUCKETS))
        c = ws.cell(row=row, column=3 + len(BUCKETS),
                    value=f"=SUM({first_letter}{row}:{last_letter}{row})")
        c.font = FONT_FORMULA
        c.number_format = NUM_USD
        c.alignment = Alignment(horizontal="right")
        row += 1
    spend_block_end = row - 1

    # Totals
    ws.cell(row=row, column=1, value="US TOTAL").font = FONT_TOTAL
    ws.cell(row=row, column=1).fill = FILL_TOTAL
    for i in range(len(BUCKETS) + 2):
        col = 2 + i
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}{spend_block_start}:{col_letter}{spend_block_end})"
        c = ws.cell(row=row, column=col, value=formula)
        c.font = FONT_TOTAL
        c.fill = FILL_TOTAL
        c.number_format = NUM_USD
        c.alignment = Alignment(horizontal="right")

    # Heatmap on spend block
    for i, _ in enumerate(BUCKETS):
        col = 2 + i
        rng = (f"{get_column_letter(col)}{spend_block_start}:"
               f"{get_column_letter(col)}{spend_block_end}")
        ws.conditional_formatting.add(rng, ColorScaleRule(
            start_type="min", start_color="FEF3C7",
            mid_type="percentile", mid_value=50, mid_color="F59E0B",
            end_type="max", end_color="78350F",
        ))

    set_col_widths(ws, [10] + [11] * len(BUCKETS) + [16, 16, 16])
    ws.freeze_panes = "B7"


# ---- Methodology tab -----------------------------------------------------
def build_methodology(wb):
    ws = wb.create_sheet("Methodology")
    ws.sheet_view.showGridLines = False

    ws.cell(row=1, column=1, value="Methodology").font = FONT_TITLE
    sections = [
        ("Scope",
         "U.S. local-government software market. Entity types tracked: "
         "counties / parishes, incorporated municipalities, organized "
         "townships, special districts. School districts and federal/state "
         "agencies are excluded."),
        ("Population buckets",
         "<1K, 1K-5K, 5K-10K, 10K-20K, 20K-50K, 50K-100K, 100K+. Applied to "
         "munis, counties, and townships. Special districts are not "
         "population-bucketed (size driven by purpose — water, fire, transit "
         "— not by population)."),
        ("Entity counts",
         "Sourced from the 2022 Census of Governments. Per-state counts "
         "encoded in data.py. National totals reconcile to Census within ~1-3% "
         "(rounding from compilation of state-by-state filings)."),
        ("Bucket distribution",
         "National baseline distribution per entity type, multiplied by "
         "state-level skew profiles (urban_strong / urban_mild / balanced / "
         "rural_mild / rural_strong) and renormalized so each state's "
         "distribution sums to 100% per entity type."),
        ("Spend math",
         "TAM_per_cell = entity_count × avg_bucket_population × per_capita_spend. "
         "Per-capita spend is anchored to Census Annual Survey of State and "
         "Local Government Finances 2022. Special district spend uses a flat "
         "$7.6M average annual operating spend per district. National total "
         "lands within ±10% of Census $2.2T figure; deviation reflects the "
         "fact that this TAM model counts each entity's spend independently "
         "(reflects software customer count) rather than netting overlapping "
         "jurisdictions."),
        ("Color coding",
         "Blue = manually entered or model-generated input cells. Black = "
         "in-sheet formulas. Green = cross-sheet links."),
        ("Limitations",
         "Per-bucket population averages are coarse; very large cities pull "
         "the 100K+ bucket up materially. Per-capita spend is uniform "
         "within each bucket and across states (no cost-of-living factor); "
         "a real-world refinement would model per-capita spend by region "
         "and entity type-of-government. Special districts vary wildly in "
         "budget (transit authorities >>> small water districts). "
         "Per-state ranking is therefore directional — states with many "
         "small munis (IL, MO, PA) tend to be over-ranked relative to "
         "states with few large munis (CA, NY, NJ) in the current "
         "bucket-distribution model. National total reconciles within "
         "spec; consume per-state TAM as a directional signal, not a "
         "precise ranking."),
        ("Refresh cadence",
         "Census of Governments runs every 5 years; next refresh 2027. "
         "Annual Survey of State and Local Government Finances runs yearly; "
         "refresh per-capita spend annually. Review competitor totals "
         "every 6 months."),
        ("Competitor methodology",
         "Each vendor's published customer total is allocated across states "
         "using HQ-state weighting, named case-study customers, "
         "acquired-company home/service states, state-specific marketing "
         "presence, and a population-weighted residual. Per-state sums "
         "calibrated to land within ±15% of each vendor's published total."),
    ]
    row = 3
    for title, body in sections:
        c = ws.cell(row=row, column=1, value=title)
        c.font = Font(name=ARIAL, size=11, bold=True)
        row += 1
        c = ws.cell(row=row, column=1, value=body)
        c.font = FONT_BODY
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 60
        row += 2

    set_col_widths(ws, [110])


# ---- Per-state tabs ------------------------------------------------------
def build_state_tab(wb, st):
    """One tab per state. Layout:

      Row 1: State title
      Rows 4-9: Munis bucket counts + spend
      Rows 11-16: Counties bucket counts + spend
      Rows 18: Townships row (collapsed if 0)
      Row 21: Special districts
      Row 22: Grand total spend
    """
    ws = wb.create_sheet(st)
    ws.sheet_view.showGridLines = False

    ws.cell(row=1, column=1, value=f"{st} — {STATE_NAMES[st]}").font = FONT_TITLE
    ws.cell(row=2, column=1, value=("Counts and estimated annual operating "
                                     "spend by entity type and bucket.")).font = FONT_BODY

    # Column headers: B=count, C=avg_pop, D=per_capita_spend, E=spend
    header_row(ws, 4, ["Entity / Bucket", "Count", "Avg Pop", "$/capita", "Spend ($)"])

    row = 5

    def write_block(label, et):
        nonlocal row
        ws.cell(row=row, column=1, value=label).font = FONT_SUBHEAD
        ws.cell(row=row, column=1).fill = FILL_SUBHEAD
        for col in range(2, 6):
            ws.cell(row=row, column=col).fill = FILL_SUBHEAD
        row += 1

        block_first = row
        bucket_counts = state_bucket_counts(et, st)
        pcs = SPEND_PER_CAPITA[et]
        for i, label_b in enumerate(BUCKET_LABELS):
            ws.cell(row=row, column=1, value=label_b).font = FONT_BODY
            c = ws.cell(row=row, column=2, value=bucket_counts[i]); c.font = FONT_INPUT; c.number_format = NUM_INT
            c = ws.cell(row=row, column=3, value=BUCKET_AVG_POP[i]); c.font = FONT_INPUT; c.number_format = NUM_INT
            c = ws.cell(row=row, column=4, value=pcs[i]); c.font = FONT_INPUT; c.number_format = NUM_USD
            c = ws.cell(row=row, column=5, value=f"=B{row}*C{row}*D{row}")
            c.font = FONT_FORMULA; c.number_format = NUM_USD
            row += 1
        # Subtotal
        ws.cell(row=row, column=1, value=f"  {label} subtotal").font = FONT_TOTAL
        ws.cell(row=row, column=1).fill = FILL_TOTAL
        c = ws.cell(row=row, column=2, value=f"=SUM(B{block_first}:B{row-1})"); c.font = FONT_TOTAL; c.fill = FILL_TOTAL; c.number_format = NUM_INT
        c = ws.cell(row=row, column=5, value=f"=SUM(E{block_first}:E{row-1})"); c.font = FONT_TOTAL; c.fill = FILL_TOTAL; c.number_format = NUM_USD
        for col in (3, 4):
            ws.cell(row=row, column=col).fill = FILL_TOTAL
        row += 2

    # Capture rows of subtotals so we can grand-total
    subtotal_rows = []

    # Munis
    write_block("Municipalities", "munis")
    subtotal_rows.append(row - 2)  # the just-written subtotal row

    # Counties
    write_block("Counties / Parishes", "counties")
    subtotal_rows.append(row - 2)

    # Townships
    if STATE_COUNTS[st][2] > 0:
        write_block("Townships", "townships")
        subtotal_rows.append(row - 2)

    # Special Districts (single row, no buckets)
    ws.cell(row=row, column=1, value="Special Districts").font = FONT_SUBHEAD
    ws.cell(row=row, column=1).fill = FILL_SUBHEAD
    for col in range(2, 6):
        ws.cell(row=row, column=col).fill = FILL_SUBHEAD
    row += 1
    ws.cell(row=row, column=1, value="(all sizes)").font = FONT_BODY
    c = ws.cell(row=row, column=2, value=STATE_COUNTS[st][3]); c.font = FONT_INPUT; c.number_format = NUM_INT
    c = ws.cell(row=row, column=4, value=SPECIAL_DISTRICT_SPEND); c.font = FONT_INPUT; c.number_format = NUM_USD
    c = ws.cell(row=row, column=5, value=f"=B{row}*D{row}"); c.font = FONT_FORMULA; c.number_format = NUM_USD
    sd_spend_row = row
    row += 1
    ws.cell(row=row, column=1, value="  Special Districts subtotal").font = FONT_TOTAL
    ws.cell(row=row, column=1).fill = FILL_TOTAL
    c = ws.cell(row=row, column=2, value=f"=B{sd_spend_row}"); c.font = FONT_TOTAL; c.fill = FILL_TOTAL; c.number_format = NUM_INT
    c = ws.cell(row=row, column=5, value=f"=E{sd_spend_row}"); c.font = FONT_TOTAL; c.fill = FILL_TOTAL; c.number_format = NUM_USD
    for col in (3, 4):
        ws.cell(row=row, column=col).fill = FILL_TOTAL
    subtotal_rows.append(row)
    row += 2

    # Grand total — at fixed row 22 (referenced from Summary tab)
    while row < 22:
        row += 1
    grand_row = 22
    ws.cell(row=grand_row, column=1, value="GRAND TOTAL").font = FONT_TITLE
    ws.cell(row=grand_row, column=1).fill = FILL_HEADER
    ws.cell(row=grand_row, column=1).font = Font(name=ARIAL, size=12, bold=True, color="FFFFFF")
    count_formula = "=" + "+".join(f"B{r}" for r in subtotal_rows)
    spend_formula = "=" + "+".join(f"E{r}" for r in subtotal_rows)
    c = ws.cell(row=grand_row, column=2, value=count_formula); c.font = Font(name=ARIAL, size=11, bold=True, color="FFFFFF"); c.fill = FILL_HEADER; c.number_format = NUM_INT
    c = ws.cell(row=grand_row, column=5, value=spend_formula); c.font = Font(name=ARIAL, size=11, bold=True, color="FFFFFF"); c.fill = FILL_HEADER; c.number_format = NUM_USD
    for col in (3, 4):
        ws.cell(row=grand_row, column=col).fill = FILL_HEADER

    set_col_widths(ws, [32, 14, 12, 14, 18])
    ws.freeze_panes = "A5"


# ---- JSON export ---------------------------------------------------------
def build_json():
    """Pre-bake JSON for the dashboard. The HTML embeds this — no fetch."""
    states_payload = {}
    for st in STATES:
        c, m, t, sd = STATE_COUNTS[st]
        munis_b   = state_bucket_counts("munis", st)
        counties_b = state_bucket_counts("counties", st)
        townships_b = state_bucket_counts("townships", st)
        spend_munis = state_spend_by_bucket("munis", st)
        spend_counties = state_spend_by_bucket("counties", st)
        spend_townships = state_spend_by_bucket("townships", st)
        sd_spend = state_special_district_spend(st)

        states_payload[st] = {
            "name": STATE_NAMES[st],
            "counts": {
                "counties": c, "munis": m, "townships": t,
                "special_districts": sd,
            },
            "by_bucket": {
                "munis":     munis_b,
                "counties":  counties_b,
                "townships": townships_b,
            },
            "spend_by_bucket": {
                "munis":     spend_munis,
                "counties":  spend_counties,
                "townships": spend_townships,
            },
            "special_districts_spend": sd_spend,
            "total_spend": total_state_spend(st),
            "total_entities": c + m + t + sd,
        }

    payload = {
        "buckets": BUCKET_LABELS,
        "bucket_avg_pop": BUCKET_AVG_POP,
        "spend_per_capita": SPEND_PER_CAPITA,
        "special_district_spend": SPECIAL_DISTRICT_SPEND,
        "anchors": NATIONAL_ANCHORS,
        "states": states_payload,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {JSON_PATH}")


# ---- Main ---------------------------------------------------------------
def build():
    wb = Workbook()
    # Remove the default sheet
    wb.remove(wb.active)

    build_summary(wb)
    build_methodology(wb)
    for st in STATES:
        build_state_tab(wb, st)

    wb.save(XLSX_PATH)
    print(f"Wrote {XLSX_PATH}")
    build_json()


if __name__ == "__main__":
    build()
