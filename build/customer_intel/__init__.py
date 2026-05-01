"""
customer_intel — find competitor customers from free public sources.

Run from a machine with full internet access (this sandbox is allowlisted to
GitHub + PyPI only). Each connector returns Customer records that match the
schema in competitor_customers.py:

    {
      "vendor":   str,         # vendor name (must match COMPETITORS)
      "muni":     str,         # muni / county / SD name
      "state":    str,         # 2-letter abbrev (None if unresolved)
      "type":     str | None,  # "muni" | "county" | "township" | None
      "bucket":   str | None,  # population bucket (only if known)
      "product":  str | None,  # vendor module if known
      "since":    int | None,  # go-live year if known
      "source":   str,         # which connector produced this record
      "evidence": str,         # url / snippet supporting the find
      "confidence": float,     # 0.0–1.0; combined dedupe heuristic
    }

Pipeline:
    harvest()  -> ./customer_intel_raw.csv
    merge()    -> updates build/competitor_customers.py with new finds
                  (manual review recommended before committing)
"""
__version__ = "0.1.0"

VENDOR_DOMAINS = {
    "Tyler Technologies": [
        "tylertech.com", "tylerportals.com", "tylerportico.com",
        "tylerhost.net", "mytylerportal.com", "newworldsystems.com",
        "tylerciviccess.com", "munisselfservice.com",
    ],
    "BS&A Software": [
        "bsasoftware.com", "bsaonline.com",
    ],
    "Caselle": [
        "caselle.com",
    ],
    "gWorks": [
        "gworks.com", "banyondatasystems.com", "pontemsoftware.com",
        "compu-strategies.com",
    ],
    "Muni-Link": [
        "muni-link.com", "munilinkpa.com",
    ],
    "TownCloud": [
        "towncloud.com",
    ],
}

# Case-study / customer-list pages by vendor. Selectors are best-effort and
# may need tweaking when vendors redesign their sites.
VENDOR_CASE_STUDY_URLS = {
    "Tyler Technologies": [
        "https://www.tylertech.com/clients",
        "https://www.tylertech.com/about-us/customer-stories",
    ],
    "BS&A Software": [
        "https://www.bsasoftware.com/customer-stories/",
    ],
    "Caselle": [
        "https://caselle.com/about-us/customers/",
    ],
    "gWorks": [
        "https://www.gworks.com/case-studies/",
    ],
    "Muni-Link": [
        "https://www.muni-link.com/customers/",
    ],
    "TownCloud": [
        "https://www.towncloud.com/case-studies/",
    ],
}
