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
    # ===== RFPs (20) — focused on sub-15K ICP (small munis) =====
    {
        "id": "sig_2026_001", "muni": "Decorah", "state": "IA",
        "population": 7800, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-22", "expires": "2026-06-15",
        "headline": "ERP / Financial Management RFP",
        "details": "Replacing on-prem financials. Cloud-native required. Est. ACV $20-35K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_002", "muni": "Indianola", "state": "IA",
        "population": 16400, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-08", "expires": "2026-05-30",
        "headline": "Utility Billing System RFP",
        "details": "Water/sewer. SaaS preferred. Est. ACV $15-28K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_003", "muni": "Livingston", "state": "MT",
        "population": 8400, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-15", "expires": "2026-06-20",
        "headline": "Permitting & Code Enforcement RFP",
        "details": "Building/planning workflow. Est. ACV $18-32K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_004", "muni": "Buffalo", "state": "WY",
        "population": 4600, "bucket": "1K-5K",
        "type": "rfp", "severity": "high",
        "detected": "2026-03-28", "expires": "2026-05-15",
        "headline": "Financial Management & Payroll RFP",
        "details": "Small-town ERP. Sourcewell preferred. Est. ACV $12-22K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_005", "muni": "Heber City", "state": "UT",
        "population": 17500, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-10", "expires": "2026-06-10",
        "headline": "ERP Modernization RFP",
        "details": "Migrating from on-prem to cloud. Est. ACV $30-50K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_006", "muni": "Glenwood Springs", "state": "CO",
        "population": 9700, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-18", "expires": "2026-06-30",
        "headline": "Cloud ERP RFP",
        "details": "Replacing legacy desktop system. Est. ACV $22-38K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_007", "muni": "Devils Lake", "state": "ND",
        "population": 7200, "bucket": "5K-10K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-02", "expires": "2026-06-01",
        "headline": "ERP Consolidation RFP",
        "details": "Consolidating 3 legacy systems. Est. ACV $25-40K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_008", "muni": "Hays", "state": "KS",
        "population": 21000, "bucket": "20K-50K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-03-20", "expires": "2026-05-05",
        "headline": "Financial System Replacement RFP",
        "details": "On-prem to SaaS. Sourcewell-eligible vendors only. Est. ACV $35-55K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_009", "muni": "Bolivar", "state": "MO",
        "population": 11800, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-25", "expires": "2026-07-01",
        "headline": "Small-City ERP RFP",
        "details": "Full ERP replacement. Est. ACV $22-38K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_010", "muni": "Crawfordsville", "state": "IN",
        "population": 16100, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-05", "expires": "2026-06-05",
        "headline": "Cloud ERP RFP",
        "details": "Replacing legacy financials. Est. ACV $28-45K.",
        "source": "Periscope/Bonfire", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_011", "muni": "Norwalk", "state": "OH",
        "population": 16800, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-12", "expires": "2026-06-12",
        "headline": "Permitting Modernization RFP",
        "details": "Building/planning system replacement. Est. ACV $20-35K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_012", "muni": "Pittsburg", "state": "KS",
        "population": 19500, "bucket": "10K-20K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-03-15", "expires": "2026-05-15",
        "headline": "Utility Billing RFP",
        "details": "Water + electric. Est. ACV $18-32K.",
        "source": "Demandstar", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_013", "muni": "Branson", "state": "MO",
        "population": 12800, "bucket": "10K-20K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-29", "expires": "2026-07-15",
        "headline": "Permitting & Tourism Tax RFP",
        "details": "Replacing 12-year-old custom system. Est. ACV $30-48K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_014", "muni": "Beloit", "state": "KS",
        "population": 3400, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-19", "expires": "2026-06-19",
        "headline": "Small-Town ERP RFP",
        "details": "Replacing 15-year-old DOS-era system. Est. ACV $9-16K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_015", "muni": "Greybull", "state": "WY",
        "population": 1750, "bucket": "1K-5K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-01", "expires": "2026-05-31",
        "headline": "Financial Management RFP",
        "details": "Replacing Caselle DOS. Est. ACV $7-13K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_016", "muni": "Plain City", "state": "OH",
        "population": 4900, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-21", "expires": "2026-06-21",
        "headline": "Utility Billing + AR RFP",
        "details": "Sub-5K muni. SaaS only. Est. ACV $9-15K.",
        "source": "Demandstar", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_017", "muni": "Madisonville", "state": "TN",
        "population": 4900, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-14", "expires": "2026-06-14",
        "headline": "Cloud ERP for small towns RFP",
        "details": "Modern SaaS preferred. Est. ACV $8-14K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_018", "muni": "Sutton", "state": "NE",
        "population": 1500, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-09", "expires": "2026-05-31",
        "headline": "Village Software RFP",
        "details": "All-in-one for utility billing + AR. Est. ACV $6-11K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_019", "muni": "Boonville", "state": "MO",
        "population": 7900, "bucket": "5K-10K",
        "type": "rfp", "severity": "high",
        "detected": "2026-04-26", "expires": "2026-06-26",
        "headline": "Sub-10K City ERP RFP",
        "details": "Replacing legacy. Est. ACV $14-24K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Tyler Technologies", "demo": True,
    },
    {
        "id": "sig_2026_020", "muni": "Cuba", "state": "MO",
        "population": 3300, "bucket": "1K-5K",
        "type": "rfp", "severity": "medium",
        "detected": "2026-04-03", "expires": "2026-05-30",
        "headline": "Small-Town Financial Mgmt RFP",
        "details": "Replacing Caselle. Est. ACV $7-13K.",
        "source": "BidNet Direct", "url": None,
        "incumbent": "Caselle", "demo": True,
    },

    # ===== Leadership changes (10) — sub-15K dominant =====
    {
        "id": "sig_2026_101", "muni": "Postville", "state": "IA",
        "population": 2500, "bucket": "1K-5K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-15", "expires": None,
        "headline": "New City Clerk-Treasurer (combined role)",
        "details": "First 90 days — typical software review window for sub-5K towns.",
        "source": "LinkedIn / city press release", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_102", "muni": "Salida", "state": "CO",
        "population": 5800, "bucket": "5K-10K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-03-10", "expires": None,
        "headline": "New Finance Director hired",
        "details": "Background in cloud financial systems. Modernization cited.",
        "source": "City press release", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_103", "muni": "Red Lodge", "state": "MT",
        "population": 2300, "bucket": "1K-5K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-08", "expires": None,
        "headline": "New City Treasurer + Clerk",
        "details": "Dual-role reset window — typical for sub-5K towns.",
        "source": "LinkedIn / city release", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_104", "muni": "Polson", "state": "MT",
        "population": 5300, "bucket": "5K-10K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-02-20", "expires": None,
        "headline": "New Finance Director",
        "details": "From private sector. Likely fresh look at vendor stack.",
        "source": "LinkedIn", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_105", "muni": "Brookings", "state": "SD",
        "population": 24000, "bucket": "20K-50K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-12", "expires": None,
        "headline": "New IT Coordinator",
        "details": "Cloud-first stated direction in inaugural memo.",
        "source": "City announcement", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_106", "muni": "Rexburg", "state": "ID",
        "population": 28500, "bucket": "20K-50K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-03-25", "expires": None,
        "headline": "New Finance Director",
        "details": "First 90-day review of legacy systems underway.",
        "source": "LinkedIn", "url": None,
        "incumbent": "Caselle", "demo": True,
    },
    {
        "id": "sig_2026_107", "muni": "Pawnee", "state": "OK",
        "population": 2100, "bucket": "1K-5K",
        "type": "leadership", "severity": "high",
        "detected": "2026-02-14", "expires": None,
        "headline": "New City Clerk",
        "details": "Sole software decision-maker for this town. Strong reset window.",
        "source": "Local press", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_108", "muni": "Larned", "state": "KS",
        "population": 3700, "bucket": "1K-5K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-22", "expires": None,
        "headline": "New Mayor + new Clerk",
        "details": "Two-thirds of the buying committee replaced — sub-5K reset.",
        "source": "City press", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_109", "muni": "Brookings", "state": "OR",
        "population": 6700, "bucket": "5K-10K",
        "type": "leadership", "severity": "medium",
        "detected": "2026-04-26", "expires": None,
        "headline": "New Finance Director",
        "details": "Coastal small town. Fresh look incoming.",
        "source": "LinkedIn", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_110", "muni": "Aspen", "state": "CO",
        "population": 7000, "bucket": "5K-10K",
        "type": "leadership", "severity": "high",
        "detected": "2026-04-30", "expires": None,
        "headline": "New CFO + Council majority change",
        "details": "Resort town with high ACV potential. Vendor stack review imminent.",
        "source": "City announcement", "url": None,
        "incumbent": "Caselle", "demo": True,
    },

    # ===== Cyber incidents (4 — small munis, generic placeholders) =====
    {
        "id": "sig_2026_201", "muni": "Small MI village", "state": "MI",
        "population": 2200, "bucket": "1K-5K",
        "type": "cyber", "severity": "high",
        "detected": "2026-04-10", "expires": None,
        "headline": "Reported ransomware incident — services disrupted",
        "details": "Demo placeholder. Replace with MS-ISAC / news feed.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_202", "muni": "Small TX town", "state": "TX",
        "population": 4100, "bucket": "1K-5K",
        "type": "cyber", "severity": "high",
        "detected": "2026-03-22", "expires": None,
        "headline": "Reported network intrusion",
        "details": "Demo placeholder. Forces cloud migration discussion.",
        "source": "MS-ISAC (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_203", "muni": "Sub-10K FL muni", "state": "FL",
        "population": 7400, "bucket": "5K-10K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-04-02", "expires": None,
        "headline": "Phishing incident — internal email compromise",
        "details": "Demo placeholder. Triggers security-stack review.",
        "source": "Local press (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_204", "muni": "Small CA muni", "state": "CA",
        "population": 3800, "bucket": "1K-5K",
        "type": "cyber", "severity": "medium",
        "detected": "2026-03-08", "expires": None,
        "headline": "Public disclosure of data breach",
        "details": "Demo placeholder. State-mandated notification triggered.",
        "source": "CA AG breach reports (placeholder)", "url": None,
        "incumbent": None, "demo": True,
    },

    # ===== Bond issuances (6 — sub-15K dominant) =====
    {
        "id": "sig_2026_301", "muni": "Hudson", "state": "WI",
        "population": 14600, "bucket": "10K-20K",
        "type": "bond", "severity": "medium",
        "detected": "2026-03-20", "expires": None,
        "headline": "$8M general obligation bond issued",
        "details": "IT/equipment line item present. Capex headroom for software.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_302", "muni": "Whitewater", "state": "WI",
        "population": 14900, "bucket": "10K-20K",
        "type": "bond", "severity": "low",
        "detected": "2026-04-10", "expires": None,
        "headline": "$4M utility revenue bond",
        "details": "Water/sewer + metering modernization.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_303", "muni": "Anamosa", "state": "IA",
        "population": 5500, "bucket": "5K-10K",
        "type": "bond", "severity": "high",
        "detected": "2026-04-18", "expires": None,
        "headline": "$3.2M GO bond — IT modernization line item",
        "details": "Bond statement explicitly mentions ERP replacement.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_304", "muni": "York", "state": "NE",
        "population": 7800, "bucket": "5K-10K",
        "type": "bond", "severity": "medium",
        "detected": "2026-03-30", "expires": None,
        "headline": "$2.5M GO bond",
        "details": "Capex for FY26-27 includes software refresh.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_305", "muni": "Greenfield", "state": "MA",
        "population": 17400, "bucket": "10K-20K",
        "type": "bond", "severity": "low",
        "detected": "2026-04-05", "expires": None,
        "headline": "$5M capital bond",
        "details": "Multi-year IT initiative noted in offering documents.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_306", "muni": "Cody", "state": "WY",
        "population": 9800, "bucket": "5K-10K",
        "type": "bond", "severity": "medium",
        "detected": "2026-04-22", "expires": None,
        "headline": "$2.8M GO bond — software refresh",
        "details": "Sub-10K town. Bond proceeds include ERP replacement.",
        "source": "MSRB EMMA", "url": None,
        "incumbent": "Caselle", "demo": True,
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

    # ===== Audit findings (5 — sub-15K dominant) =====
    {
        "id": "sig_2026_601", "muni": "Bay City", "state": "MI",
        "population": 4900, "bucket": "1K-5K",
        "type": "audit", "severity": "high",
        "detected": "2026-03-12", "expires": None,
        "headline": "State audit cited financial-system controls",
        "details": "Material weakness flagged in financials — pressure to modernize.",
        "source": "MI auditor general", "url": None,
        "incumbent": "BS&A Software", "demo": True,
    },
    {
        "id": "sig_2026_602", "muni": "Beckley", "state": "WV",
        "population": 16200, "bucket": "10K-20K",
        "type": "audit", "severity": "medium",
        "detected": "2026-04-20", "expires": None,
        "headline": "Audit deficiency: cash reconciliation",
        "details": "Forces ERP/cash-management review.",
        "source": "WV state auditor", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_603", "muni": "Cleveland", "state": "MS",
        "population": 11200, "bucket": "10K-20K",
        "type": "audit", "severity": "medium",
        "detected": "2026-03-05", "expires": None,
        "headline": "Audit recommendation: modernize AR",
        "details": "Non-material but flagged — opens permitting/billing conversation.",
        "source": "MS state auditor", "url": None,
        "incumbent": None, "demo": True,
    },
    {
        "id": "sig_2026_604", "muni": "Chamberlain", "state": "SD",
        "population": 2500, "bucket": "1K-5K",
        "type": "audit", "severity": "high",
        "detected": "2026-04-08", "expires": None,
        "headline": "Audit: significant deficiency in financial system",
        "details": "Sub-5K town. Aging on-prem system flagged.",
        "source": "SD state auditor", "url": None,
        "incumbent": "gWorks", "demo": True,
    },
    {
        "id": "sig_2026_605", "muni": "Vinton", "state": "IA",
        "population": 5200, "bucket": "5K-10K",
        "type": "audit", "severity": "medium",
        "detected": "2026-04-15", "expires": None,
        "headline": "Audit: utility billing reconciliation issue",
        "details": "Triggers utility-billing system review for sub-10K town.",
        "source": "IA state auditor", "url": None,
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
