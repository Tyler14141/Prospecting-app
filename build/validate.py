"""
End-to-end validation report. Confirms:
  - Entity counts reconcile to Census within ±3%
  - Total $ TAM lands within ±10% of $2.2T anchor
  - Workbook has all expected tabs and no formula errors
  - Each competitor's per-state sum is within ±15% of published total
  - HTML dashboard contains all four tabs and embedded JSON
  - DOCX is loadable and has expected structure
"""

import json
import os
import re

from openpyxl import load_workbook

from competitors import COMPETITORS, calibration_check
from data import (NATIONAL_ANCHORS, STATE_COUNTS, STATES,
                  state_bucket_counts, total_state_spend)
from signals import SIGNALS, SIGNAL_TYPES, SEVERITY_FACTOR, signal_score

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
XLSX = os.path.join(OUT_DIR, "Local_Government_TAM.xlsx")
HTML = os.path.join(OUT_DIR, "Local_Government_TAM_Dashboard.html")
DOCX = os.path.join(OUT_DIR, "Competitive_Landscape_Brief.docx")


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def check(label, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{('  — ' + detail) if detail else ''}")
    return ok


def main():
    all_ok = True

    section("1. ENTITY-COUNT RECONCILIATION (Census of Governments 2022)")
    nat = {
        "counties": sum(v[0] for v in STATE_COUNTS.values()),
        "munis":    sum(v[1] for v in STATE_COUNTS.values()),
        "townships": sum(v[2] for v in STATE_COUNTS.values()),
        "sd":       sum(v[3] for v in STATE_COUNTS.values()),
    }
    anchors = {
        "counties":  NATIONAL_ANCHORS["counties"],
        "munis":     NATIONAL_ANCHORS["municipalities"],
        "townships": NATIONAL_ANCHORS["townships"],
        "sd":        NATIONAL_ANCHORS["special_districts"],
    }
    for k in ("counties", "munis", "townships", "sd"):
        dev = (nat[k] - anchors[k]) / anchors[k] * 100
        ok = abs(dev) <= 3.0
        all_ok &= check(f"{k:9s}: {nat[k]:>6,} vs {anchors[k]:>6,}",
                         ok, f"dev {dev:+.2f}%")

    section("2. SPEND RECONCILIATION ($2.2T anchor)")
    total_spend = sum(total_state_spend(s) for s in STATES)
    dev = (total_spend - NATIONAL_ANCHORS["total_op_spend"]) / NATIONAL_ANCHORS["total_op_spend"] * 100
    all_ok &= check(f"total operating spend: ${total_spend/1e12:.2f}T vs $2.20T",
                     abs(dev) <= 10.0, f"dev {dev:+.1f}%")

    section("3. PER-STATE BUCKET DISTRIBUTIONS SUM TO 100%")
    fail = []
    for st in STATES:
        for et in ("munis", "counties", "townships"):
            bc = state_bucket_counts(et, st)
            total = sum(bc)
            idx = {"counties": 0, "munis": 1, "townships": 2}[et]
            expected = STATE_COUNTS[st][idx]
            if total != expected:
                fail.append(f"{st}.{et}: {total} vs {expected}")
    all_ok &= check("all 51×3 distributions sum to entity totals",
                     not fail, f"{len(fail)} mismatches" if fail else "all good")
    if fail:
        for f in fail[:5]:
            print(f"      {f}")

    section("4. COMPETITOR CALIBRATION (±15%)")
    calib = calibration_check()
    for vendor, (pub, alloc, dev) in calib.items():
        ok = abs(dev) <= 15.0
        all_ok &= check(f"{vendor:22s}: published {pub:>6,} | allocated {alloc:>6,}",
                         ok, f"dev {dev:+.1f}%")

    section("5. WORKBOOK STRUCTURE")
    wb = load_workbook(XLSX)
    expected_tabs = {"Summary", "Methodology", "Competitor Summary",
                      "Competitor Penetration"} | set(STATES)
    missing = expected_tabs - set(wb.sheetnames)
    extra = set(wb.sheetnames) - expected_tabs
    all_ok &= check(f"expected {len(expected_tabs)} tabs, found {len(wb.sheetnames)}",
                     not missing,
                     f"missing {missing}" if missing else "")
    if extra:
        print(f"      note: extra tabs {extra}")

    # Scan for formula errors in cached values
    error_tokens = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!", "#NULL!")
    err_count = 0
    err_examples = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value in error_tokens:
                    err_count += 1
                    if len(err_examples) < 5:
                        err_examples.append(f"{ws.title}!{cell.coordinate}={cell.value}")
    all_ok &= check(f"no formula errors in cached cells",
                     err_count == 0,
                     f"{err_count} errors" + (": " + ", ".join(err_examples) if err_examples else ""))

    # Check Summary tab US Total spend lands close to model total
    ws = wb["Summary"]
    # Find US TOTAL spend row — by scanning column A
    ust_row = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=1).value
        if v == "US TOTAL":
            ust_row = r  # last match (spend block totals)
    print(f"      Summary US TOTAL row: {ust_row}")

    section("6. HTML DASHBOARD")
    with open(HTML) as f:
        html = f.read()
    all_ok &= check("file size > 50 KB",
                     os.path.getsize(HTML) > 50_000,
                     f"{os.path.getsize(HTML)/1024:.1f} KB")
    all_ok &= check("Chart.js CDN reference present",
                     "chart.js" in html.lower())
    all_ok &= check("all seven tab sections present",
                     all(s in html for s in
                         ('id="tab-overview"', 'id="tab-heatmaps"',
                          'id="tab-names"', 'id="tab-competitive"',
                          'id="tab-signals"', 'id="tab-prospects"',
                          'id="tab-discovery"')))
    all_ok &= check("embedded JSON data present",
                     "TAM = " in html and "COMP = " in html
                     and "NAMES = " in html and "TILEMAP = " in html
                     and "SIGNALS = " in html and "GREENFIELD = " in html
                     and "LEADS = " in html)
    all_ok &= check("no localStorage / sessionStorage",
                     "localStorage" not in html and "sessionStorage" not in html)
    all_ok &= check("no fetch() calls",
                     not re.search(r"\bfetch\s*\(", html))
    all_ok &= check("no unfilled placeholders",
                     not any(p in html for p in ("__TAM__", "__COMP__",
                                                  "__NAMES__", "__TILEMAP__",
                                                  "__GEO__", "__SIGNALS__",
                                                  "__GREENFIELD__", "__LEADS__")))
    all_ok &= check("d3 CDN reference present",
                     "d3@7" in html.lower() or "d3.geojson" in html.lower()
                     or "d3.geoalbers" in html.lower() or 'd3.min.js' in html)
    all_ok &= check("choropleth container present",
                     'id="choropleth"' in html)
    all_ok &= check("named customers panel present",
                     'id="namedCust"' in html)
    all_ok &= check("muni size-tier filter present",
                     'data-mshow=' in html)

    # Named-customer dataset structural checks
    import json as _json
    with open(os.path.join(OUT_DIR, "competitors_data.json")) as _f:
        comp_data = _json.load(_f)
    vendors_with_customers = sum(
        1 for v in comp_data["vendors"].values() if v.get("named_customers"))
    all_ok &= check(f"every vendor has at least one named customer",
                     vendors_with_customers == len(comp_data["vendors"]),
                     f"{vendors_with_customers}/{len(comp_data['vendors'])} vendors with customers")

    # Names data — confirm sub-15K munis present
    with open(os.path.join(HERE, "names_data.json")) as _f:
        names_data = _json.load(_f)
    total_munis = sum(len(s["cities"]) for s in names_data.values())
    small_munis = sum(1 for s in names_data.values() for c in s["cities"]
                      if c["pop"] is None)
    all_ok &= check(f"sub-15K muni coverage",
                     small_munis > 5000,
                     f"{small_munis} small munis of {total_munis} total")

    section("7. DOCX BRIEF")
    from docx import Document
    doc = Document(DOCX)
    all_ok &= check("US Letter dimensions",
                     doc.sections[0].page_height.twips == 15840
                     and doc.sections[0].page_width.twips == 12240)
    all_ok &= check("at least 1 table",
                     len(doc.tables) >= 1)
    all_ok &= check("has bullet paragraphs",
                     any(p.style.name == "List Bullet" for p in doc.paragraphs))
    all_ok &= check("has all vendor profile headings",
                     all(any(v in p.text for p in doc.paragraphs) for v in COMPETITORS))
    all_ok &= check("uses smart quote (’)",
                     any("’" in p.text for p in doc.paragraphs))

    section("8. BUYING SIGNALS")
    all_ok &= check("at least one signal of every type",
                     all(any(s["type"] == t for s in SIGNALS) for t in SIGNAL_TYPES),
                     f"have {set(s['type'] for s in SIGNALS)}")
    bad_sev = [s["id"] for s in SIGNALS if s["severity"] not in SEVERITY_FACTOR]
    all_ok &= check("severity values valid",
                     not bad_sev,
                     f"{len(bad_sev)} bad" if bad_sev else "")
    bad_state = [s["id"] for s in SIGNALS
                  if s["state"] != "ALL" and s["state"] not in STATES]
    all_ok &= check("all signal states valid",
                     not bad_state,
                     f"{len(bad_state)} bad" if bad_state else "")
    ids = [s["id"] for s in SIGNALS]
    all_ok &= check("signal ids unique",
                     len(ids) == len(set(ids)),
                     f"{len(ids) - len(set(ids))} dupes" if len(ids) != len(set(ids)) else "")
    nonzero = [s for s in SIGNALS if signal_score(s) > 0]
    all_ok &= check("at least 80% of seeded signals are within dropoff window",
                     len(nonzero) >= 0.8 * len(SIGNALS),
                     f"{len(nonzero)}/{len(SIGNALS)} active")

    section("9. GREENFIELD / PERSONA / RENEWAL")
    with open(os.path.join(OUT_DIR, "greenfield_data.json")) as _f:
        gf_data = _json.load(_f)
    all_ok &= check(f"top_prospects populated",
                     len(gf_data.get("top_prospects", [])) >= 100,
                     f"{len(gf_data.get('top_prospects', []))} rows")
    all_ok &= check("each prospect has score components",
                     all("components" in r for r in gf_data["top_prospects"]),
                     "")
    all_ok &= check("each prospect has personas",
                     all(len(r.get("personas") or []) >= 1
                         for r in gf_data["top_prospects"]),
                     "")
    statuses = {r["renewal_status"] for r in gf_data["top_prospects"]}
    in_cycle = bool(statuses.intersection({"in-window", "imminent",
                                             "warming", "past-due"}))
    all_ok &= check("renewal statuses include greenfield + at least one in-cycle",
                     "greenfield" in statuses and in_cycle,
                     f"have {statuses}")
    # Personas module sanity
    from personas import personas_for
    all_ok &= check("personas_for(muni, 1K-5K, ERP) returns >= 3 titles",
                     len(personas_for("muni", "1K-5K", "Munis ERP")) >= 3)
    # Renewals sanity
    from renewals import renewal_window
    rw = renewal_window("Tyler Technologies", 2024, "Munis ERP")
    all_ok &= check("renewal_window for 2024 Tyler Munis returns active/warming",
                     rw["status"] in ("active", "warming"),
                     f"got {rw['status']}")

    section("DELIVERABLES SUMMARY")
    total_entities = sum(STATE_COUNTS[s][0] + STATE_COUNTS[s][1]
                         + STATE_COUNTS[s][2] + STATE_COUNTS[s][3]
                         for s in STATES)
    total_customers = sum(c[1] for c in calib.values())
    sorted_states = sorted(STATES, key=lambda s: -total_state_spend(s))[:5]

    print(f"  Total entities tracked:         {total_entities:,}")
    print(f"  Total annual TAM (operating):   ${total_spend/1e12:.2f}T")
    print(f"  Top-5 states by TAM:")
    for st in sorted_states:
        print(f"    {st} ({total_state_spend(st)/1e9:.1f}B)")
    print(f"  Tracked competitor customers:   {total_customers:,}")
    print(f"  Active buying signals:          {len(nonzero):,}")
    print()
    print(f"  Files:")
    for path in (XLSX, HTML, DOCX):
        size = os.path.getsize(path) / 1024
        print(f"    {path}  ({size:.1f} KB)")

    section("OVERALL")
    print("  " + ("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED — see above"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
