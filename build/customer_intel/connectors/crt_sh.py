"""
Certificate Transparency log connector — finds vendor-hosted muni subdomains.

How it works
------------
Most local-gov ERP vendors host customer portals on a per-customer subdomain
of one of their main domains (e.g., "cityofdesmoines.tylerportico.com",
"saginaw.bsaonline.com"). Every TLS cert issued for those subdomains is
publicly logged in Certificate Transparency. crt.sh is a free, no-auth
search interface to the CT logs.

We query crt.sh for each vendor domain, harvest all SAN entries (Subject
Alternative Names), strip the vendor TLD, and run the leading subdomain
through a muni-name extractor. Hits are joined back to a US places list
to produce (vendor, muni, state) records.

Coverage / limits
-----------------
- High precision: a hit means a real cert was issued for that subdomain.
  False positives mostly come from non-customer subdomains like "www",
  "support", "demo", "sandbox" — filtered below.
- Coverage varies by vendor. Tyler/BS&A: very high (per-customer portals
  are standard). Caselle: lower (more on-prem). TownCloud: high (cloud-
  native). gWorks: mixed.
- crt.sh rate limits: ~1 req/sec for unauthenticated. Sleep between calls.

Run
---
    python -m customer_intel.connectors.crt_sh

Outputs candidates to stdout. The full pipeline (harvest.py) calls this and
merges with other connectors.
"""

import json
import re
import time
import urllib.parse
import urllib.request

from customer_intel import VENDOR_DOMAINS


CRT_SH_BASE = "https://crt.sh/?q=%25.{domain}&output=json"

# Subdomains to ignore — these are vendor-internal, not customers.
IGNORE_SUBS = {
    "www", "mail", "admin", "support", "sandbox", "demo", "staging", "stage",
    "test", "dev", "qa", "uat", "internal", "vpn", "portal", "api", "auth",
    "login", "sso", "cdn", "static", "media", "blog", "marketing", "downloads",
    "training", "help", "kb", "kbase", "intranet", "extranet", "partners",
    "secure", "files", "ftp", "smtp", "imap", "calendar", "exchange",
    "office365", "remote", "cloud", "monitor", "metrics", "status",
    "test-portal", "uat-portal", "dev-portal",
}


def fetch_certs(domain: str, retries: int = 3, backoff: float = 2.0):
    """Fetch all CT log entries for *.<domain> from crt.sh."""
    url = CRT_SH_BASE.format(domain=domain)
    req = urllib.request.Request(url, headers={"User-Agent": "customer-intel/0.1"})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(f"crt.sh failed for {domain}: {last_err}")


def extract_subdomains(certs: list, vendor_domain: str) -> set:
    """Pull unique subdomain prefixes from CT records."""
    out = set()
    suffix = "." + vendor_domain.lower()
    for c in certs:
        # 'name_value' may contain multiple SANs separated by newlines
        for n in (c.get("name_value", "") or "").split("\n"):
            n = n.strip().lower()
            if not n or "*" in n:
                continue
            if not n.endswith(suffix):
                continue
            sub = n[: -len(suffix)]
            if not sub:
                continue
            # Multi-label subdomains: take the leftmost label
            label = sub.split(".")[0]
            if label and label not in IGNORE_SUBS:
                out.add(label)
    return out


# ---- Muni-name extractor -------------------------------------------------
# Subdomains often follow patterns like:
#    cityofdesmoines, des-moines, desmoines, desmoinesia, cofdesmoines,
#    desmoines-ia, town-of-greenwood, vil-pleasantville, oxfordtwp
# We strip common prefixes/suffixes and split CamelCase / hyphens.

PREFIXES = [
    "cityof", "townof", "townshipof", "villageof", "boroughof", "countyof",
    "city-of", "town-of", "village-of", "borough-of", "county-of",
    "cof", "tof", "vof", "co", "city", "town", "village", "twp", "township",
]
SUFFIXES = ["city", "town", "twp", "township", "village", "vil", "vlg",
             "boro", "borough", "co", "county"]
STATE_HINT_RE = re.compile(r"[-_]([a-z]{2})$")  # trailing -ia, _ny, etc.


def extract_muni_candidate(label: str):
    """Return (muni_name, state_hint) — best-effort parse."""
    s = label.lower()
    state_hint = None
    m = STATE_HINT_RE.search(s)
    if m:
        state_hint = m.group(1).upper()
        s = s[: m.start()]
    s = s.replace("_", "-")
    for p in sorted(PREFIXES, key=len, reverse=True):
        if s.startswith(p):
            s = s[len(p):]
            break
    for suf in sorted(SUFFIXES, key=len, reverse=True):
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
            break
    s = s.strip("-")
    # Split CamelCase compounds — but inputs are lowercased, so split on
    # hyphen instead. Keep multi-word names joined with spaces.
    parts = [p for p in s.split("-") if p]
    if not parts:
        return None, state_hint
    name = " ".join(p.capitalize() for p in parts)
    return name, state_hint


# ---- US places lookup ----------------------------------------------------
# Reuse names_data.json built by build_names_data.py. We use it to confirm
# the candidate is a real muni and resolve its state.

def load_places(names_data_path: str = None) -> dict:
    """Returns {lower_name: [(state, pop), ...]} index across all 50+DC."""
    import os
    if names_data_path is None:
        here = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        names_data_path = os.path.join(here, "names_data.json")
    if not os.path.exists(names_data_path):
        return {}
    with open(names_data_path) as f:
        data = json.load(f)
    idx = {}
    for st, blob in data.items():
        for c in blob.get("cities", []):
            idx.setdefault(c["name"].lower(), []).append((st, c.get("pop")))
    return idx


def resolve(candidate: str, state_hint: str, places: dict):
    """Return (canonical_muni, state) or (None, None) if unresolved."""
    matches = places.get(candidate.lower(), [])
    if not matches:
        return None, None
    if len(matches) == 1:
        return candidate.title(), matches[0][0]
    # Disambiguate by state hint
    if state_hint:
        for st, _ in matches:
            if st == state_hint:
                return candidate.title(), st
    # Otherwise pick the largest by population (None populations sort last)
    matches.sort(key=lambda m: -(m[1] or 0))
    return candidate.title(), matches[0][0]


# ---- Public entry point --------------------------------------------------

def harvest(sleep_between: float = 1.5, names_data_path: str = None) -> list:
    """Pull all vendors. Returns list of customer dicts."""
    places = load_places(names_data_path)
    out = []
    for vendor, domains in VENDOR_DOMAINS.items():
        for d in domains:
            try:
                print(f"  crt.sh: fetching {d} ...", end="", flush=True)
                certs = fetch_certs(d)
                print(f" {len(certs)} CT records")
            except Exception as e:
                print(f"  ERROR: {e}")
                time.sleep(sleep_between)
                continue
            subs = extract_subdomains(certs, d)
            for sub in subs:
                cand, hint = extract_muni_candidate(sub)
                if not cand:
                    continue
                muni, state = resolve(cand, hint, places)
                if not muni or not state:
                    # Still emit unresolved candidates with low confidence
                    out.append({
                        "vendor": vendor, "muni": cand, "state": hint,
                        "type": None, "bucket": None, "product": None,
                        "since": None,
                        "source": "crt.sh",
                        "evidence": f"{sub}.{d}",
                        "confidence": 0.3,
                    })
                    continue
                out.append({
                    "vendor": vendor, "muni": muni, "state": state,
                    "type": "muni", "bucket": None, "product": None,
                    "since": None,
                    "source": "crt.sh",
                    "evidence": f"{sub}.{d}",
                    "confidence": 0.85,
                })
            time.sleep(sleep_between)  # rate limit
    return out


if __name__ == "__main__":
    import csv
    import sys
    rows = harvest()
    print(f"\nharvested {len(rows)} candidate customers")
    high_conf = [r for r in rows if r["confidence"] >= 0.7]
    print(f"  high-confidence (resolved to a US place): {len(high_conf)}")
    by_v = {}
    for r in high_conf:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"    {v:25s} {n:>5}")

    if "--csv" in sys.argv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
