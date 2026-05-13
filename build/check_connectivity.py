"""
check_connectivity.py — verify this environment can run full_state_dive.py.

Probes:
  1. Python deps (beautifulsoup4, pdfplumber)
  2. DNS resolution for known muni hosts
  3. HTTP fetch of a small sample of muni .gov / .org sites
  4. /agendas index walk + PDF download from one site that has minutes
  5. Confirms the harvest pipeline can land at least one verbatim PDF

Run before kicking off the full state dive:

    cd build
    python3 check_connectivity.py
    # if all green, then:
    python3 full_state_dive.py --states NY PA ME OH

Exits 0 if ready, 1 if blockers found.
"""

import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


UA = "customer-intel-checkup/0.1"
RESULTS = {"pass": 0, "fail": 0, "warn": 0}


def _print(status, msg, indent=0):
    pad = "  " * indent
    icons = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "INFO": "•"}
    color = {
        "PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m",
        "INFO": "\033[36m", "END": "\033[0m"
    }
    print(f"{pad}{color[status]}{icons[status]}{color['END']} {msg}")
    if status == "PASS": RESULTS["pass"] += 1
    elif status == "FAIL": RESULTS["fail"] += 1
    elif status == "WARN": RESULTS["warn"] += 1


def section(title):
    print(f"\n\033[1m{title}\033[0m")
    print("─" * 64)


# ---- 1. Python deps -----------------------------------------------------
def check_deps():
    section("1. Python dependencies")
    try:
        import bs4  # noqa
        _print("PASS", "beautifulsoup4 installed")
    except ImportError:
        _print("FAIL", "beautifulsoup4 missing — run `pip install beautifulsoup4`")
    try:
        import pdfplumber  # noqa
        _print("PASS", "pdfplumber installed")
    except ImportError:
        _print("WARN", "pdfplumber missing — install for best PDF extraction "
               "(`pip install pdfplumber`); falls back to pypdf or pdftotext")
    try:
        from pypdf import PdfReader  # noqa
        _print("PASS", "pypdf installed (PDF fallback)")
    except ImportError:
        try:
            import subprocess
            r = subprocess.run(["pdftotext", "-v"], capture_output=True, timeout=5)
            _print("PASS", "pdftotext available (PDF fallback)")
        except Exception:
            _print("WARN", "No PDF fallback found — install pdfplumber or pypdf")


# ---- 2. DNS resolution --------------------------------------------------
def check_dns():
    section("2. DNS resolution")
    test_hosts = [
        "raw.githubusercontent.com",   # for the lutangar mirror
        "www.belfastmaine.org",        # sample ME town
        "www.cooperstownny.gov",       # sample NY village
        "www.bryanohio.com",           # sample OH city
        "www.lewistownpa.gov",         # sample PA borough
    ]
    failed = 0
    for h in test_hosts:
        try:
            socket.gethostbyname(h)
            _print("PASS", f"resolves: {h}", indent=1)
        except socket.gaierror:
            _print("WARN", f"no DNS record: {h} (host may not exist; try alt slug)", indent=1)
            failed += 1
    if failed == len(test_hosts):
        _print("FAIL", "DNS resolution failed for every host — environment is "
               "offline or DNS broken", indent=0)


# ---- 3. HTTP fetch of muni sites ----------------------------------------
SAMPLE_MUNI_URLS = [
    # Known-good URLs for sub-15K munis across the 4 target states
    ("ME", "Belfast",    "https://www.cityofbelfast.org/"),
    ("ME", "Bath",       "https://www.cityofbath.com/"),
    ("ME", "Camden",     "https://www.camdenmaine.gov/"),
    ("NY", "Cooperstown","https://www.cooperstownny.org/"),
    ("NY", "Geneva",     "https://www.genevany.gov/"),
    ("PA", "Lewistown",  "https://www.lewistownpa.org/"),
    ("PA", "Bellefonte", "https://www.bellefontepa.gov/"),
    ("OH", "Wapakoneta", "https://www.wapakoneta.net/"),
    ("OH", "Bryan",      "https://www.bryanohio.gov/"),
]

def check_http():
    section("3. HTTP fetch of sample muni websites")
    ok = 0
    for st, name, url in SAMPLE_MUNI_URLS:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                size = len(r.read(50_000))
                _print("PASS", f"{name}, {st}: HTTP {r.status} ({size} bytes)",
                       indent=1)
                ok += 1
        except urllib.error.HTTPError as e:
            if e.code == 403:
                _print("FAIL", f"{name}, {st}: HTTP 403 (firewalled or rejecting bot UA)",
                       indent=1)
            elif e.code == 404:
                _print("WARN", f"{name}, {st}: HTTP 404 (URL changed; scraper "
                       "will fall back to other patterns)", indent=1)
            else:
                _print("WARN", f"{name}, {st}: HTTP {e.code}", indent=1)
        except urllib.error.URLError as e:
            _print("FAIL", f"{name}, {st}: {e.reason}", indent=1)
        except socket.timeout:
            _print("WARN", f"{name}, {st}: timeout (slow site)", indent=1)
        except Exception as e:
            _print("FAIL", f"{name}, {st}: {type(e).__name__}: {e}", indent=1)
    if ok == 0:
        _print("FAIL", "All sample sites unreachable — environment is firewalled "
               "OR network is down. full_state_dive.py will not work.", indent=0)
    elif ok < 3:
        _print("WARN", "Most sites unreachable. Connector will still try, but "
               "expect a low hit rate.", indent=0)
    return ok


# ---- 4. PDF download via /agendas walk ----------------------------------
def check_pdf_download():
    section("4. PDF download from /agendas (full pipeline)")
    # Try several muni sites known to host agendas/PDFs; stop at first success.
    from customer_intel.connectors.meeting_minutes import (
        find_meeting_pdfs, fetch_bytes, extract_pdf_text, discover_url, slugify
    )
    test_munis = [
        ("Belfast",    "ME"),
        ("Cooperstown","NY"),
        ("Camden",     "ME"),
        ("Bath",       "ME"),
        ("Bryan",      "OH"),
    ]
    for name, state in test_munis:
        slug = slugify(name)
        base = discover_url(slug, state)
        if not base:
            _print("WARN", f"{name}, {state}: site URL discovery failed (no "
                   "matching pattern)", indent=1)
            continue
        _print("INFO", f"{name}, {state}: discovered {base}", indent=1)
        try:
            pdfs = find_meeting_pdfs(base, max_pdfs=3)
        except Exception as e:
            _print("WARN", f"  agendas walk failed: {e}", indent=1)
            continue
        if not pdfs:
            _print("INFO", "  no PDF links found on agendas page", indent=1)
            continue
        _print("PASS", f"  {len(pdfs)} PDF link(s) found", indent=1)
        # Download the first PDF and try to extract text
        try:
            blob = fetch_bytes(pdfs[0], timeout=12)
            if not blob:
                _print("WARN", "  PDF download returned empty body", indent=1)
                continue
            _print("PASS", f"  downloaded {pdfs[0]} ({len(blob)} bytes)",
                   indent=1)
            try:
                text = extract_pdf_text(blob)
                if text and len(text) > 100:
                    _print("PASS", f"  PDF text extracted ({len(text)} chars) "
                           "— end-to-end pipeline works", indent=1)
                    return True
                _print("WARN", "  PDF extracted 0 chars (encrypted? scanned image?)",
                       indent=1)
            except Exception as e:
                _print("FAIL", f"  PDF text extraction failed: {e}", indent=1)
        except Exception as e:
            _print("WARN", f"  PDF download failed: {e}", indent=1)
    _print("FAIL", "Could not complete end-to-end PDF probe — full_state_dive "
           "may produce zero hits", indent=0)
    return False


# ---- 5. Names data presence ---------------------------------------------
def check_names_data():
    section("5. Names data (muni list for the dive)")
    import os
    import json
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "names_data.json")
    if not os.path.exists(p):
        _print("FAIL", "names_data.json missing — run build_names_data.py first")
        return
    with open(p) as f:
        d = json.load(f)
    total = sum(len(v.get("cities", [])) for v in d.values())
    sub15 = sum(1 for v in d.values() for c in v.get("cities", [])
                if c.get("pop") is None or (c.get("pop") or 0) < 15000)
    states_in_focus = ("NY", "PA", "ME", "OH")
    focus = sum(len(d.get(s, {}).get("cities", [])) for s in states_in_focus)
    _print("PASS", f"names_data.json present: {total:,} munis total, "
           f"{sub15:,} sub-15K")
    _print("INFO", f"NY/PA/ME/OH muni count: {focus:,} (this is the dive target)")


# ---- Main ---------------------------------------------------------------
def main():
    print("\033[1m╔════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1m║  Connectivity check for full_state_dive.py                 ║\033[0m")
    print("\033[1m╚════════════════════════════════════════════════════════════╝\033[0m")

    t0 = time.time()
    check_deps()
    check_dns()
    n_http_ok = check_http()
    check_names_data()
    pdf_ok = False
    if n_http_ok > 0:
        pdf_ok = check_pdf_download()
    else:
        section("4. PDF download — SKIPPED (no muni sites reachable)")

    section("Summary")
    print(f"  Pass: {RESULTS['pass']}    Warn: {RESULTS['warn']}    "
          f"Fail: {RESULTS['fail']}    ({time.time() - t0:.1f}s)")

    if RESULTS["fail"] == 0 and n_http_ok >= 3 and pdf_ok:
        print("\n\033[32m\033[1m✓ Environment is READY.\033[0m  Run:")
        print("    python3 full_state_dive.py --states NY PA ME OH\n")
        return 0
    elif n_http_ok > 0:
        print("\n\033[33m\033[1m⚠ Partial connectivity.\033[0m  full_state_dive will run "
              "but produce a lower hit rate than expected.")
        print("  Try a smaller test run first:")
        print("    python3 full_state_dive.py --states ME --max-per-state 25 --max-pdfs 5\n")
        return 0
    else:
        print("\n\033[31m\033[1m✗ Environment is NOT ready.\033[0m  Muni websites are "
              "unreachable from here.")
        print("  Likely cause: firewall, restricted sandbox, or offline.")
        print("  Run this script from a normal-internet machine (your laptop or "
              "an unrestricted Codespace).")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
