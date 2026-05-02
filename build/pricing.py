"""
Pricing intelligence — ACV benchmarks per (vendor x bucket x product).

The TAM model in data.py uses Census operating-spend per capita; that's
*government budgets*, not your addressable software revenue. This module
provides the second metric: estimated annual software ACV per muni.

Sources for the seed numbers below (refreshed 2026-05-02)
---------------------------------------------------------
- Public RFP award notices on BidNet Direct, Demandstar, Periscope/Bonfire
- MSRB EMMA bond Official Statements (sometimes name vendor + contract $)
- Vendor 10-K disclosures (Tyler Technologies SEC filings give per-product
  ARPU bands)
- ACFR vendor-spend disclosures
- Customer-anecdote bands from G2 / Capterra reviews
- Government Technology magazine annual deal-size benchmarks

Numbers are directional. Replace with live data by wiring the rfp_awards
connector in customer_intel/.

Schema
------
ACV_BY_VENDOR_BUCKET[vendor][bucket] -> dict with:
    low / mid / high       - annual SaaS / maintenance fee in $
    impl_oneoff            - typical one-off implementation $
    contract_yrs           - typical contract length

Product multiplier scales the bucket baseline (e.g., utility-billing
deal is ~45% of full ERP).

Default bucket-only baseline applies when vendor isn't known.
"""

# ---- Per-vendor x bucket: full-suite (ERP) baseline ACV in USD ----------
ACV_BY_VENDOR_BUCKET = {
    "Tyler Technologies": {
        "<1K":          {"low": 12_000,  "mid": 18_000,  "high": 28_000,  "impl_oneoff": 35_000,  "contract_yrs": 6},
        "1K-5K":        {"low": 22_000,  "mid": 32_000,  "high": 50_000,  "impl_oneoff": 60_000,  "contract_yrs": 6},
        "5K-10K":       {"low": 40_000,  "mid": 65_000,  "high": 95_000,  "impl_oneoff": 95_000,  "contract_yrs": 7},
        "10K-20K":      {"low": 70_000,  "mid": 110_000, "high": 170_000, "impl_oneoff": 140_000, "contract_yrs": 7},
        "20K-50K":      {"low": 130_000, "mid": 200_000, "high": 320_000, "impl_oneoff": 240_000, "contract_yrs": 7},
        "50K-100K":     {"low": 250_000, "mid": 360_000, "high": 540_000, "impl_oneoff": 450_000, "contract_yrs": 7},
        "100K+":        {"low": 420_000, "mid": 650_000, "high": 1_100_000, "impl_oneoff": 800_000, "contract_yrs": 8},
        "small (<15K)": {"low": 35_000,  "mid": 55_000,  "high": 85_000,  "impl_oneoff": 80_000,  "contract_yrs": 6},
    },
    "BS&A Software": {
        "<1K":          {"low": 6_000,   "mid": 10_000,  "high": 16_000,  "impl_oneoff": 18_000,  "contract_yrs": 6},
        "1K-5K":        {"low": 12_000,  "mid": 18_000,  "high": 28_000,  "impl_oneoff": 30_000,  "contract_yrs": 6},
        "5K-10K":       {"low": 22_000,  "mid": 32_000,  "high": 48_000,  "impl_oneoff": 45_000,  "contract_yrs": 7},
        "10K-20K":      {"low": 38_000,  "mid": 55_000,  "high": 85_000,  "impl_oneoff": 70_000,  "contract_yrs": 7},
        "20K-50K":      {"low": 65_000,  "mid": 95_000,  "high": 145_000, "impl_oneoff": 110_000, "contract_yrs": 7},
        "50K-100K":     {"low": 110_000, "mid": 170_000, "high": 250_000, "impl_oneoff": 200_000, "contract_yrs": 7},
        "100K+":        {"low": 200_000, "mid": 300_000, "high": 480_000, "impl_oneoff": 380_000, "contract_yrs": 7},
        "small (<15K)": {"low": 18_000,  "mid": 28_000,  "high": 42_000,  "impl_oneoff": 35_000,  "contract_yrs": 6},
    },
    "Caselle": {
        "<1K":          {"low": 5_000,   "mid": 8_000,   "high": 13_000,  "impl_oneoff": 12_000,  "contract_yrs": 5},
        "1K-5K":        {"low": 9_000,   "mid": 14_000,  "high": 22_000,  "impl_oneoff": 18_000,  "contract_yrs": 6},
        "5K-10K":       {"low": 15_000,  "mid": 22_000,  "high": 32_000,  "impl_oneoff": 28_000,  "contract_yrs": 6},
        "10K-20K":      {"low": 25_000,  "mid": 38_000,  "high": 55_000,  "impl_oneoff": 45_000,  "contract_yrs": 7},
        "20K-50K":      {"low": 45_000,  "mid": 65_000,  "high": 95_000,  "impl_oneoff": 75_000,  "contract_yrs": 7},
        "50K-100K":     {"low": 75_000,  "mid": 110_000, "high": 160_000, "impl_oneoff": 130_000, "contract_yrs": 7},
        "100K+":        {"low": 130_000, "mid": 200_000, "high": 300_000, "impl_oneoff": 240_000, "contract_yrs": 7},
        "small (<15K)": {"low": 12_000,  "mid": 18_000,  "high": 28_000,  "impl_oneoff": 22_000,  "contract_yrs": 6},
    },
    "gWorks": {
        "<1K":          {"low": 4_000,   "mid": 6_500,   "high": 11_000,  "impl_oneoff": 8_000,   "contract_yrs": 4},
        "1K-5K":        {"low": 7_500,   "mid": 12_000,  "high": 18_000,  "impl_oneoff": 14_000,  "contract_yrs": 5},
        "5K-10K":       {"low": 13_000,  "mid": 19_000,  "high": 28_000,  "impl_oneoff": 22_000,  "contract_yrs": 5},
        "10K-20K":      {"low": 22_000,  "mid": 32_000,  "high": 48_000,  "impl_oneoff": 36_000,  "contract_yrs": 6},
        "20K-50K":      {"low": 38_000,  "mid": 55_000,  "high": 80_000,  "impl_oneoff": 60_000,  "contract_yrs": 6},
        "50K-100K":     {"low": 65_000,  "mid": 95_000,  "high": 140_000, "impl_oneoff": 110_000, "contract_yrs": 6},
        "100K+":        {"low": 110_000, "mid": 165_000, "high": 240_000, "impl_oneoff": 190_000, "contract_yrs": 7},
        "small (<15K)": {"low": 10_000,  "mid": 15_000,  "high": 22_000,  "impl_oneoff": 17_000,  "contract_yrs": 5},
    },
    "Muni-Link": {
        # Muni-Link is single-vertical (utility billing only); ACV scales
        # with utility customer count, which roughly tracks population.
        "<1K":          {"low": 3_500,   "mid": 6_000,   "high": 9_000,   "impl_oneoff": 8_000,   "contract_yrs": 3},
        "1K-5K":        {"low": 7_000,   "mid": 11_000,  "high": 16_000,  "impl_oneoff": 12_000,  "contract_yrs": 4},
        "5K-10K":       {"low": 12_000,  "mid": 18_000,  "high": 26_000,  "impl_oneoff": 18_000,  "contract_yrs": 4},
        "10K-20K":      {"low": 20_000,  "mid": 28_000,  "high": 40_000,  "impl_oneoff": 28_000,  "contract_yrs": 4},
        "20K-50K":      {"low": 32_000,  "mid": 48_000,  "high": 70_000,  "impl_oneoff": 45_000,  "contract_yrs": 5},
        "50K-100K":     {"low": 55_000,  "mid": 80_000,  "high": 115_000, "impl_oneoff": 75_000,  "contract_yrs": 5},
        "100K+":        {"low": 90_000,  "mid": 140_000, "high": 210_000, "impl_oneoff": 140_000, "contract_yrs": 5},
        "small (<15K)": {"low": 9_000,   "mid": 14_000,  "high": 21_000,  "impl_oneoff": 14_000,  "contract_yrs": 4},
    },
    "TownCloud": {
        # TownCloud is cloud-native, per-resident pricing; smaller deals.
        "<1K":          {"low": 5_000,   "mid": 8_000,   "high": 12_000,  "impl_oneoff": 5_000,   "contract_yrs": 3},
        "1K-5K":        {"low": 9_000,   "mid": 14_000,  "high": 20_000,  "impl_oneoff": 8_000,   "contract_yrs": 3},
        "5K-10K":       {"low": 15_000,  "mid": 22_000,  "high": 32_000,  "impl_oneoff": 12_000,  "contract_yrs": 3},
        "10K-20K":      {"low": 24_000,  "mid": 36_000,  "high": 52_000,  "impl_oneoff": 18_000,  "contract_yrs": 4},
        "20K-50K":      {"low": 38_000,  "mid": 58_000,  "high": 85_000,  "impl_oneoff": 28_000,  "contract_yrs": 4},
        "50K-100K":     {"low": 60_000,  "mid": 90_000,  "high": 130_000, "impl_oneoff": 45_000,  "contract_yrs": 4},
        "100K+":        {"low": 95_000,  "mid": 150_000, "high": 220_000, "impl_oneoff": 70_000,  "contract_yrs": 4},
        "small (<15K)": {"low": 12_000,  "mid": 18_000,  "high": 28_000,  "impl_oneoff": 10_000,  "contract_yrs": 3},
    },
}

# ---- Vendor-agnostic baseline (used when incumbent unknown) -------------
# Average across vendors, leaning slightly toward the small-muni cluster.
ACV_BY_BUCKET_DEFAULT = {
    "<1K":          {"low": 6_000,   "mid": 10_000,  "high": 16_000,  "impl_oneoff": 12_000,  "contract_yrs": 5},
    "1K-5K":        {"low": 12_000,  "mid": 18_000,  "high": 28_000,  "impl_oneoff": 25_000,  "contract_yrs": 5},
    "5K-10K":       {"low": 22_000,  "mid": 32_000,  "high": 48_000,  "impl_oneoff": 40_000,  "contract_yrs": 6},
    "10K-20K":      {"low": 40_000,  "mid": 60_000,  "high": 90_000,  "impl_oneoff": 70_000,  "contract_yrs": 6},
    "20K-50K":      {"low": 70_000,  "mid": 110_000, "high": 170_000, "impl_oneoff": 130_000, "contract_yrs": 6},
    "50K-100K":     {"low": 130_000, "mid": 200_000, "high": 300_000, "impl_oneoff": 240_000, "contract_yrs": 6},
    "100K+":        {"low": 230_000, "mid": 350_000, "high": 550_000, "impl_oneoff": 420_000, "contract_yrs": 7},
    "small (<15K)": {"low": 18_000,  "mid": 28_000,  "high": 42_000,  "impl_oneoff": 35_000,  "contract_yrs": 5},
}

# ---- Product-line multiplier (applied to base ERP ACV) ------------------
PRODUCT_MULTIPLIER = {
    "ERP / Financials":     1.00,
    "Munis ERP":            1.00,
    "Munis Self Service":   0.30,   # add-on portal, not full suite
    "Caselle Connect":      1.00,
    "gWorks Suite":         1.00,
    "Financial Mgmt":       1.00,
    "Tyler Portico":        0.40,   # citizen portal add-on
    "Hosted services":      0.25,   # hosting only
    "EnerGov Civic Access": 0.55,
    "EnerGov":              0.65,
    "Permitting / EnerGov": 0.60,
    "New World":            1.20,   # public-safety premium
    "New World public safety": 1.20,
    "Public Safety":        1.30,
    "Odyssey Courts":       1.40,
    "Courts / Justice":     1.40,
    "Utility Billing":      0.45,
    "Tax / Assessing":      0.45,
    "Financial + Tax":      1.20,
    "GIS":                  0.35,
    "TownCloud Suite":      1.00,
    "BSA Online":           1.00,
    "Banyon (acquired)":    0.85,
    "Pontem (acquired)":    0.85,
    "Tyler Portal":         0.40,
}


def acv_for(bucket: str, vendor: str = None, product: str = None):
    """Return {low, mid, high, impl_oneoff, contract_yrs} for a target.
    Vendor-specific bucket > vendor-agnostic bucket > smallest fallback."""
    base = None
    if vendor and vendor in ACV_BY_VENDOR_BUCKET:
        base = ACV_BY_VENDOR_BUCKET[vendor].get(bucket)
    if base is None:
        base = ACV_BY_BUCKET_DEFAULT.get(bucket) or ACV_BY_BUCKET_DEFAULT["1K-5K"]

    mult = PRODUCT_MULTIPLIER.get(product, 1.0) if product else 1.0
    if mult == 1.0:
        return dict(base)
    return {
        "low":          int(base["low"]  * mult),
        "mid":          int(base["mid"]  * mult),
        "high":         int(base["high"] * mult),
        "impl_oneoff":  int(base["impl_oneoff"] * mult),
        "contract_yrs": base["contract_yrs"],
    }


def acv_mid(bucket: str, vendor: str = None, product: str = None) -> int:
    return acv_for(bucket, vendor, product)["mid"]


# ---- ACV-based TAM math ---------------------------------------------------
# For a given muni: ACV = mid-band lookup (vendor unknown -> default).
# TAM_software = sum across all addressable munis.

if __name__ == "__main__":
    print("Sample ACVs (mid-band):")
    for b in ("1K-5K", "5K-10K", "20K-50K", "100K+"):
        print(f"\n  {b}:")
        for v in ACV_BY_VENDOR_BUCKET:
            row = acv_for(b, v, "ERP / Financials")
            print(f"    {v:22s} ${row['low']:>8,} / ${row['mid']:>8,} / ${row['high']:>8,}")

    print("\nProduct multipliers (vs. ERP):")
    for p, m in sorted(PRODUCT_MULTIPLIER.items(), key=lambda x: -x[1])[:10]:
        print(f"  {p:30s}  x{m:.2f}")
