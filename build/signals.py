"""
Buying-signal taxonomy, scoring, and a focused demo dataset.

Each signal links a specific municipality to an event that creates near-term
buying intent (active RFP, leadership change, cyber incident, bond issuance,
compliance deadline, vendor EOL/M&A, audit finding).

This dataset is **focused** to the user's ICP and territory:
  - Population: sub-15,000 ONLY
  - States: New York, Pennsylvania, Maine, Ohio

All entries are flagged demo=True and use real muni names from those four
states with realistic populations. Vendor incumbents are best-effort
inferences based on each vendor's known geographic footprint (e.g.,
Caselle is uncommon in the Northeast; BS&A is gaining ground in OH;
Tyler New World legacy installs are common in NY/PA mid-size towns).
Replace by wiring the connectors in signals_pipeline.py to the real
sources listed there.

# refreshed 2026-05-03
"""

from datetime import date, timedelta


TODAY = date(2026, 5, 3)

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

RECENCY_HALFLIFE_DAYS = 60
HARD_DROPOFF_DAYS    = 180


# ---- Focused dataset: sub-15K munis in NY, PA, ME, OH --------------------

SIGNALS = [
    # ============== RFPs (16) ==============
    # ----- New York -----
    {
        "id": "sig_2026_001", "muni": "Tupper Lake", "state": "NY",
        "population": 3500, "bucket": "1K-5K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-22", "expires": "2026-06-15",
        "headline": "Village ERP RFP",
        "details": "Replacing legacy on-prem financials. SaaS preferred. Est. ACV $9-15K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_002", "muni": "Hudson", "state": "NY",
        "population": 6000, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-08", "expires": "2026-05-30",
        "headline": "Utility Billing System RFP",
        "details": "Water/sewer modernization. Est. ACV $14-22K.",
        "source": "Empire State Purchasing", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_003", "muni": "Olean", "state": "NY",
        "population": 14300, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-15", "expires": "2026-06-20",
        "headline": "Permitting + Code Enforcement RFP",
        "details": "Replacing 15-year-old custom system. Est. ACV $22-38K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_004", "muni": "Beacon", "state": "NY",
        "population": 14000, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-29", "expires": "2026-07-01",
        "headline": "Cloud ERP RFP",
        "details": "City-wide ERP replacement. Sourcewell vendors only. Est. ACV $32-50K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },

    # ----- Pennsylvania -----
    {
        "id": "sig_2026_005", "muni": "Lewistown", "state": "PA",
        "population": 8400, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-10", "expires": "2026-06-10",
        "headline": "Borough Financial Management RFP",
        "details": "Replacing on-prem accounting. Est. ACV $16-26K.",
        "source": "PA eMarketplace", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_006", "muni": "Bellefonte", "state": "PA",
        "population": 6000, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-18", "expires": "2026-06-30",
        "headline": "Utility Billing RFP",
        "details": "Water/sewer SaaS migration. Est. ACV $13-20K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Muni-Link", "demo": True,
    },
    {
        "id": "sig_2026_007", "muni": "Hershey", "state": "PA",
        "population": 13300, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-02", "expires": "2026-06-01",
        "headline": "Permitting + Tourism Tax RFP",
        "details": "Township-level deal. Est. ACV $24-42K.",
        "source": "PA eMarketplace", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_008", "muni": "Bradford", "state": "PA",
        "population": 7400, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-03-20", "expires": "2026-05-15",
        "headline": "Financial Management RFP",
        "details": "Sub-10K borough. Replacing aging Tyler New World legacy.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },

    # ----- Maine -----
    {
        "id": "sig_2026_009", "muni": "Belfast", "state": "ME",
        "population": 6800, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-25", "expires": "2026-07-01",
        "headline": "Town ERP RFP",
        "details": "Replacing 18-year-old on-prem system. Est. ACV $14-22K.",
        "source": "Maine Bid Portal", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_010", "muni": "Wiscasset", "state": "ME",
        "population": 3700, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-05", "expires": "2026-06-05",
        "headline": "Town Financial Management RFP",
        "details": "Sub-5K coastal town. SaaS only. Est. ACV $8-14K.",
        "source": "Maine Bid Portal", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_011", "muni": "Caribou", "state": "ME",
        "population": 7800, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-12", "expires": "2026-06-12",
        "headline": "Utility Billing + AR RFP",
        "details": "Aroostook County. Est. ACV $13-21K.",
        "source": "Maine Bid Portal", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_012", "muni": "Bar Harbor", "state": "ME",
        "population": 5000, "bucket": "1K-5K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-19", "expires": "2026-06-19",
        "headline": "Permitting + Land Use RFP",
        "details": "Tourism-driven town. Est. ACV $11-18K.",
        "source": "Maine Bid Portal", "url": None,
        "incumbent": None, "demo": True,
    },

    # ----- Ohio -----
    {
        "id": "sig_2026_013", "muni": "Wapakoneta", "state": "OH",
        "population": 9500, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-01", "expires": "2026-05-31",
        "headline": "City ERP RFP",
        "details": "Replacing aging accounting suite. Est. ACV $17-28K.",
        "source": "OhioBuys", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_014", "muni": "Bellefontaine", "state": "OH",
        "population": 13300, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-21", "expires": "2026-06-21",
        "headline": "Financial Management RFP",
        "details": "Mid-Ohio city. Est. ACV $22-36K.",
        "source": "OhioBuys", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_015", "muni": "Marietta", "state": "OH",
        "population": 13300, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-14", "expires": "2026-06-14",
        "headline": "Permitting + Code Enforcement RFP",
        "details": "Sub-15K river city. Est. ACV $24-40K.",
        "source": "OhioBuys", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_016", "muni": "Bryan", "state": "OH",
        "population": 8500, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-09", "expires": "2026-05-31",
        "headline": "Cloud ERP RFP",
        "details": "Small NW Ohio city. Est. ACV $16-26K.",
        "source": "Demandstar", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },

    # ============== Leadership changes (10) ==============
    # ----- New York -----
    {
        "id": "sig_2026_101", "muni": "Cooperstown", "state": "NY",
        "population": 1800, "bucket": "1K-5K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-15", "expires": None,
        "headline": "New Village Mayor",
        "details": "Sole software decision-maker for sub-2K village. Strong reset window.",
        "source": "Local press", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_102", "muni": "Geneva", "state": "NY",
        "population": 12800, "bucket": "10K-20K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-03-10", "expires": None,
        "headline": "New Finance Director",
        "details": "Cloud-systems background per LinkedIn. Modernization cited.",
        "source": "LinkedIn / city release", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_103", "muni": "Saranac Lake", "state": "NY",
        "population": 4800, "bucket": "1K-5K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-08", "expires": None,
        "headline": "New Village Treasurer",
        "details": "Adirondack village. First 90 days = vendor review window.",
        "source": "City press", "url": None,
        "incumbent": None, "demo": True,
    },

    # ----- Pennsylvania -----
    {
        "id": "sig_2026_104", "muni": "Lewisburg", "state": "PA",
        "population": 5700, "bucket": "5K-10K",
        "type": "leadership", "severity": "high",
        "detected": "2026-02-20", "expires": None,
        "headline": "New Borough Manager + Finance Officer",
        "details": "Two-thirds of buying committee replaced. Strong reset.",
        "source": "LinkedIn", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_105", "muni": "Selinsgrove", "state": "PA",
        "population": 5400, "bucket": "5K-10K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-12", "expires": None,
        "headline": "New Borough Secretary-Treasurer",
        "details": "Combined role. Cited modernization in inaugural memo.",
        "source": "Borough release", "url": None,
        "incumbent": "Muni-Link", "demo": True,
    },

    # ----- Maine -----
    {
        "id": "sig_2026_106", "muni": "Camden", "state": "ME",
        "population": 5200, "bucket": "5K-10K",
        "type": "leadership", "severity": "high",
        "detected": "2026-03-25", "expires": None,
        "headline": "New Town Manager",
        "details": "Modern coastal town. SaaS-first stated direction.",
        "source": "LinkedIn / town release", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_107", "muni": "Bath", "state": "ME",
        "population": 8400, "bucket": "5K-10K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-02-14", "expires": None,
        "headline": "New Finance Director",
        "details": "First budget cycle includes IT modernization line item.",
        "source": "Town press", "url": None,
        "incumbent": None, "demo": True,
    },

    # ----- Ohio -----
    {
        "id": "sig_2026_108", "muni": "Coshocton", "state": "OH",
        "population": 11400, "bucket": "10K-20K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-22", "expires": None,
        "headline": "New Finance Director",
        "details": "From private sector. Cited cloud-first stack.",
        "source": "LinkedIn", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_109", "muni": "Greenville", "state": "OH",
        "population": 12800, "bucket": "10K-20K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-26", "expires": None,
        "headline": "New City Auditor",
        "details": "Public statement re: vendor consolidation.",
        "source": "City press", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_110", "muni": "St. Marys", "state": "OH",
        "population": 8300, "bucket": "5K-10K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-30", "expires": None,
        "headline": "New Mayor + Auditor",
        "details": "Two-thirds turnover. Sub-10K reset window.",
        "source": "Local press", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },

    # ============== Cyber incidents (4 — focus states, generic placeholders) ==============
    {
        "id": "sig_2026_201", "muni": "Sub-10K NY village", "state": "NY",
        "population": 4200, "bucket": "1K-5K",
        "type": "cyber", "severity": "high",
        "detected": "2026-04-10", "expires": None,
        "headline": "Reported ransomware incident — services disrupted",
        "details": "Demo placeholder. Replace with MS-ISAC / NY breach registry data.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_202", "muni": "Sub-10K PA borough", "state": "PA",
        "population": 5500, "bucket": "5K-10K",
        "type": "cyber", "severity": "high",
        "detected": "2026-03-22", "expires": None,
        "headline": "Reported network intrusion",
        "details": "Demo placeholder. Forces cloud migration discussion.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_203", "muni": "Sub-15K ME town", "state": "ME",
        "population": 11000, "bucket": "10K-20K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-04-02", "expires": None,
        "headline": "Phishing incident — internal email compromise",
        "details": "Demo placeholder. Triggers security-stack review.",
        "source": "Local press (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_204", "muni": "Small OH city", "state": "OH",
        "population": 7800, "bucket": "5K-10K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-03-08", "expires": None,
        "headline": "Public disclosure of data breach",
        "details": "Demo placeholder. State-mandated notification triggered.",
        "source": "OH breach reports (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },

    # ============== Bond issuances (5 — focus states, sub-15K) ==============
    {
        "id": "sig_2026_301", "muni": "Glens Falls", "state": "NY",
        "population": 14500, "bucket": "10K-20K",
        "type": "bond", "severity": "medium",
        "detected": "2026-03-20", "expires": None,
        "headline": "$3.2M GO bond — IT modernization line item",
        "details": "Bond docs explicitly mention ERP replacement.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_302", "muni": "Sunbury", "state": "PA",
        "population": 9800, "bucket": "5K-10K",
        "type": "bond", "severity": "low",
        "detected": "2026-04-10", "expires": None,
        "headline": "$2.5M utility revenue bond",
        "details": "Water/sewer + metering modernization.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "Muni-Link", "demo": True,
    },
    {
        "id": "sig_2026_303", "muni": "Rockland", "state": "ME",
        "population": 7300, "bucket": "5K-10K",
        "type": "bond", "severity": "high",
        "detected": "2026-04-18", "expires": None,
        "headline": "$1.8M GO bond — software refresh",
        "details": "Bond statement explicitly mentions ERP replacement.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_304", "muni": "Findlay-area township", "state": "OH",
        "population": 4900, "bucket": "1K-5K",
        "type": "bond", "severity": "medium",
        "detected": "2026-03-30", "expires": None,
        "headline": "$1.2M GO bond",
        "details": "Sub-5K township. Capex includes software refresh.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_305", "muni": "Oneonta", "state": "NY",
        "population": 13000, "bucket": "10K-20K",
        "type": "bond", "severity": "medium",
        "detected": "2026-04-22", "expires": None,
        "headline": "$2.1M capital bond",
        "details": "Multi-year IT initiative noted in offering documents.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },

    # ============== Compliance deadlines (4 — state-mandated) ==============
    {
        "id": "sig_2026_401", "muni": "Statewide", "state": "NY",
        "population": 0, "bucket": None,
        "type": "compliance", "severity": "high",
        "detected": "2026-02-20", "expires": "2026-08-15",
        "headline": "NY SHIELD Act expanded enforcement",
        "details": "Expanded breach-notification scope. Security review for all NY munis.",
        "source": "NY DFS", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_402", "muni": "Statewide", "state": "PA",
        "population": 0, "bucket": None,
        "type": "compliance", "severity": "medium",
        "detected": "2026-03-01", "expires": "2026-09-30",
        "headline": "PA Local Government Cybersecurity Act phase-2",
        "details": "Sub-15K boroughs/townships must adopt cyber framework. Drives security-vendor refresh.",
        "source": "PA Auditor General", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_403", "muni": "Statewide", "state": "ME",
        "population": 0, "bucket": None,
        "type": "compliance", "severity": "medium",
        "detected": "2026-02-10", "expires": "2026-12-31",
        "headline": "ME municipal cyber-readiness reporting",
        "details": "Annual disclosure of vendor stack — opens RFP review windows.",
        "source": "ME Bureau of Information Services", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_404", "muni": "Statewide", "state": "OH",
        "population": 0, "bucket": None,
        "type": "compliance", "severity": "high",
        "detected": "2026-01-15", "expires": "2026-09-01",
        "headline": "OH HB23 cyber compliance deadline",
        "details": "All OH local govts must adopt cyber framework. Drives security-vendor refresh.",
        "source": "OH legislature", "url": None,
        "incumbent": None, "demo": True,
    },

    # ============== Vendor EOL / M&A (4 — states-relevant) ==============
    {
        "id": "sig_2026_501", "muni": "Vendor-wide", "state": "OH",
        "population": 0, "bucket": None,
        "type": "vendor_eol", "severity": "high",
        "detected": "2026-04-01", "expires": None,
        "headline": "BS&A Harris-driven product line consolidation",
        "details": "Constellation roll-up activity may force OH customers to re-evaluate.",
        "source": "Competitor watch", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_502", "muni": "Vendor-wide", "state": "PA",
        "population": 0, "bucket": None,
        "type": "vendor_eol", "severity": "medium",
        "detected": "2026-04-15", "expires": None,
        "headline": "Muni-Link pricing model change",
        "details": "Reported per-account pricing shift may surface RFPs from existing PA customers.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Muni-Link", "demo": True,
    },
    {
        "id": "sig_2026_503", "muni": "Vendor-wide", "state": "NY",
        "population": 0, "bucket": None,
        "type": "vendor_eol", "severity": "high",
        "detected": "2026-02-15", "expires": None,
        "headline": "Tyler New World legacy migration push",
        "details": "Tyler migrating ~600 NY/PA New World CAD/RMS customers. Disruption window.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_504", "muni": "Vendor-wide", "state": "ME",
        "population": 0, "bucket": None,
        "type": "vendor_eol", "severity": "medium",
        "detected": "2026-03-20", "expires": None,
        "headline": "Tyler Munis price uplift in Northeast",
        "details": "Reported 6-8% uplift on ME/NH/VT renewals — surfaces RFPs for switchers.",
        "source": "Competitor watch", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },

    # ============== Audit findings (5 — sub-15K, focus states) ==============
    {
        "id": "sig_2026_601", "muni": "Dunkirk", "state": "NY",
        "population": 12000, "bucket": "10K-20K",
        "type": "audit", "severity": "medium",
        "detected": "2026-03-12", "expires": None,
        "headline": "NY OSC audit cited financial-system controls",
        "details": "Material weakness flagged. Pressure to modernize.",
        "source": "NY State Comptroller", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_602", "muni": "St. Marys", "state": "PA",
        "population": 13000, "bucket": "10K-20K",
        "type": "audit", "severity": "medium",
        "detected": "2026-04-20", "expires": None,
        "headline": "Audit deficiency: cash reconciliation",
        "details": "Forces ERP/cash-management review.",
        "source": "PA Auditor General", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_603", "muni": "Houlton", "state": "ME",
        "population": 6000, "bucket": "5K-10K",
        "type": "audit", "severity": "high",
        "detected": "2026-03-05", "expires": None,
        "headline": "Audit recommendation: modernize AR + utility billing",
        "details": "Sub-10K Aroostook County town. Triggers billing system review.",
        "source": "ME Auditor", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_604", "muni": "Cambridge", "state": "OH",
        "population": 10400, "bucket": "10K-20K",
        "type": "audit", "severity": "high",
        "detected": "2026-04-08", "expires": None,
        "headline": "Audit: significant deficiency in financial system",
        "details": "OH State Auditor flagged controls gap. ERP review window.",
        "source": "OH State Auditor", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_605", "muni": "York", "state": "ME",
        "population": 14000, "bucket": "10K-20K",
        "type": "audit", "severity": "medium",
        "detected": "2026-04-15", "expires": None,
        "headline": "Audit: utility billing reconciliation issue",
        "details": "Triggers utility-billing system review.",
        "source": "ME Auditor", "url": None,
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
    by_state = {}
    pop_buckets = {"sub-15K": 0, "15K+": 0, "statewide": 0}
    for s in SIGNALS:
        by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        by_state[s["state"]] = by_state.get(s["state"], 0) + 1
        pop = s.get("population", 0) or 0
        if pop == 0:
            pop_buckets["statewide"] += 1
        elif pop < 15000:
            pop_buckets["sub-15K"] += 1
        else:
            pop_buckets["15K+"] += 1
    print(f"\nBy type:")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {SIGNAL_TYPES[t]['label']:22s}: {n}")
    print(f"\nBy state:")
    for st, n in sorted(by_state.items(), key=lambda x: -x[1]):
        print(f"  {st}: {n}")
    print(f"\nBy population: {pop_buckets}")
    print()
    top = sorted(SIGNALS, key=lambda s: -signal_score(s))[:8]
    print("Top 8 by score:")
    for s in top:
        pop_str = f"{s['population']:,}" if s.get('population') else "—"
        print(f"  {signal_score(s):>5.2f}  {s['muni']:25s} {s['state']}  "
              f"pop={pop_str:>7s}  {s['headline']}")
