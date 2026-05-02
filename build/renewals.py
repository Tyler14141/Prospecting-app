"""
Renewal-window estimator.

Most local-gov ERP / vendor contracts run on multi-year cycles. RFPs
typically issue 12-18 months before contract end. Knowing where each
known incumbent customer sits in their cycle is the difference between
"call in 2 years" and "they're in market right now".

Heuristic
---------
Given a customer's known go-live year:
    typical_cycle    = 5 to 7 years (varies by product / vendor)
    next_renewal_min = since + cycle_min
    next_renewal_max = since + cycle_max
    rfp_window_open  = next_renewal_min - 1.5 years
    rfp_window_close = next_renewal_max - 0.5 years

Status buckets (relative to today):
    "active"        — far from renewal (>3yr away)
    "warming"       — renewal in 18-36 months
    "in-window"     — RFP-ready right now (typically 6-18mo from end)
    "imminent"      — likely re-procuring within 12 months
    "past-due"      — model expected renewal already passed (vendor extended)
    "unknown"       — no go-live year on record

Vendor-specific cycle overrides (best-effort; refine from your own win/loss):

    Tyler Munis             7 yrs  (long, sticky enterprise)
    Tyler New World         6 yrs
    Tyler EnerGov           5 yrs
    BS&A Software           7 yrs  (sticky in MI; long renewals)
    Caselle                 6 yrs  (older legacy contracts)
    gWorks                  5 yrs  (small-town SaaS, faster cycles)
    Muni-Link               4 yrs  (utility billing — shorter)
    TownCloud               3 yrs  (new SaaS — early renewals common)

# refreshed 2026-05-02
"""

from datetime import date


TODAY = date(2026, 5, 2)
TODAY_YEAR_FRAC = TODAY.year + (TODAY.month - 1) / 12.0

# (cycle_min_years, cycle_max_years) per vendor / product class
DEFAULT_CYCLE = (5, 7)
VENDOR_CYCLE = {
    "Tyler Technologies": (5, 7),   # default; product-specific below
    "BS&A Software":      (5, 7),
    "Caselle":            (5, 7),
    "gWorks":             (4, 6),
    "Muni-Link":          (3, 5),
    "TownCloud":          (3, 4),
}
PRODUCT_CYCLE_OVERRIDES = {
    # product substring (lowercase) -> (min, max)
    "munis":          (6, 8),
    "enterprise erp": (6, 8),
    "new world":      (5, 7),
    "energov":        (4, 6),
    "civic access":   (4, 6),
    "courts":         (7, 10),
    "odyssey":        (7, 10),
    "utility billing":(3, 5),
    "muni-link":      (3, 5),
    "towncloud":      (3, 4),
    "caselle":        (5, 7),
}


def _cycle_for(vendor: str, product: str = None):
    if product:
        plow = product.lower()
        for k, c in PRODUCT_CYCLE_OVERRIDES.items():
            if k in plow:
                return c
    return VENDOR_CYCLE.get(vendor, DEFAULT_CYCLE)


def renewal_window(vendor: str, since_year, product: str = None,
                    today: float = TODAY_YEAR_FRAC):
    """Returns dict with renewal-window analysis for one customer.

    since_year may be int (year) or None (unknown go-live)."""
    cmin, cmax = _cycle_for(vendor, product)
    if not since_year:
        # Mid-cycle assumption — RFP within next 18-36 mo
        return {
            "status": "unknown",
            "since": None,
            "cycle_min": cmin, "cycle_max": cmax,
            "next_renewal_min": None,
            "next_renewal_max": None,
            "rfp_window_open": None,
            "rfp_window_close": None,
            "months_until_window": None,
            "label": f"unknown go-live (assume {cmin}-{cmax} yr cycle)",
        }
    nr_min = since_year + cmin
    nr_max = since_year + cmax
    rfp_open  = nr_min - 1.5
    rfp_close = nr_max - 0.5
    months_until = (rfp_open - today) * 12

    if today < rfp_open - 1.0:
        status, label = "active", f"renewal {nr_min}-{nr_max}"
    elif rfp_open - 1.0 <= today < rfp_open:
        status, label = "warming", f"warming for {nr_min}-{nr_max} renewal"
    elif rfp_open <= today <= rfp_close:
        status, label = "in-window", f"in renewal window now ({nr_min}-{nr_max})"
    elif rfp_close < today <= nr_max + 0.5:
        status, label = "imminent", f"imminent renewal ({nr_min}-{nr_max})"
    else:
        status, label = "past-due", f"past expected renewal ({nr_max} cycle, vendor extended)"

    return {
        "status": status,
        "since": since_year,
        "cycle_min": cmin, "cycle_max": cmax,
        "next_renewal_min": nr_min,
        "next_renewal_max": nr_max,
        "rfp_window_open": round(rfp_open, 2),
        "rfp_window_close": round(rfp_close, 2),
        "months_until_window": round(months_until, 1),
        "label": label,
    }


# Status -> sort priority (lower = more urgent for outbound)
STATUS_PRIORITY = {
    "in-window": 0,
    "imminent":  1,
    "warming":   2,
    "past-due":  3,
    "unknown":   4,
    "active":    5,
}


if __name__ == "__main__":
    # Sample: Boston Tyler Munis since 2008 -> long past renewal
    samples = [
        ("Tyler Technologies", 2008, "Munis ERP"),
        ("Tyler Technologies", 2017, "Munis ERP"),
        ("Tyler Technologies", 2021, "Munis ERP"),
        ("BS&A Software",      2010, "Financial Mgmt"),
        ("Caselle",            2007, "Caselle Connect"),
        ("gWorks",              2018, "gWorks Suite"),
        ("Muni-Link",          2018, "Utility Billing"),
        ("TownCloud",          2023, "TownCloud Suite"),
        ("Tyler Technologies", None, None),  # unknown
    ]
    for v, y, p in samples:
        rw = renewal_window(v, y, p)
        print(f"  {v:22s} since={str(y):4s}  product={p or '-':25s}  "
              f"-> {rw['status']:10s}  {rw['label']}")
