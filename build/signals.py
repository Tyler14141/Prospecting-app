"""
Buying-signal taxonomy, scoring, and a seeded demo dataset.

Each signal links a specific municipality to an event that creates near-term
buying intent (active RFP, leadership change, cyber incident, bond issuance,
compliance deadline, vendor EOL/M&A, audit finding).

The dataset below is SEED / DEMO data — illustrative, not live.  Replace it
by wiring the connectors in signals_pipeline.py to the real sources listed
in the SOURCE_HINTS docstring of each connector.

# refreshed 2026-05-01
"""

from datetime import date, timedelta


TODAY = date(2026, 5, 1)

# A signal's score = base_weight × recency_decay × severity_factor.
# Higher weight = more direct buying intent.
SIGNAL_TYPES = {
    "rfp":         {"label": "Active RFP",          "weight": 5.0, "color": "#ef4444"},
    "vendor_eol":  {"label": "Vendor EOL / M&A",    "weight": 4.5, "color": "#10b981"},
    "cyber":       {"label": "Cyber incident",      "weight": 4.0, "color": "#dc2626"},
    "leadership":  {"label": "New leadership",      "weight": 3.0, "color": "#f59e0b"},
    "compliance":  {"label": "Compliance deadline", "weight": 3.0, "color": "#a855f7"},
    "audit":       {"label": "Audit finding",       "weight": 3.0, "color": "#f97316"},
    "bond":        {"label": "Bond issuance",       "weight": 2.0, "color": "#3b82f6"},
}

SEVERITY_FACTOR = {"high": 1.0, "medium": 0.7, "low": 0.4}

RECENCY_HALFLIFE_DAYS = 60   # signal score halves every 60 days
HARD_DROPOFF_DAYS    = 180   # signals older than this are excluded


# ---- Seeded demo dataset --------------------------------------------------
# Schema:
#   id, muni, state, population, bucket, type, severity,
#   detected (ISO date), expires (ISO date or None),
#   headline, details, source, url, incumbent, demo (bool)
#
# Notes on each entry: cyber and leadership entries use generic patterns;
# compliance entries reference real, public state/federal deadlines; RFP
# and bond entries are public-record style. All entries are flagged
# demo=True until the live connectors are wired in.

SIGNALS = [
    # ===== RFPs (15) =====
    {
        "id": "sig_2026_001", "muni": "Cedar Falls", "state": "IA",
        "population": 41000, "bucket": "20K-50K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-22", "expires": "2026-06-15",
        "headline": "ERP / Financial Management RFP",
        "details": "Replacing on-prem financials. Cloud-native required. Est. ACV $90-140K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_002", "muni": "Coralville", "state": "IA",
        "population": 23000, "bucket": "20K-50K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-08", "expires": "2026-05-30",
        "headline": "Utility Billing System RFP",
        "details": "Water/sewer/storm. SaaS preferred. Est. ACV $25-45K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_003", "muni": "Bozeman", "state": "MT",
        "population": 56000, "bucket": "50K-100K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-15", "expires": "2026-06-20",
        "headline": "Permitting & GIS Integration RFP",
        "details": "Building/planning workflow + GIS layer. Implementation Q4. ACV $75-120K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_004", "muni": "Cheyenne", "state": "WY",
        "population": 65000, "bucket": "50K-100K",
        "type": "rfp", "severity": "high",
        "detected": "2026-03-28", "expires": "2026-05-15",
        "headline": "Financial Management & Payroll RFP",
        "details": "Multi-department ERP. State co-op contract preferred (Sourcewell).",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_005", "muni": "Logan", "state": "UT",
        "population": 53000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-10", "expires": "2026-06-10",
        "headline": "ERP Modernization RFP",
        "details": "Migrating from on-prem to cloud. ACV $60-100K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_006", "muni": "Grand Junction", "state": "CO",
        "population": 67000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-18", "expires": "2026-06-30",
        "headline": "Cloud ERP Migration RFP",
        "details": "Replacing legacy AS/400. ACV $80-130K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_007", "muni": "Bismarck", "state": "ND",
        "population": 75000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-02", "expires": "2026-06-01",
        "headline": "ERP Consolidation RFP",
        "details": "Consolidating 4 legacy systems. ACV $100-160K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_008", "muni": "Manhattan", "state": "KS",
        "population": 54000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-03-20", "expires": "2026-05-05",
        "headline": "Financial System Replacement RFP",
        "details": "On-prem to SaaS. Sourcewell-eligible vendors only.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_009", "muni": "Columbia", "state": "MO",
        "population": 127000, "bucket": "100K+",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-25", "expires": "2026-07-01",
        "headline": "ERP RFP",
        "details": "City-wide ERP replacement. ACV $250-450K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_010", "muni": "Bloomington", "state": "IN",
        "population": 79000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-05", "expires": "2026-06-05",
        "headline": "Cloud ERP RFP",
        "details": "Replacing legacy financials. ACV $90-150K.",
        "source": "Periscope/Bonfire", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_011", "muni": "Akron", "state": "OH",
        "population": 190000, "bucket": "100K+",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-12", "expires": "2026-06-12",
        "headline": "GIS & Permitting Modernization RFP",
        "details": "Multi-year IT modernization initiative.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_012", "muni": "Lawrence", "state": "KS",
        "population": 95000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-03-15", "expires": "2026-05-15",
        "headline": "Utility Billing RFP",
        "details": "Water + electric. ACV $40-70K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_013", "muni": "Springfield", "state": "MO",
        "population": 169000, "bucket": "100K+",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-29", "expires": "2026-07-15",
        "headline": "Permitting & Code Enforcement RFP",
        "details": "Replacing 18-year-old custom system. ACV $120-200K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_014", "muni": "Salina", "state": "KS",
        "population": 47000, "bucket": "20K-50K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-19", "expires": "2026-06-19",
        "headline": "ERP RFP",
        "details": "Mid-market ERP. State pricing preferred.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_015", "muni": "Casper", "state": "WY",
        "population": 59000, "bucket": "50K-100K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-01", "expires": "2026-05-31",
        "headline": "Financial Management RFP",
        "details": "Replacing Caselle. ACV $60-100K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },

    # ===== Leadership changes (8) =====
    {
        "id": "sig_2026_101", "muni": "Ames", "state": "IA",
        "population": 67000, "bucket": "50K-100K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-15", "expires": None,
        "headline": "New Finance Director appointed",
        "details": "First 90 days — typical IT review window.",
        "source": "LinkedIn / city press release", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_102", "muni": "Greeley", "state": "CO",
        "population": 110000, "bucket": "100K+",
        "type": "leadership", "severity": "medium",
        "detected": "2026-03-10", "expires": None,
        "headline": "New City Manager hired",
        "details": "Public-sector tech background. Cited modernization in press.",
        "source": "City press release", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_103", "muni": "Helena", "state": "MT",
        "population": 33000, "bucket": "20K-50K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-08", "expires": None,
        "headline": "New Finance Director + IT Director",
        "details": "Dual-role replacement creates strong reset window.",
        "source": "LinkedIn / city release", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_104", "muni": "Missoula", "state": "MT",
        "population": 76000, "bucket": "50K-100K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-02-20", "expires": None,
        "headline": "New CFO appointed",
        "details": "From private sector — likely fresh look at vendor stack.",
        "source": "LinkedIn", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_105", "muni": "Sioux Falls", "state": "SD",
        "population": 200000, "bucket": "100K+",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-12", "expires": None,
        "headline": "New IT Director",
        "details": "Cloud-first stated direction in inaugural memo.",
        "source": "City announcement", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_106", "muni": "Pocatello", "state": "ID",
        "population": 56000, "bucket": "50K-100K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-03-25", "expires": None,
        "headline": "New Finance Director",
        "details": "First 90-day review of legacy systems underway.",
        "source": "LinkedIn", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_107", "muni": "Lawton", "state": "OK",
        "population": 90000, "bucket": "50K-100K",
        "type": "leadership", "severity": "low",
        "detected": "2026-02-14", "expires": None,
        "headline": "New City Clerk",
        "details": "Smaller-scope change — flag for relationship-mapping.",
        "source": "Local press", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_108", "muni": "Topeka", "state": "KS",
        "population": 126000, "bucket": "100K+",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-22", "expires": None,
        "headline": "New CIO",
        "details": "Public statement re: vendor consolidation initiative.",
        "source": "Government Technology", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },

    # ===== Cyber incidents (4 — genericized) =====
    {
        "id": "sig_2026_201", "muni": "Mid-size MI city", "state": "MI",
        "population": 22000, "bucket": "20K-50K",
        "type": "cyber", "severity": "high",
        "detected": "2026-04-10", "expires": None,
        "headline": "Reported ransomware incident — recovery underway",
        "details": "Demo placeholder. Replace with MS-ISAC / news feed.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_202", "muni": "Small TX county", "state": "TX",
        "population": 12000, "bucket": "10K-20K",
        "type": "cyber", "severity": "high",
        "detected": "2026-03-22", "expires": None,
        "headline": "Reported network intrusion — services disrupted",
        "details": "Demo placeholder. Forces cloud migration discussion.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_203", "muni": "Mid-size FL muni", "state": "FL",
        "population": 38000, "bucket": "20K-50K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-04-02", "expires": None,
        "headline": "Phishing incident — internal email compromise",
        "details": "Demo placeholder. Triggers security-stack review.",
        "source": "Local press (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_204", "muni": "Small CA muni", "state": "CA",
        "population": 8500, "bucket": "5K-10K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-03-08", "expires": None,
        "headline": "Public disclosure of data breach",
        "details": "Demo placeholder. State-mandated notification triggered.",
        "source": "CA AG breach reports (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },

    # ===== Bond issuances (5) =====
    {
        "id": "sig_2026_301", "muni": "Eau Claire", "state": "WI",
        "population": 70000, "bucket": "50K-100K",
        "type": "bond", "severity": "low",
        "detected": "2026-03-20", "expires": None,
        "headline": "$24M general obligation bond issued",
        "details": "IT/equipment line item present. Capex headroom for software.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_302", "muni": "Sheboygan", "state": "WI",
        "population": 49000, "bucket": "20K-50K",
        "type": "bond", "severity": "low",
        "detected": "2026-04-10", "expires": None,
        "headline": "$15M utility revenue bond",
        "details": "Water/sewer infrastructure + metering modernization.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_303", "muni": "Council Bluffs", "state": "IA",
        "population": 62000, "bucket": "50K-100K",
        "type": "bond", "severity": "medium",
        "detected": "2026-04-18", "expires": None,
        "headline": "$32M GO bond — IT modernization included",
        "details": "Bond statement explicitly mentions ERP replacement.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_304", "muni": "Kearney", "state": "NE",
        "population": 34000, "bucket": "20K-50K",
        "type": "bond", "severity": "low",
        "detected": "2026-03-30", "expires": None,
        "headline": "$12M GO bond",
        "details": "Capex for FY26-27 includes software refresh.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_305", "muni": "Lawrence", "state": "MA",
        "population": 89000, "bucket": "50K-100K",
        "type": "bond", "severity": "low",
        "detected": "2026-04-05", "expires": None,
        "headline": "$45M capital bond",
        "details": "Multi-year IT initiative noted in offering documents.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },

    # ===== Compliance deadlines (4 — these reference real public mandates) ====
    {
        "id": "sig_2026_401", "muni": "Statewide", "state": "TX",
        "population": 0, "bucket": "100K+",
        "type": "compliance", "severity": "medium",
        "detected": "2026-01-15", "expires": "2026-09-01",
        "headline": "TX SB820 cybersecurity compliance deadline",
        "details": "All TX local govts must adopt cyber framework. Drives security-vendor refresh.",
        "source": "TX legislature", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_402", "muni": "Statewide", "state": "CA",
        "population": 0, "bucket": "100K+",
        "type": "compliance", "severity": "high",
        "detected": "2026-02-01", "expires": "2026-12-31",
        "headline": "CA AB749 IT vendor disclosure",
        "details": "Annual disclosure of vendor stack — opens RFP review windows.",
        "source": "CA legislature", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_403", "muni": "All states", "state": "ALL",
        "population": 0, "bucket": "100K+",
        "type": "compliance", "severity": "high",
        "detected": "2026-03-01", "expires": "2026-06-30",
        "headline": "GASB 96 SBITA reporting period",
        "details": "Subscription-based IT arrangements: full year-end. Drives ERP/AP module refreshes.",
        "source": "GASB", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_404", "muni": "Statewide", "state": "NY",
        "population": 0, "bucket": "100K+",
        "type": "compliance", "severity": "medium",
        "detected": "2026-02-20", "expires": "2026-08-15",
        "headline": "NY SHIELD Act expanded enforcement",
        "details": "Expanded breach-notification scope — security review for all munis.",
        "source": "NY DFS", "url": None,
        "incumbent": None, "demo": True,
    },

    # ===== Vendor EOL / M&A (5) =====
    {
        "id": "sig_2026_501", "muni": "Vendor-wide", "state": "ALL",
        "population": 0, "bucket": "100K+",
        "type": "vendor_eol", "severity": "high",
        "detected": "2026-03-01", "expires": "2026-12-31",
        "headline": "Caselle DOS-era suite end-of-support",
        "details": "Estimated ~120 small-muni installs in UT/ID/WY/MT/NV approaching EOL. Replacement RFP window.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_502", "muni": "Vendor-wide", "state": "ALL",
        "population": 0, "bucket": "100K+",
        "type": "vendor_eol", "severity": "high",
        "detected": "2026-02-15", "expires": None,
        "headline": "Tyler New World legacy migration push",
        "details": "Tyler migrating ~600 New World CAD/RMS customers to Enterprise. Disruption window for displacement.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_503", "muni": "Vendor-wide", "state": "MI",
        "population": 0, "bucket": "100K+",
        "type": "vendor_eol", "severity": "medium",
        "detected": "2026-04-01", "expires": None,
        "headline": "BS&A Harris-driven product line consolidation",
        "details": "Constellation roll-up activity may force MI customers to re-evaluate.",
        "source": "Competitor watch", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_504", "muni": "Vendor-wide", "state": "ALL",
        "population": 0, "bucket": "100K+",
        "type": "vendor_eol", "severity": "medium",
        "detected": "2026-03-20", "expires": None,
        "headline": "gWorks roll-up integration debt",
        "details": "Banyon/Pontem/Compu-Strategies customers reporting integration friction — switching window.",
        "source": "Competitor watch", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_505", "muni": "Vendor-wide", "state": "PA",
        "population": 0, "bucket": "100K+",
        "type": "vendor_eol", "severity": "low",
        "detected": "2026-04-15", "expires": None,
        "headline": "Muni-Link pricing model change",
        "details": "Reported per-account pricing shift may surface RFPs from existing PA customers.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Muni-Link", "demo": True,
    },

    # ===== Audit findings (3) =====
    {
        "id": "sig_2026_601", "muni": "Saginaw", "state": "MI",
        "population": 44000, "bucket": "20K-50K",
        "type": "audit", "severity": "medium",
        "detected": "2026-03-12", "expires": None,
        "headline": "State audit cited financial-system controls",
        "details": "Material weakness flagged in financials — pressure to modernize.",
        "source": "MI auditor general", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_602", "muni": "Charleston", "state": "WV",
        "population": 47000, "bucket": "20K-50K",
        "type": "audit", "severity": "medium",
        "detected": "2026-04-20", "expires": None,
        "headline": "Audit deficiency: cash reconciliation",
        "details": "Forces ERP/cash-management review.",
        "source": "WV state auditor", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_603", "muni": "Tupelo", "state": "MS",
        "population": 38000, "bucket": "20K-50K",
        "type": "audit", "severity": "low",
        "detected": "2026-03-05", "expires": None,
        "headline": "Audit recommendation: modernize accounts receivable",
        "details": "Non-material but flagged — opens permitting/billing conversation.",
        "source": "MS state auditor", "url": None,
        "incumbent": None, "demo": True,
    },
]


# ---- Scoring --------------------------------------------------------------
def signal_score(sig: dict, today: date = TODAY) -> float:
    """Composite score: weight × recency × severity. Stale signals score 0."""
    detected = date.fromisoformat(sig["detected"])
    days_old = (today - detected).days
    if days_old > HARD_DROPOFF_DAYS or days_old < 0:
        return 0.0
    recency = 0.5 ** (days_old / RECENCY_HALFLIFE_DAYS)
    weight = SIGNAL_TYPES[sig["type"]]["weight"]
    sev = SEVERITY_FACTOR[sig["severity"]]
    return round(weight * recency * sev, 3)


def signals_for_state(st: str) -> list:
    return [s for s in SIGNALS if s["state"] == st or s["state"] == "ALL"]


def state_signal_density(st: str, today: date = TODAY) -> float:
    """Sum of scores for active signals targeting this state (incl. ALL)."""
    return sum(signal_score(s, today)
               for s in SIGNALS
               if s["state"] == st or s["state"] == "ALL")


# ---- Self-test -----------------------------------------------------------
if __name__ == "__main__":
    print(f"Total signals: {len(SIGNALS)}")
    by_type = {}
    for s in SIGNALS:
        by_type[s["type"]] = by_type.get(s["type"], 0) + 1
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {SIGNAL_TYPES[t]['label']:22s}: {n}")
    print()
    top = sorted(SIGNALS, key=lambda s: -signal_score(s))[:8]
    print("Top 8 by score:")
    for s in top:
        print(f"  {signal_score(s):>5.2f}  {s['muni']:25s} {s['state']}  "
              f"{SIGNAL_TYPES[s['type']]['label']:18s}  {s['headline']}")
