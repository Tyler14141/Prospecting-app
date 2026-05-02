"""
Greenfield / Win-Probability scoring per muni.

Ties together TAM, competitive penetration, named customers, buying
signals, persona, and renewal-window data into a single 0-100 score
per municipality. Higher = stronger outbound target right now.

Components (max points per row in parens):
  ICP fit                (30)  — population bucket vs. small-muni ICP
  Displaceability        (25)  — based on incumbent vendor (or greenfield)
  Signal intensity       (25)  — buying signals affecting this muni / state
  White-space density    (20)  — 1 - state-level competitor penetration
  Renewal-window boost  (+10)  — added when incumbent is in/near renewal window

Total cap = 100.

# refreshed 2026-05-02
"""

from collections import defaultdict

from competitor_customers import CUSTOMERS
from competitors import STATE_PENETRATION
from data import STATE_COUNTS, STATES
from renewals import renewal_window
from signals import SIGNALS, signal_score
from personas import personas_for, directory_links_for


# ---- ICP fit (0-30) -------------------------------------------------------
# Sweet spot for small-muni outbound is 1K-50K. Largest at 5K-10K.
ICP_BY_BUCKET = {
    "<1K":            8,
    "1K-5K":          25,
    "5K-10K":         30,
    "10K-20K":        28,
    "20K-50K":        22,
    "50K-100K":       15,
    "100K+":          8,
    "small (<15K)":   22,    # generic small-muni placeholder bucket
    None:             18,
}

# ---- Displaceability (0-25) -----------------------------------------------
# Higher = easier to displace. Keyed by (vendor, product_substring) so we
# can differentiate Tyler Munis (sticky) vs. Tyler New World (sunset).
def displaceability(incumbent_vendor: str, incumbent_product: str = None,
                     state: str = None) -> int:
    if not incumbent_vendor:
        return 25                                           # pure greenfield
    p = (incumbent_product or "").lower()
    v = incumbent_vendor

    # Tyler product-line specifics
    if v == "Tyler Technologies":
        if "new world" in p:
            return 20    # sunset legacy product
        if "energov" in p or "civic access" in p:
            return 14    # active product, mid-stickiness
        if "munis self service" in p:
            return 10    # enterprise sticky
        if "munis" in p or "enterprise erp" in p:
            return 8     # very sticky
        if "hosted" in p:
            return 12
        return 12        # Tyler general

    # BS&A — entrenched in MI, less so elsewhere
    if v == "BS&A Software":
        return 5 if state == "MI" else 16

    if v == "Caselle":
        return 22    # legacy on-prem, active EOL pressure

    if v == "gWorks":
        return 18    # roll-up integration friction

    if v == "Muni-Link":
        return 14    # single-product, replaceable

    if v == "TownCloud":
        return 6     # modern cloud, sticky

    return 15        # unknown vendor


# ---- White-space density (0-20) -------------------------------------------
def white_space(state: str, addressable_by_state: dict, combined_by_state: dict) -> int:
    addr = addressable_by_state.get(state, 0)
    if addr <= 0:
        return 0
    pen = combined_by_state.get(state, 0) / addr
    # Map penetration 0..0.5 -> score 20..0 (above 50% pen, no white space credit)
    return max(0, int(round(20 * (1.0 - min(pen / 0.5, 1.0)))))


# ---- Signal intensity (0-25) ----------------------------------------------
# Sum signal_score for any signal targeting (muni,state) plus a small
# state-wide boost from generic signals (compliance / vendor EOL targeting
# the whole state).
def signal_intensity(muni_name: str, state: str,
                      muni_signal_index: dict, state_signal_index: dict) -> int:
    direct = sum(s["score"] for s in muni_signal_index.get((muni_name, state), []))
    statewide = sum(s["score"] for s in state_signal_index.get(state, []))
    raw = direct * 4.0 + statewide * 1.5
    # Compress to 0..25
    return min(25, int(round(raw)))


# ---- Renewal boost (0-10) -------------------------------------------------
def renewal_boost(rw: dict) -> int:
    if not rw:
        return 0
    return {
        "in-window": 10,
        "imminent":   8,
        "warming":    5,
        "past-due":   6,
        "unknown":    2,
        "active":     0,
    }.get(rw.get("status"), 0)


# ---- Index builders -------------------------------------------------------
def build_indices():
    """Pre-compute lookups for fast per-muni scoring."""
    # 1. Incumbent index from named customers
    incumbents = {}
    for c in CUSTOMERS:
        key = (c["muni"].lower(), c["state"])
        # Prefer entries with product info; else first wins
        if key not in incumbents or (c.get("product") and not incumbents[key].get("product")):
            incumbents[key] = c

    # 2. Signal index — direct (muni,state) and statewide (state)
    enriched = []
    for s in SIGNALS:
        sc = signal_score(s)
        if sc <= 0:
            continue
        enriched.append({**s, "score": sc})
    muni_idx = defaultdict(list)
    state_idx = defaultdict(list)
    for s in enriched:
        if s["state"] == "ALL" or s["muni"].lower().startswith(
                ("statewide", "vendor-wide", "all states")):
            # Statewide / cross-state signal — apply to whole state
            state_idx[s["state"]].append(s)
        else:
            muni_idx[(s["muni"], s["state"])].append(s)

    # 3. Combined competitor presence per state
    combined = {st: 0 for st in STATES}
    for v, by_state in STATE_PENETRATION.items():
        for st, n in by_state.items():
            combined[st] += n
    addressable = {st: STATE_COUNTS[st][0] + STATE_COUNTS[st][1] + STATE_COUNTS[st][2]
                    for st in STATES}

    return incumbents, muni_idx, state_idx, addressable, combined


def score_muni(name: str, state: str, pop, bucket: str,
                indices: tuple, entity_type: str = "muni") -> dict:
    incumbents, muni_idx, state_idx, addressable, combined = indices
    inc = incumbents.get((name.lower(), state))
    inc_vendor  = inc["vendor"]  if inc else None
    inc_product = inc.get("product") if inc else None
    inc_since   = inc.get("since") if inc else None

    rw = renewal_window(inc_vendor, inc_since, inc_product) if inc else None

    icp = ICP_BY_BUCKET.get(bucket, 18)
    disp = displaceability(inc_vendor, inc_product, state)
    ws = white_space(state, addressable, combined)
    si = signal_intensity(name, state, muni_idx, state_idx)
    rb = renewal_boost(rw) if rw else (
        # No incumbent known: small uncertainty discount on the boost
        # because a greenfield prospect doesn't have a renewal cycle, but
        # the displaceability score already credits that.
        0
    )

    total = min(100, icp + disp + ws + si + rb)
    primary_personas = personas_for(entity_type, bucket, inc_product)[:3]
    return {
        "muni": name,
        "state": state,
        "pop": pop,
        "bucket": bucket,
        "entity_type": entity_type,
        "score": total,
        "components": {
            "icp": icp, "displace": disp, "white_space": ws,
            "signal": si, "renewal": rb,
        },
        "incumbent": (
            {"vendor": inc_vendor, "product": inc_product, "since": inc_since}
            if inc else None
        ),
        "renewal": rw,
        "personas": primary_personas,
        "directory_hints": directory_links_for(state),
        "signals": [s["id"] for s in muni_idx.get((name, state), [])],
    }


if __name__ == "__main__":
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "names_data.json")) as f:
        names = json.load(f)

    indices = build_indices()
    rows = []
    for st, blob in names.items():
        for c in blob.get("cities", []):
            rows.append(score_muni(c["name"], st, c.get("pop"),
                                     c.get("bucket"), indices))
    rows.sort(key=lambda r: -r["score"])
    print(f"Scored {len(rows):,} munis")
    print("\nTop 25:")
    for r in rows[:25]:
        inc = r["incumbent"]
        inc_str = f"{inc['vendor']} ({inc.get('product') or '?'})" if inc else "GREENFIELD"
        rs = r["renewal"]["status"] if r.get("renewal") else "-"
        print(f"  {r['score']:>3}  {r['muni']:25s} {r['state']}  "
              f"{r['bucket']:14s}  {inc_str:50s}  {rs}")
