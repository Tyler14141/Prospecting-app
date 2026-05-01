"""
Job-postings connector — search public job boards for muni listings that
require vendor-specific skills, e.g. "Experience with Tyler Munis".

How it works
------------
A finance director / IT analyst posting that requires "Tyler Munis" or
"BS&A" experience is a near-certain confirmation that the hiring muni
runs that vendor today. We search public job aggregators with vendor
keywords and extract the employer (which is almost always a city/county).

Implementation
--------------
This connector demonstrates the pattern with a public-mirror search URL.
For production, swap in:
  - Indeed Publisher API (free tier, 1K calls/day):
        https://www.indeed.com/publisher
  - USAJobs API (free, gov-only employers):
        https://developer.usajobs.gov/api-reference/get-api-search
  - LinkedIn job-postings API (paid; Sales Navigator integration)
  - Glassdoor partner API
  - Government Jobs (governmentjobs.com) — RSS feeds per agency

Run
---
    python -m customer_intel.connectors.job_postings
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request

from customer_intel import VENDOR_DOMAINS

UA = "Mozilla/5.0 (compatible; customer-intel/0.1)"

# Vendor -> list of search keywords most likely to appear in a job posting
# referring to that vendor's product
VENDOR_KEYWORDS = {
    "Tyler Technologies": ["Tyler Munis", "Tyler Technologies", "Munis ERP",
                            "New World Systems", "EnerGov"],
    "BS&A Software":      ["BS&A Software", "BSA software", "BS&A financials"],
    "Caselle":            ["Caselle", "Caselle Connect"],
    "gWorks":             ["gWorks", "Banyon Data"],
    "Muni-Link":          ["Muni-Link"],
    "TownCloud":          ["TownCloud"],
}


def search_indeed(keyword: str, max_results: int = 20) -> list:
    """
    Indeed search via the public web (best-effort scrape).
    Replace with the Publisher API for production:
        https://api.indeed.com/ads/apisearch?publisher=XXX&q=...
    """
    url = (
        "https://www.indeed.com/jobs?"
        + urllib.parse.urlencode({"q": keyword, "l": "United States",
                                    "fromage": "30"})
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"    indeed fetch failed: {e}")
        return []

    # Indeed embeds JSON job data — looser regex extraction than ideal,
    # robust enough for v1
    out = []
    # Look for "jobtitle" + "company" pairs in the result HTML
    for m in re.finditer(
            r'data-jk="([^"]+)"[\s\S]{0,500}?title="([^"]+)"[\s\S]{0,500}?'
            r'companyName[^>]*>([^<]+)<[\s\S]{0,500}?'
            r'companyLocation[^>]*>([^<]+)<', html):
        out.append({
            "title": m.group(2),
            "employer": m.group(3).strip(),
            "location": m.group(4).strip(),
            "url": f"https://www.indeed.com/viewjob?jk={m.group(1)}",
        })
        if len(out) >= max_results:
            break
    return out


def search_usajobs(keyword: str, max_results: int = 25) -> list:
    """
    USAJobs API (no key required for read-only).
    Federal jobs only — useful as a complement to muni-focused boards.
    """
    url = ("https://data.usajobs.gov/api/Search?"
            + urllib.parse.urlencode({"Keyword": keyword,
                                       "ResultsPerPage": str(max_results)}))
    req = urllib.request.Request(url, headers={
        "User-Agent": "customer-intel/0.1",
        "Host": "data.usajobs.gov",
        "Authorization-Key": "FAKE_KEY_REPLACE",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"    usajobs fetch failed: {e}")
        return []

    items = data.get("SearchResult", {}).get("SearchResultItems", [])
    out = []
    for it in items:
        d = it.get("MatchedObjectDescriptor", {})
        out.append({
            "title": d.get("PositionTitle"),
            "employer": d.get("OrganizationName"),
            "location": ", ".join(
                l.get("LocationName", "") for l in d.get("PositionLocation", [])
            ),
            "url": d.get("PositionURI"),
        })
    return out


# Match employer string to a state. "City of Springfield, MO" -> ("Springfield", "MO")
EMPLOYER_PAT = re.compile(
    r"^(City|Town|Village|Borough|County)\s+of\s+([A-Z][A-Za-z\.' \-]+)", re.I)
LOCATION_STATE_PAT = re.compile(r",\s*([A-Z]{2})\b")


def parse_employer(employer: str, location: str = ""):
    """Return (muni, state, type)."""
    muni = None
    typ = "muni"
    m = EMPLOYER_PAT.match(employer.strip())
    if m:
        muni = m.group(2).strip().rstrip(".,;")
        kind = m.group(1).lower()
        typ = "county" if kind == "county" else "muni"
    elif employer.lower().endswith(" county"):
        muni = employer[: -len(" County")].strip()
        typ = "county"
    state = None
    m2 = LOCATION_STATE_PAT.search(location or "")
    if m2:
        state = m2.group(1)
    return muni, state, typ


def harvest(per_keyword_max: int = 20) -> list:
    out = []
    for vendor, keywords in VENDOR_KEYWORDS.items():
        for kw in keywords:
            print(f"  job_postings: {vendor!r} q={kw!r} ...", end="", flush=True)
            jobs = search_indeed(kw, max_results=per_keyword_max)
            print(f" {len(jobs)} hits")
            for j in jobs:
                muni, state, typ = parse_employer(j["employer"],
                                                    j.get("location", ""))
                if not muni or not state:
                    continue
                out.append({
                    "vendor": vendor, "muni": muni, "state": state,
                    "type": typ, "bucket": None, "product": None,
                    "since": None,
                    "source": "job_posting",
                    "evidence": j["url"],
                    "confidence": 0.85,
                })
            time.sleep(2.0)  # friendly to indeed
    # Dedupe by (vendor, muni, state)
    keys = set()
    deduped = []
    for r in out:
        k = (r["vendor"], r["muni"], r["state"])
        if k in keys:
            continue
        keys.add(k)
        deduped.append(r)
    return deduped


if __name__ == "__main__":
    rows = harvest()
    print(f"\n{len(rows)} customers identified via job postings")
    by_v = {}
    for r in rows:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")
