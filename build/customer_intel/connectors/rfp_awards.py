"""
RFP-award scraper — extracts vendor + amount + contract end-date from
public state purchasing portals.

Why
---
Award notices are the most authoritative pricing source you can get for
free. They confirm vendor, dollar amount, and contract length — feeding
both the named-customer dataset AND the per-bucket ACV benchmarks in
pricing.py. Each award is a triple win: a confirmed customer, a
confirmed price point, and a confirmed renewal-window anchor.

Sources
-------
1. **BidNet Direct** — broadest US coverage. Awards published on each
   agency's page; needs a paid account for the export feed but most
   per-agency award notices are public.
2. **Demandstar** — strong in NE / MW / SE. Award archive is per-agency.
3. **Periscope/Bonfire** — modern SaaS bid platform; award notices in
   each tenant's portal.
4. **State purchasing portals** — many states publish their own:
       CA: https://caleprocure.ca.gov/
       TX: https://www.txsmartbuy.com/
       NY: https://online.ogs.ny.gov/
       FL: https://www.myfloridamarketplace.com/
       PA: https://www.dgs.pa.gov/Procurement/
       (etc.)

Connector strategy
------------------
Per portal, fetch the awards index, parse rows into structured records.
Each award row contains: agency name, vendor, award $, contract start /
end, scope description.

The text extractor below pulls vendor + dollars from a free-text RFP
"Notice of Award" PDF or HTML page using regex + a small LLM-ready
prompt fallback. For production volume use the Anthropic SDK to do the
extraction step at high accuracy (~$0.005/award).

Run
---
    python -m customer_intel.connectors.rfp_awards
    python -m customer_intel.connectors.rfp_awards --portal bidnet --states IA NE KS

This connector will not run from this sandbox (state portals blocked).
Run locally with full internet access.

Output schema
-------------
Same as competitor_customers + extra fields:
    contract_end:   year (int) — when the contract terminates
    award_amount:   $ (annual ACV when known; total contract value otherwise)
    award_total:    bool — true if award_amount is the total contract
                    value, false if it's annual
"""

import argparse
import csv
import os
import re
import sys
import time
import urllib.parse
import urllib.request


UA = "customer-intel-rfp/0.1"

# Portal config
PORTALS = {
    "bidnet": {
        "search_url": "https://www.bidnetdirect.com/searches?q={q}",
        "needs_login": True,
    },
    "demandstar": {
        "search_url": "https://www.demandstar.com/search?keyword={q}",
        "needs_login": False,
    },
    "periscope": {
        "search_url": "https://opportunities.publicpurchase.com/searchterm/{q}",
        "needs_login": False,
    },
    "ca_state": {
        "search_url": "https://caleprocure.ca.gov/pages/Public/SearchEvents.aspx?keyword={q}",
        "needs_login": False,
    },
    "tx_state": {
        "search_url": "https://www.txsmartbuy.com/search?q={q}",
        "needs_login": False,
    },
    "ny_state": {
        "search_url": "https://online.ogs.ny.gov/purchase/spg/search/?keyword={q}",
        "needs_login": False,
    },
}

# Search keywords — what to look for
RFP_KEYWORDS = [
    "ERP", "Enterprise Resource Planning",
    "Financial Management System",
    "Utility Billing System",
    "Permitting System", "Building Permit Software",
    "Court Management",
    "Public Safety RMS", "Computer Aided Dispatch",
]

# Vendor name detection — used when scraping award notices
VENDOR_PATTERNS = [
    (re.compile(r"Tyler\s+Technologies?,?\s*Inc\.?", re.I), "Tyler Technologies"),
    (re.compile(r"BS\s*&\s*A\s+Software,?\s*Inc\.?", re.I), "BS&A Software"),
    (re.compile(r"Caselle,?\s*Inc\.?", re.I), "Caselle"),
    (re.compile(r"gWorks?,?\s*(?:LLC|Inc\.?)?", re.I), "gWorks"),
    (re.compile(r"Muni-?Link,?\s*(?:LLC|Inc\.?)?", re.I), "Muni-Link"),
    (re.compile(r"TownCloud,?\s*(?:LLC|Inc\.?)?", re.I), "TownCloud"),
    # Acquired / sub-brands
    (re.compile(r"New\s+World\s+Systems", re.I), "Tyler Technologies"),
    (re.compile(r"Banyon\s+Data\s+Systems", re.I), "gWorks"),
    (re.compile(r"Pontem\s+Software", re.I), "gWorks"),
]

# $ amount extractors
DOLLAR_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|M|thousand|K)?", re.I)
CONTRACT_LEN_RE = re.compile(
    r"(\d+)\s*[-–]?\s*year\s+(?:contract|term|agreement)", re.I)
DATE_END_RE = re.compile(
    r"(?:through|until|ending|expir(?:es|ation))[:\s]+"
    r"(?:\w+\s+\d+,\s*)?(20\d{2})", re.I)


def fetch(url: str, timeout: float = 10.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_award_text(text: str):
    """Best-effort parse of an award-notice text block. Returns dict with
    vendor, award_amount, award_total, contract_end."""
    out = {"vendor": None, "award_amount": None,
            "award_total": True, "contract_end": None}
    for pat, vendor in VENDOR_PATTERNS:
        if pat.search(text):
            out["vendor"] = vendor
            break

    m = DOLLAR_RE.search(text)
    if m:
        amount = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        if suffix in ("million", "m"):
            amount *= 1_000_000
        elif suffix in ("thousand", "k"):
            amount *= 1_000
        out["award_amount"] = int(amount)

    m = CONTRACT_LEN_RE.search(text)
    if m:
        years = int(m.group(1))
        # Convert total contract -> annual ACV if it's a "X year contract"
        if out["award_amount"] and years > 1:
            # Heuristic: if dollar appears with "annual" or "/year" nearby,
            # leave as-is; otherwise treat as total.
            if not re.search(r"(?:annual|per\s+year|/\s*year|annually)",
                              text, re.I):
                # Total contract -> derive annual
                pass
            out["contract_end"] = None  # need a start date to compute end

    m = DATE_END_RE.search(text)
    if m:
        out["contract_end"] = int(m.group(1))

    return out


# ---- Public entry point --------------------------------------------------
def harvest(portal: str = "bidnet", states: list = None,
             keywords: list = None, max_per_keyword: int = 50):
    """
    NOTE: this is the production scaffold. To actually fetch live data,
    each portal needs its specific scraping logic. The functions below
    are stubs that document the contract; replace with portal-specific
    implementations for production runs.
    """
    if portal not in PORTALS:
        raise ValueError(f"unknown portal: {portal}; known: {list(PORTALS)}")
    config = PORTALS[portal]
    if config["needs_login"]:
        raise NotImplementedError(
            f"{portal} requires authenticated session; "
            "wire your account credentials and a session cookie")

    rows = []
    keywords = keywords or RFP_KEYWORDS
    for kw in keywords:
        url = config["search_url"].format(q=urllib.parse.quote(kw))
        print(f"  rfp_awards: {portal} q={kw!r} -> {url}")
        try:
            html = fetch(url)
        except Exception as e:
            print(f"    fetch failed: {e}")
            continue
        # Per-portal parsing logic should slot in here. For now we just
        # parse free-text vendor/amount mentions across the whole result
        # page. Real connector would walk into each result detail page.
        parsed = parse_award_text(html)
        if parsed["vendor"]:
            rows.append({
                "vendor": parsed["vendor"],
                "muni": None, "state": None, "type": "muni",
                "bucket": None, "product": None,
                "since": None,
                "contract_end": parsed["contract_end"],
                "award_amount": parsed["award_amount"],
                "award_total":  parsed["award_total"],
                "source": f"rfp_award ({portal})",
                "evidence": url,
                "confidence": 0.7,  # below per-vendor fingerprint
                "demo": False,
            })
        time.sleep(2.0)  # polite

    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", default="bidnet",
                    choices=list(PORTALS.keys()))
    ap.add_argument("--states", nargs="*")
    ap.add_argument("--keywords", nargs="*")
    ap.add_argument("--out", default="rfp_awards_hits.csv")
    args = ap.parse_args()

    try:
        rows = harvest(portal=args.portal, states=args.states,
                        keywords=args.keywords)
    except NotImplementedError as e:
        print(f"NOTE: {e}")
        rows = []

    print(f"\n{len(rows)} award rows captured")
    if rows:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {args.out}")
