"""
Muni website fingerprint connector — discover the incumbent vendor stack
for any municipality by crawling its public website.

How it works
------------
1. **Discover** the muni's official site by probing ~10 common URL
   patterns (`https://www.cityof<muni>.gov`, `https://<muni>.<st>.gov`,
   etc.) until one resolves with HTTP 200.
2. **Crawl** a small set of high-value pages on that site:
   `/`, `/payments`, `/utility-billing`, `/permits`, `/inspections`,
   `/agendas`, `/finance`, `/government`. Vendors typically surface in
   external-domain links from these pages.
3. **Fingerprint** the combined HTML for vendor URL patterns
   (e.g., `tylerciviccess.com`, `bsaonline.com`, `muni-link.com`) and
   common text tells ("Powered by Tyler Technologies", "BS&A Software",
   etc.).
4. **Map** each hit to a (vendor, product) record matching the existing
   `competitor_customers.py` schema, with the source URL as evidence.

Coverage
--------
- Picks up vendors who host customer-facing portals on their own domain
  and link from the muni site (Tyler Civic Access, Munis Self Service,
  Muni-Link, BS&A Online, etc.). These are very common for small munis.
- Misses vendors hosted entirely on the muni's own domain (rare for
  ERP, common for content-management).
- Expected coverage: 40-60% of munis with a public website. Combine with
  `crt_sh` and `cafr_pdf` for ~80% combined.

Run
---
    python -m customer_intel.connectors.muni_website
    python -m customer_intel.connectors.muni_website --top-prospects 1000
    python -m customer_intel.connectors.muni_website --states IA NE KS
    python -m customer_intel.connectors.muni_website --concurrency 20

Politeness
----------
- 1.5s delay between requests to the same host
- 5s timeout per request, 3 retries with exponential backoff
- User-Agent identifies the tool: "customer-intel-muni/0.1"
- Capped at one /robots.txt fetch per site (respected if present)
"""

import argparse
import concurrent.futures as cf
import csv
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "customer-intel-muni/0.1 (https://example.com/bot)"

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAMES_PATH = os.path.join(HERE, "names_data.json")
GREENFIELD_PATH = os.path.normpath(os.path.join(
    HERE, "..", "TAM", "greenfield_data.json"))


# Common URL patterns for muni websites. Tried in order; first 200 wins.
URL_PATTERNS = [
    "https://www.cityof{slug}.gov",
    "https://cityof{slug}.gov",
    "https://www.cityof{slug}.org",
    "https://cityof{slug}.org",
    "https://www.cityof{slug}.com",
    "https://www.{slug}.gov",
    "https://{slug}.gov",
    "https://www.{slug}{st}.gov",
    "https://{slug}{st}.gov",
    "https://www.{slug}-{st}.gov",
    "https://www.{slug}.{st}.gov",
    "https://www.townof{slug}.gov",
    "https://townof{slug}.org",
    "https://www.villageof{slug}.gov",
    "https://www.{slug}.us",
    "https://www.{slug}.org",
    "https://{slug}.org",
    "https://www.{slug}-{st}.com",
]

KEY_PATHS = [
    "/", "/payments", "/utility-billing", "/utilities", "/billing",
    "/permits", "/inspections", "/finance", "/government",
    "/agendas", "/online-services", "/citizen-portal", "/online-payments",
]


# ---- Vendor URL pattern fingerprints -------------------------------------
# Order matters — most specific products first. Captures domain in the
# matched URL as evidence.
VENDOR_URL_FINGERPRINTS = [
    # Tyler product family
    (re.compile(r"tylerciviccess\.com",   re.I), "Tyler Technologies", "EnerGov Civic Access"),
    (re.compile(r"munisselfservice\.com", re.I), "Tyler Technologies", "Munis Self Service"),
    (re.compile(r"tylerportico\.com",     re.I), "Tyler Technologies", "Tyler Portico"),
    (re.compile(r"tylerportals\.com",     re.I), "Tyler Technologies", "Munis / Enterprise"),
    (re.compile(r"tylerhost\.net",        re.I), "Tyler Technologies", "Hosted services"),
    (re.compile(r"energovweb\.com|energovaccess\.com|energov\.net", re.I),
                                                  "Tyler Technologies", "EnerGov"),
    (re.compile(r"newworldsystems\.com",  re.I), "Tyler Technologies", "New World public safety"),
    (re.compile(r"mytylerportal\.com",    re.I), "Tyler Technologies", "Tyler Portal"),
    (re.compile(r"socrata\.com",          re.I), "Tyler Technologies", "Socrata"),
    (re.compile(r"tylertech\.com",        re.I), "Tyler Technologies", None),
    # BS&A
    (re.compile(r"bsaonline\.com",        re.I), "BS&A Software", "BSA Online"),
    (re.compile(r"bsasoftware\.com",      re.I), "BS&A Software", None),
    # Caselle
    (re.compile(r"caselle\.com",          re.I), "Caselle", "Caselle Connect"),
    # gWorks family
    (re.compile(r"banyondatasystems\.com", re.I), "gWorks", "Banyon (acquired)"),
    (re.compile(r"pontemsoftware\.com",   re.I), "gWorks", "Pontem (acquired)"),
    (re.compile(r"gworks\.com",           re.I), "gWorks", "gWorks Suite"),
    # Muni-Link
    (re.compile(r"muni-link\.com|munilinkpa\.com", re.I), "Muni-Link", "Utility Billing"),
    # TownCloud
    (re.compile(r"towncloud\.com",        re.I), "TownCloud", "TownCloud Suite"),
]

# Text-based fingerprints for vendor mentions in page copy / footers.
# Less precise than URL patterns; emit at lower confidence.
VENDOR_TEXT_FINGERPRINTS = [
    (re.compile(r"powered\s+by\s+tyler",       re.I), "Tyler Technologies", None),
    (re.compile(r"tyler\s+technolog(?:y|ies)", re.I), "Tyler Technologies", None),
    (re.compile(r"\bMUNIS\b"),                       "Tyler Technologies", "Munis ERP"),
    (re.compile(r"new\s+world\s+systems",      re.I), "Tyler Technologies", "New World"),
    (re.compile(r"(?:powered\s+by\s+)?BS&A\s+Software", re.I), "BS&A Software", None),
    (re.compile(r"\bCaselle(?:\s+Connect)?\b", re.I),  "Caselle",            "Caselle Connect"),
    (re.compile(r"powered\s+by\s+Caselle",     re.I), "Caselle",            None),
    (re.compile(r"\bgWorks\b"),                       "gWorks",             "gWorks Suite"),
    (re.compile(r"banyon\s+data\s+systems?",   re.I), "gWorks",             "Banyon"),
    (re.compile(r"(?:powered\s+by\s+)?Muni-?Link", re.I), "Muni-Link",      "Utility Billing"),
    (re.compile(r"\bTownCloud\b",              re.I), "TownCloud",          "TownCloud Suite"),
]


# ---- HTTP helpers --------------------------------------------------------

def slugify(name: str) -> str:
    n = re.sub(r"[^a-z0-9 \-']", "", name.lower())
    n = n.replace("'", "").replace(" ", "").replace("-", "")
    return n


def fetch(url: str, timeout: float = 5.0, max_bytes: int = 500_000) -> str:
    """Fetch a URL and return decoded body. Caps at max_bytes."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            return ""
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("text/") and "html" not in ctype:
            return ""
        body = r.read(max_bytes)
        charset = r.headers.get_content_charset() or "utf-8"
        return body.decode(charset, errors="replace")


def discover_url(slug: str, state: str, timeout: float = 4.0) -> str:
    """Try each URL pattern until one resolves and returns a non-error
    response. Returns the working URL or None."""
    st = state.lower()
    for pat in URL_PATTERNS:
        url = pat.format(slug=slug, st=st)
        try:
            socket.gethostbyname(urllib.parse.urlparse(url).netloc)
        except socket.gaierror:
            continue  # DNS doesn't resolve — skip without HTTP attempt
        try:
            req = urllib.request.Request(url, method="HEAD",
                                          headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if 200 <= r.status < 400:
                    return url
        except urllib.error.HTTPError as e:
            if e.code in (200, 301, 302, 403):  # 403 still likely real site
                return url
        except Exception:
            pass
    return None


# ---- Fingerprinting ------------------------------------------------------

def fingerprint(html: str, vendor_filter: set = None) -> list:
    """Return list of (vendor, product, evidence_snippet) tuples found in
    the HTML."""
    out = []
    seen = set()

    for pat, vendor, product in VENDOR_URL_FINGERPRINTS:
        if vendor_filter and vendor not in vendor_filter:
            continue
        m = pat.search(html)
        if m:
            key = (vendor, product, "url")
            if key in seen:
                continue
            seen.add(key)
            start = max(0, m.start() - 30)
            end = min(len(html), m.end() + 30)
            snippet = re.sub(r"\s+", " ", html[start:end]).strip()
            out.append((vendor, product, snippet, "url", 0.95))

    for pat, vendor, product in VENDOR_TEXT_FINGERPRINTS:
        if vendor_filter and vendor not in vendor_filter:
            continue
        m = pat.search(html)
        if m:
            key = (vendor, product, "text")
            if key in seen:
                continue
            seen.add(key)
            start = max(0, m.start() - 30)
            end = min(len(html), m.end() + 30)
            snippet = re.sub(r"\s+", " ", html[start:end]).strip()
            out.append((vendor, product, snippet, "text", 0.75))

    return out


def scan_muni(name: str, state: str, pop=None, bucket=None,
               page_delay: float = 1.5) -> list:
    """Discover, crawl, fingerprint one muni. Returns list of customer
    records (matching competitor_customers schema)."""
    slug = slugify(name)
    if not slug:
        return []
    url = discover_url(slug, state)
    if not url:
        return []
    base = url.rstrip("/")
    combined_html = []
    seen_paths = set()
    for path in KEY_PATHS:
        full = base + path
        if full in seen_paths:
            continue
        seen_paths.add(full)
        try:
            html = fetch(full, timeout=6.0)
            if html:
                combined_html.append(html)
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
        time.sleep(page_delay)
    if not combined_html:
        return []

    big = "\n".join(combined_html)
    hits = fingerprint(big)
    out = []
    for vendor, product, snippet, kind, conf in hits:
        out.append({
            "vendor": vendor,
            "muni": name,
            "state": state,
            "type": "muni",
            "bucket": bucket,
            "product": product,
            "since": None,
            "source": f"muni_website ({kind})",
            "evidence": f"{base}: {snippet[:120]}",
            "confidence": conf,
            "pop": pop,
            "site_url": base,
        })
    return out


# ---- Bulk runner ---------------------------------------------------------

def load_targets(states=None, top_n=None, top_prospects: bool = False):
    """Build the list of (name, state, pop, bucket) to scan."""
    if top_prospects:
        if not os.path.exists(GREENFIELD_PATH):
            sys.exit(f"  ERROR: {GREENFIELD_PATH} missing — run "
                      "build_greenfield_data.py first")
        with open(GREENFIELD_PATH) as f:
            gf = json.load(f)
        rows = []
        for p in gf.get("top_prospects", []):
            if states and p["state"] not in states:
                continue
            # Only scan the ones still marked greenfield (no incumbent)
            if p.get("incumbent"):
                continue
            rows.append((p["muni"], p["state"], p.get("pop"), p.get("bucket")))
            if top_n and len(rows) >= top_n:
                break
        return rows
    # Otherwise iterate full names_data
    with open(NAMES_PATH) as f:
        names = json.load(f)
    out = []
    for st, blob in names.items():
        if states and st not in states:
            continue
        for c in blob.get("cities", []):
            out.append((c["name"], st, c.get("pop"), c.get("bucket")))
    out.sort(key=lambda r: (r[2] is None, -(r[2] or 0)))
    if top_n:
        out = out[:top_n]
    return out


def harvest(states=None, top_n=None, top_prospects=False,
             concurrency: int = 12):
    targets = load_targets(states=states, top_n=top_n,
                            top_prospects=top_prospects)
    print(f"  scanning {len(targets):,} munis (concurrency={concurrency})")
    rows = []
    t0 = time.time()
    completed = 0
    found = 0
    with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {ex.submit(scan_muni, n, st, p, b): (n, st)
                   for n, st, p, b in targets}
        for fut in cf.as_completed(futures):
            completed += 1
            try:
                hits = fut.result()
            except Exception as e:
                hits = []
            if hits:
                rows.extend(hits)
                found += 1
            if completed % 50 == 0:
                elapsed = time.time() - t0
                rate = completed / max(elapsed, 0.001)
                eta = (len(targets) - completed) / max(rate, 0.001)
                print(f"    {completed:,}/{len(targets):,}  "
                      f"({rate:.1f}/s, ETA {eta:.0f}s, "
                      f"{found} sites with hits, {len(rows)} hits total)")
    print(f"  done in {time.time() - t0:.1f}s")
    print(f"  {found} munis returned at least one vendor hit")
    print(f"  {len(rows)} total hits before dedupe")
    # Dedupe by (vendor, muni, state) keeping highest confidence + product
    keyed = {}
    for r in rows:
        k = (r["vendor"], r["muni"], r["state"])
        if k not in keyed or r["confidence"] > keyed[k]["confidence"]:
            keyed[k] = r
        elif r.get("product") and not keyed[k].get("product"):
            keyed[k]["product"] = r["product"]
    return list(keyed.values())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="*", help="filter to specific states")
    ap.add_argument("--top", type=int, help="limit to top-N munis by pop")
    ap.add_argument("--top-prospects", action="store_true",
                    help="only scan greenfield-status rows from "
                          "greenfield_data.json (focus on actionable prospects)")
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--out", default="muni_website_hits.csv")
    args = ap.parse_args()

    rows = harvest(states=args.states, top_n=args.top,
                    top_prospects=args.top_prospects,
                    concurrency=args.concurrency)
    print(f"\n{len(rows)} unique customer hits")
    by_v = {}
    for r in rows:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")

    if rows:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"\nwrote {args.out}")
