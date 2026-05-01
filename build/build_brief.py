"""
Build Competitive_Landscape_Brief.docx — narrative summary of vendor profiles,
threat assessment, heat zones, and refinement suggestions.

Uses python-docx. US Letter (12240×15840 DXA), 1-inch margins, Arial,
smart quotes, real LevelFormat.BULLET for lists.
"""

import os

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor, Twips

from competitors import COMPETITORS, STATE_PENETRATION, vendor_state_total
from data import (STATE_COUNTS, STATE_NAMES, STATES, total_state_spend)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
DOCX_PATH = os.path.join(OUT_DIR, "Competitive_Landscape_Brief.docx")

ARIAL = "Arial"

# Smart quotes (per spec)
RSQUO = "’"  # &#x2019;


def fmt_usd(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    if n >= 1e6:  return f"${n/1e6:.0f}M"
    if n >= 1e3:  return f"${n/1e3:.0f}K"
    return f"${n:.0f}"


def fmt_int(n):
    return f"{int(round(n)):,}"


def set_run_font(run, size=11, bold=False, color=None):
    run.font.name = ARIAL
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    # Set East-Asian font as well so Word doesn't substitute
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), ARIAL)
    rFonts.set(qn("w:hAnsi"), ARIAL)
    rFonts.set(qn("w:eastAsia"), ARIAL)
    rFonts.set(qn("w:cs"), ARIAL)


def add_para(doc, text, size=11, bold=False, italic=False, color=None,
             align=None, space_after=6):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run(text)
    r.italic = italic
    set_run_font(r, size=size, bold=bold, color=color)
    return p


def add_heading(doc, text, level=1):
    sizes = {1: 18, 2: 13, 3: 11}
    bold = True
    color = "0F172A"
    if level == 1:
        size = sizes[1]
    elif level == 2:
        size = sizes[2]
    else:
        size = sizes[3]
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(12 if level <= 2 else 6)
    pf.space_after = Pt(6)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, color=color)
    return p


def add_bullets(doc, items):
    """Real LevelFormat.BULLET — uses python-docx 'List Bullet' style and
    sets each paragraph's font/size explicitly."""
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        pf = p.paragraph_format
        pf.space_after = Pt(2)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        r = p.runs[0] if p.runs else p.add_run("")
        # python-docx already added text via "List Bullet" — replace runs
        for r in list(p.runs):
            r.text = ""
        r = p.add_run(item)
        set_run_font(r, size=11)


def add_table(doc, headers, rows, col_widths_dxa):
    """Build a table with explicit widths. WidthType.DXA per spec."""
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False

    # Set tblW + columnWidths in DXA
    tbl = t._tbl
    tblPr = tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(sum(col_widths_dxa)))
    tblW.set(qn("w:type"), "dxa")

    tblGrid = tbl.find(qn("w:tblGrid"))
    if tblGrid is not None:
        tbl.remove(tblGrid)
    tblGrid = OxmlElement("w:tblGrid")
    for w in col_widths_dxa:
        gridCol = OxmlElement("w:gridCol")
        gridCol.set(qn("w:w"), str(w))
        tblGrid.append(gridCol)
    tbl.insert(list(tbl).index(tblPr) + 1, tblGrid)

    # Header
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.width = Twips(col_widths_dxa[i])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            for r in p.runs:
                r.text = ""
        p = cell.paragraphs[0]
        pf = p.paragraph_format
        pf.space_after = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        r = p.add_run(h)
        set_run_font(r, size=10, bold=True, color="FFFFFF")
        # Header shading
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "0F172A")
        tcPr.append(shd)

    # Body rows
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[1 + ri].cells[ci]
            cell.width = Twips(col_widths_dxa[ci])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            for p in cell.paragraphs:
                for r in p.runs:
                    r.text = ""
            p = cell.paragraphs[0]
            pf = p.paragraph_format
            pf.space_after = Pt(0)
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            r = p.add_run(str(val))
            set_run_font(r, size=10)

    return t


def build():
    doc = Document()

    # US Letter, 1-inch margins
    section = doc.sections[0]
    section.page_height = Twips(15840)  # 11in × 1440
    section.page_width = Twips(12240)   # 8.5in × 1440
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Default font on Normal style
    style = doc.styles["Normal"]
    style.font.name = ARIAL
    style.font.size = Pt(11)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), ARIAL)
    rfonts.set(qn("w:hAnsi"), ARIAL)
    rfonts.set(qn("w:eastAsia"), ARIAL)
    rfonts.set(qn("w:cs"), ARIAL)

    # ==== Title ====
    add_heading(doc, "Competitive Landscape Brief", level=1)
    add_para(doc, ("U.S. Local-Government Software Market — "
                    "Vendor Profiles, Threat Assessment, and Heat-Zone "
                    "Analysis"), size=12, italic=True, color="475569",
             space_after=12)

    # ==== Executive Summary ====
    add_heading(doc, "Executive Summary", level=2)
    total_spend = sum(total_state_spend(s) for s in STATES)
    total_entities = sum(STATE_COUNTS[s][0] + STATE_COUNTS[s][1]
                         + STATE_COUNTS[s][2] + STATE_COUNTS[s][3]
                         for s in STATES)
    total_customers = sum(vendor_state_total(v) for v in COMPETITORS)
    add_para(doc,
        f"The U.S. local-government software TAM is approximately "
        f"{fmt_usd(total_spend)} in annual operating spend across "
        f"{fmt_int(total_entities)} addressable entities (counties, "
        f"municipalities, townships, and special districts; school "
        f"districts excluded). Combined tracked-vendor footprint across the "
        f"six competitors profiled in this brief totals roughly "
        f"{fmt_int(total_customers)} customers — implying that even the "
        f"named incumbents collectively reach a fraction of total "
        f"addressable entities, leaving substantial white space, "
        f"particularly in sub-10K-population municipalities and townships.")
    add_para(doc,
        f"Tyler Technologies dominates the mid-to-large segment "
        f"({fmt_int(COMPETITORS['Tyler Technologies']['total'])} customers "
        f"published) with broad product coverage. Regional specialists "
        f"(BS&A in MI, Caselle in the Mountain West, gWorks in the Plains, "
        f"Muni-Link in PA{RSQUO}s utility billing niche, TownCloud in the "
        f"Southeast) hold defensible local positions but limited national "
        f"share. The headline opportunity sits in the long tail of small "
        f"municipalities and townships outside any incumbent{RSQUO}s home "
        f"region.")

    # ==== Methodology ====
    add_heading(doc, "Methodology", level=2)
    add_para(doc,
        "Entity counts are sourced from the 2022 Census of Governments. "
        "Operating spend per entity is computed as entity_count × "
        "average_bucket_population × per_capita_spend (anchored to "
        "the Census Annual Survey of State and Local Government Finances "
        "2022). Special-district spend uses a flat $7.6M average annual "
        "operating-spend per district. Per-vendor customer counts are "
        "published totals; per-state allocations weight HQ states, named "
        "case studies, and acquired-company home/service states, with a "
        "population-weighted residual. Each vendor{0}s allocated total is "
        "calibrated within ±15% of published.".format(RSQUO))

    # ==== At-a-Glance Comparison Table ====
    add_heading(doc, "At-a-Glance Vendor Comparison", level=2)
    rows = []
    for v, meta in COMPETITORS.items():
        sp = STATE_PENETRATION[v]
        top = sorted(sp.items(), key=lambda x: -x[1])[:2]
        top_str = ", ".join(f"{s} ({n})" for s, n in top)
        rows.append([
            v, meta["hq"], fmt_int(meta["total"]),
            meta["size_target"], top_str, meta["threat"].upper()
        ])
    # Total row width 6.5in = 9360 dxa
    add_table(doc,
              ["Vendor", "HQ", "Customers", "Size Target", "Top States", "Threat"],
              rows,
              col_widths_dxa=[1700, 600, 1100, 1900, 2700, 900])

    add_para(doc, "", space_after=0)  # spacer

    # ==== Vendor Profiles ====
    add_heading(doc, "Vendor Profiles", level=2)
    for v, meta in COMPETITORS.items():
        add_heading(doc, v, level=3)
        sp = STATE_PENETRATION[v]
        top5 = sorted(sp.items(), key=lambda x: -x[1])[:5]
        top5_str = ", ".join(f"{s} ({n})" for s, n in top5)

        add_para(doc, f"HQ: {meta['hq_state_full']} ({meta['hq']}) · "
                       f"Published customers: {fmt_int(meta['total'])} · "
                       f"Size target: {meta['size_target']} · "
                       f"Threat level: {meta['threat'].upper()}",
                 italic=True, color="475569", space_after=6)
        add_para(doc, f"Product focus: {meta['focus']}", space_after=6)
        add_para(doc, f"Top 5 states: {top5_str}", space_after=6)
        if meta.get("acquired"):
            add_para(doc, f"Notable M&A: {'; '.join(meta['acquired'])}",
                     space_after=6)
        add_para(doc, meta["notes"], space_after=6)

        add_para(doc, "Strengths", bold=True, space_after=2)
        add_bullets(doc, meta["strengths"])
        add_para(doc, "Weaknesses", bold=True, space_after=2)
        add_bullets(doc, meta["weaknesses"])

    # ==== Heat Zones ====
    add_heading(doc, "Heat Zones — High Competition vs. Greenfield",
                level=2)

    # Compute combined competitor presence per state
    combined = {st: sum(STATE_PENETRATION[v][st] for v in COMPETITORS)
                for st in STATES}
    addressable = {st: STATE_COUNTS[st][0] + STATE_COUNTS[st][1]
                       + STATE_COUNTS[st][2]
                   for st in STATES}
    pen = {st: combined[st] / addressable[st] if addressable[st] else 0
           for st in STATES}

    high = sorted(pen.items(), key=lambda x: -x[1])[:10]
    low = sorted([(s, p) for s, p in pen.items() if addressable[s] >= 100],
                 key=lambda x: x[1])[:10]

    add_para(doc, "Highest combined-vendor penetration "
                  "(competition density):", bold=True, space_after=4)
    add_bullets(doc, [
        f"{STATE_NAMES[s]} ({s}) — "
        f"{fmt_int(combined[s])} tracked customers across "
        f"{fmt_int(addressable[s])} entities ({p*100:.1f}%)"
        for s, p in high
    ])

    add_para(doc, "Lowest penetration / largest white space "
                  "(states with ≥100 entities):", bold=True,
             space_after=4)
    add_bullets(doc, [
        f"{STATE_NAMES[s]} ({s}) — "
        f"{fmt_int(combined[s])} tracked customers across "
        f"{fmt_int(addressable[s])} entities ({p*100:.1f}%)"
        for s, p in low
    ])

    # ==== Ways to sharpen ====
    add_heading(doc, "Ways to Sharpen This Further", level=2)
    add_bullets(doc, [
        ("Cooperative-purchasing data: Sourcewell, OMNIA Partners, BuyBoard "
         "publish awarded-vendor lists; tracking which vendors hold which "
         "co-op contracts shows where they{0}re positioned to be "
         "preferred-vendor.").format(RSQUO),
        ("GovShop / GovTribe / GovWin: federal-style contract intelligence "
         "with state and local awards to fingerprint named-customer wins "
         "by state."),
        ("G2 / Capterra / Gartner Peer Insights: customer-review "
         "geographic distribution as a sanity check on vendor footprint."),
        ("LinkedIn Sales Navigator: filter by current-employer = "
         "vendor + by-state to estimate field-sales density and customer "
         "service coverage."),
        ("Bond-disclosure documents (EMMA, MunicipalBonds.com): municipal "
         "ERP vendor sometimes listed in CAFR / ACFR financial statements "
         "or appendix vendor lists."),
        ("CIO interviews and CIO-focused media (e.g., Government "
         "Technology magazine, StateScoop, Route Fifty): qualitative reads "
         "on which vendors are gaining vs. losing in specific markets."),
        ("RFP-tracking services (BidNet, GovDeals, Demandstar, "
         "Periscope/Bonfire): live RFP feeds reveal which vendors are "
         "responding where, indicating active sales motion."),
    ])

    add_para(doc, "", space_after=0)
    add_para(doc, ("Refresh: Census of Governments runs every 5 years (next "
                    "2027). Re-baseline competitor totals every 6 months "
                    "as vendors publish new customer counts."),
             italic=True, color="475569", size=10)

    doc.save(DOCX_PATH)
    print(f"Wrote {DOCX_PATH}")


if __name__ == "__main__":
    build()
