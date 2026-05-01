"""
Competitor metadata and per-state customer-count estimates.

Methodology: each vendor's published customer total is allocated across states
using HQ-state weighting, named case-study customers, acquired-company home
states, and population-weighted residual. Per-state sums must land within
±15% of the published total.

# refreshed 2026-05-01
"""

# Each vendor block:
#   total: published customer count (rounded, defensible)
#   hq: state abbreviation
#   hq_state_full: full state name
#   focus: product focus (short)
#   size_target: which population buckets they sell into
#   notes: terse context — M&A history, competitive strengths, etc.
#   acquired: list of relevant acquisitions
#   strengths / weaknesses / threat: for the brief
COMPETITORS = {
    "Tyler Technologies": {
        "total": 13000,
        "hq": "TX",
        "hq_state_full": "Texas",
        "focus": "Enterprise ERP, courts, public safety, K-12, payments",
        "size_target": "Mid-to-large (10K-100K+)",
        "notes": (
            "Largest pure-play public-sector software vendor. NIC acquisition "
            "(2021, $2.3B) added payments + 30 state portal contracts. Strong "
            "in county courts, ERP (Munis), CAD/RMS (New World)."
        ),
        "acquired": ["NIC (2021)", "MicroPact (2019)", "Socrata (2018)",
                     "New World Systems (2015)", "MUNIS"],
        "strengths": [
            "Broadest product portfolio across local-gov verticals",
            "Public-company scale, R&D budget, and balance sheet",
            "Deep references in mid-large counties and state agencies",
        ],
        "weaknesses": [
            "Premium pricing — often non-starter for towns under 5K",
            "Implementations multi-year; switching costs cut both ways",
            "Many products from acquisitions are loosely integrated",
        ],
        "threat": "high",
    },
    "BS&A Software": {
        "total": 2500,
        "hq": "MI",
        "hq_state_full": "Michigan",
        "focus": "Financial mgmt, assessing, tax, building permits",
        "size_target": "Small-to-mid (1K-50K)",
        "notes": (
            "Michigan dominant — estimated ~70-80% of MI municipalities run "
            "BS&A. Acquired by Harris Computer (Constellation Software) in "
            "2021. Expanding into OH, IN, IL via Harris's distribution."
        ),
        "acquired": ["Acquired by Harris Computer / Constellation (2021)"],
        "strengths": [
            "Near-monopoly in Michigan small/mid muni segment",
            "Constellation parent provides capital + roll-up engine",
            "Tight integration across financials, assessing, and tax",
        ],
        "weaknesses": [
            "Geographic concentration creates expansion risk",
            "Legacy on-prem footprint slowing cloud migration",
            "Limited brand outside upper-Midwest",
        ],
        "threat": "medium",
    },
    "Caselle": {
        "total": 1000,
        "hq": "UT",
        "hq_state_full": "Utah",
        "focus": "Accounting, payroll, utility billing for small cities",
        "size_target": "Small (<10K)",
        "notes": (
            "Mountain-West small-town stronghold. Long-tenured installed "
            "base in UT/ID/WY/MT/NV. Slower modernization than some peers; "
            "core suite still stable cash cow."
        ),
        "acquired": [],
        "strengths": [
            "Sticky installed base — average tenure 10+ years",
            "Low-cost suite tuned to <10K-pop municipalities",
            "Strong reference accounts across Mountain West",
        ],
        "weaknesses": [
            "On-prem heavy; cloud roadmap behind cloud-native peers",
            "Limited verticals (no permits, GIS, public-safety)",
            "Concentrated in 6-8 states — exposed to gWorks, TownCloud",
        ],
        "threat": "medium",
    },
    "gWorks": {
        "total": 2500,
        "hq": "NE",
        "hq_state_full": "Nebraska",
        "focus": "All-in-one ERP, GIS, websites for very small towns",
        "size_target": "Very small (<5K)",
        "notes": (
            "Roll-up of small public-sector vendors. Acquired Banyon Data "
            "Systems (MN), Pontem, and others. Plains-states stronghold; "
            "expanding eastward via channel."
        ),
        "acquired": ["Banyon Data Systems", "Pontem", "Compu-Strategies"],
        "strengths": [
            "Bundled GIS + ERP + website is rare at sub-5K-pop price point",
            "Targeted roll-up strategy growing customer base 15-20% YoY",
            "Strong in NE/IA/KS/SD/ND clerk-of-the-courthouse market",
        ],
        "weaknesses": [
            "Customer count inflated by very-small-town tail (low ACV)",
            "Integration debt across acquired products",
            "Sales motion still mostly direct — limited marketing reach",
        ],
        "threat": "medium",
    },
    "Muni-Link": {
        "total": 750,
        "hq": "PA",
        "hq_state_full": "Pennsylvania",
        "focus": "Cloud utility billing (water, sewer, stormwater)",
        "size_target": "Small-to-mid utilities (1K-50K)",
        "notes": (
            "Single-vertical SaaS focused on municipal utility billing. "
            "Concentrated in PA/OH/WV with growing presence in NY/MD/VA. "
            "Often layered alongside a separate ERP."
        ),
        "acquired": [],
        "strengths": [
            "Modern cloud architecture; quick deploy under 90 days",
            "Pure-play focus = strong utility billing depth",
            "Easy integration alongside Tyler/BS&A as utility module",
        ],
        "weaknesses": [
            "Single product line — no obvious upsell vector",
            "Regional brand; weak national awareness",
            "Vulnerable to utility module bundled by full-suite ERPs",
        ],
        "threat": "low",
    },
    "TownCloud": {
        "total": 200,
        "hq": "VA",
        "hq_state_full": "Virginia",
        "focus": "Cloud-native ERP for small Southeast towns",
        "size_target": "Small (<5K)",
        "notes": (
            "Newer entrant. Cloud-native from day one. Concentrated in VA/"
            "NC/SC/TN. Smaller footprint but fastest growth rate among the "
            "tracked set."
        ),
        "acquired": [],
        "strengths": [
            "Cleanest UX of any tracked vendor — modern tech stack",
            "Per-resident SaaS pricing; predictable for small-town budgets",
            "Fastest implementations — typical 30-60 day go-live",
        ],
        "weaknesses": [
            "Smallest installed base of tracked competitors",
            "Limited functional depth in assessing/tax",
            "Has not yet won a 50K+ pop city — uncertain mid-market fit",
        ],
        "threat": "low",
    },
}


# ---- State-level customer allocations -------------------------------------
# Each vendor → {state: customer_count}. Per-state sums calibrated to ±15%
# of each vendor's published total above. Heavy weighting on HQ state and
# documented case-study states; population-weighted spread for residual.
STATE_PENETRATION = {
    "Tyler Technologies": {
        "AL": 220, "AK": 30,  "AZ": 230, "AR": 180, "CA": 750, "CO": 320,
        "CT": 110, "DE": 50,  "FL": 540, "GA": 380, "HI": 25,  "ID": 130,
        "IL": 520, "IN": 290, "IA": 240, "KS": 220, "KY": 230, "LA": 200,
        "ME": 70,  "MD": 200, "MA": 240, "MI": 380, "MN": 320, "MS": 170,
        "MO": 320, "MT": 90,  "NE": 130, "NV": 110, "NH": 80,  "NJ": 290,
        "NM": 110, "NY": 470, "NC": 400, "ND": 70,  "OH": 470, "OK": 200,
        "OR": 220, "PA": 480, "RI": 35,  "SC": 220, "SD": 70,  "TN": 270,
        "TX": 1100,"UT": 170, "VT": 50,  "VA": 320, "WA": 320, "WV": 110,
        "WI": 280, "WY": 50,  "DC": 10,
    },
    "BS&A Software": {
        "AL": 5,   "AK": 0,   "AZ": 8,   "AR": 5,   "CA": 12,  "CO": 10,
        "CT": 4,   "DE": 2,   "FL": 18,  "GA": 12,  "HI": 0,   "ID": 8,
        "IL": 75,  "IN": 110, "IA": 25,  "KS": 12,  "KY": 18,  "LA": 4,
        "ME": 4,   "MD": 6,   "MA": 12,  "MI": 1450,"MN": 60,  "MS": 4,
        "MO": 25,  "MT": 4,   "NE": 8,   "NV": 4,   "NH": 4,   "NJ": 20,
        "NM": 2,   "NY": 50,  "NC": 18,  "ND": 4,   "OH": 220, "OK": 6,
        "OR": 8,   "PA": 60,  "RI": 2,   "SC": 8,   "SD": 4,   "TN": 18,
        "TX": 30,  "UT": 8,   "VT": 2,   "VA": 18,  "WA": 12,  "WV": 6,
        "WI": 75,  "WY": 2,   "DC": 0,
    },
    "Caselle": {
        "AL": 4,   "AK": 8,   "AZ": 35,  "AR": 5,   "CA": 22,  "CO": 60,
        "CT": 0,   "DE": 0,   "FL": 8,   "GA": 4,   "HI": 0,   "ID": 110,
        "IL": 6,   "IN": 4,   "IA": 18,  "KS": 35,  "KY": 4,   "LA": 2,
        "ME": 0,   "MD": 2,   "MA": 0,   "MI": 4,   "MN": 18,  "MS": 2,
        "MO": 18,  "MT": 70,  "NE": 25,  "NV": 50,  "NH": 0,   "NJ": 2,
        "NM": 30,  "NY": 6,   "NC": 4,   "ND": 30,  "OH": 6,   "OK": 18,
        "OR": 35,  "PA": 4,   "RI": 0,   "SC": 2,   "SD": 30,  "TN": 4,
        "TX": 30,  "UT": 280, "VT": 0,   "VA": 4,   "WA": 35,  "WV": 0,
        "WI": 6,   "WY": 90,  "DC": 0,
    },
    "gWorks": {
        "AL": 8,   "AK": 4,   "AZ": 12,  "AR": 30,  "CA": 18,  "CO": 50,
        "CT": 0,   "DE": 0,   "FL": 14,  "GA": 12,  "HI": 0,   "ID": 50,
        "IL": 80,  "IN": 50,  "IA": 280, "KS": 220, "KY": 18,  "LA": 12,
        "ME": 4,   "MD": 4,   "MA": 0,   "MI": 35,  "MN": 200, "MS": 12,
        "MO": 130, "MT": 70,  "NE": 480, "NV": 8,   "NH": 0,   "NJ": 4,
        "NM": 25,  "NY": 18,  "NC": 18,  "ND": 130, "OH": 35,  "OK": 70,
        "OR": 18,  "PA": 25,  "RI": 0,   "SC": 8,   "SD": 220, "TN": 18,
        "TX": 90,  "UT": 25,  "VT": 0,   "VA": 12,  "WA": 25,  "WV": 8,
        "WI": 50,  "WY": 35,  "DC": 0,
    },
    "Muni-Link": {
        "AL": 4,   "AK": 0,   "AZ": 4,   "AR": 4,   "CA": 8,   "CO": 4,
        "CT": 6,   "DE": 4,   "FL": 14,  "GA": 12,  "HI": 0,   "ID": 0,
        "IL": 12,  "IN": 12,  "IA": 4,   "KS": 4,   "KY": 14,  "LA": 4,
        "ME": 4,   "MD": 35,  "MA": 14,  "MI": 12,  "MN": 6,   "MS": 4,
        "MO": 8,   "MT": 0,   "NE": 4,   "NV": 0,   "NH": 4,   "NJ": 35,
        "NM": 0,   "NY": 50,  "NC": 30,  "ND": 0,   "OH": 100, "OK": 4,
        "OR": 4,   "PA": 220, "RI": 4,   "SC": 18,  "SD": 0,   "TN": 14,
        "TX": 14,  "UT": 4,   "VT": 4,   "VA": 60,  "WA": 6,   "WV": 60,
        "WI": 12,  "WY": 0,   "DC": 0,
    },
    "TownCloud": {
        "AL": 4,   "AK": 0,   "AZ": 2,   "AR": 4,   "CA": 0,   "CO": 2,
        "CT": 0,   "DE": 0,   "FL": 8,   "GA": 14,  "HI": 0,   "ID": 0,
        "IL": 2,   "IN": 4,   "IA": 0,   "KS": 0,   "KY": 6,   "LA": 4,
        "ME": 0,   "MD": 4,   "MA": 0,   "MI": 0,   "MN": 0,   "MS": 4,
        "MO": 4,   "MT": 0,   "NE": 0,   "NV": 0,   "NH": 0,   "NJ": 2,
        "NM": 0,   "NY": 4,   "NC": 30,  "ND": 0,   "OH": 4,   "OK": 4,
        "OR": 0,   "PA": 4,   "RI": 0,   "SC": 18,  "SD": 0,   "TN": 22,
        "TX": 8,   "UT": 0,   "VT": 0,   "VA": 50,  "WA": 0,   "WV": 4,
        "WI": 0,   "WY": 0,   "DC": 0,
    },
}


def vendor_state_total(vendor: str) -> int:
    return sum(STATE_PENETRATION[vendor].values())


def calibration_check(verbose: bool = False):
    """Returns dict {vendor: (total_published, total_allocated, pct_dev)}."""
    out = {}
    for v, meta in COMPETITORS.items():
        published = meta["total"]
        allocated = vendor_state_total(v)
        dev = (allocated - published) / published * 100
        out[v] = (published, allocated, dev)
        if verbose:
            mark = "OK " if abs(dev) <= 15 else "OFF"
            print(f"{mark}  {v:20s}  published={published:>6}  "
                  f"allocated={allocated:>6}  dev={dev:+5.1f}%")
    return out


if __name__ == "__main__":
    calibration_check(verbose=True)
