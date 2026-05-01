"""
Vendor case-study / customer-list scraper.

Most vendor websites have a public "Our Customers" or "Case Studies" page
that names individual cities and counties. This connector pulls each
configured page, extracts text, and runs a place-name extractor against a
cached US places list (from names_data.json).

Coverage / limits
-----------------
- Lower coverage than crt.sh — vendors only publish reference customers,
  not their full installed base.
- Higher precision when the page lists customers by name. Pages that only
  show logos require OCR or alt-text scraping.
- Vendor sites change layouts. If a connector breaks, update the selector
  in CASE_STUDY_SOURCES below.

Run
---
    python -m customer_intel.connectors.case_studies
"""

import json
import os
import re
import time
import urllib.request

from customer_intel import VENDOR_CASE_STUDY_URLS

try:
    from bs4 import BeautifulSoup
    HAVE_BS4 = True
except ImportError:
    HAVE_BS4 = False


# Regex matches "City of <Name>", "<Name> County", "Town of <Name>",
# "<Name>, <ST>" — picks up most muni references in case-study text.
PLACE_PATTERNS = [
    re.compile(r"\bCity of ([A-Z][A-Za-z\.\-' ]{2,40}?)(?=[,\.\;\n\(]|$)"),
    re.compile(r"\bTown of ([A-Z][A-Za-z\.\-' ]{2,40}?)(?=[,\.\;\n\(]|$)"),
    re.compile(r"\bVillage of ([A-Z][A-Za-z\.\-' ]{2,40}?)(?=[,\.\;\n\(]|$)"),
    re.compile(r"\bBorough of ([A-Z][A-Za-z\.\-' ]{2,40}?)(?=[,\.\;\n\(]|$)"),
    re.compile(r"\bCounty of ([A-Z][A-Za-z\.\-' ]{2,40}?)(?=[,\.\;\n\(]|$)"),
    re.compile(r"\b([A-Z][A-Za-z\.\-' ]{2,40}?) County\b"),
    re.compile(r"\b([A-Z][a-zA-Z\.\-' ]{2,40}),\s*([A-Z]{2})\b"),
]

UA = "Mozilla/5.0 (compatible; customer-intel/0.1)"


def fetch(url: str, retries: int = 3, backoff: float = 2.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                charset = r.headers.get_content_charset() or "utf-8"
                return r.read().decode(charset, errors="replace")
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(f"fetch {url} failed: {last_err}")


def text_from_html(html: str) -> str:
    if HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(" ")
    # Fallback regex stripper
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def extract_alts(html: str) -> list:
    """Pull alt text from <img> tags — many vendor pages use logos with
    informative alt='City of Springfield' style text."""
    out = []
    if HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            alt = (img.get("alt") or "").strip()
            if len(alt) > 3:
                out.append(alt)
    else:
        for m in re.finditer(r'<img[^>]+alt="([^"]+)"', html, re.I):
            out.append(m.group(1).strip())
    return out


def find_places(text: str, places: dict):
    """Yield (muni_canonical, state) pairs found in *text*."""
    seen = set()
    for pat in PLACE_PATTERNS:
        for m in pat.finditer(text):
            groups = m.groups()
            name = groups[0].strip().rstrip(".,;:")
            if not name or len(name) > 40:
                continue
            state_hint = groups[1] if len(groups) > 1 and len(groups[1]) == 2 else None
            matches = places.get(name.lower(), [])
            if not matches:
                # Try without trailing period
                matches = places.get(name.lower().rstrip("."), [])
            if not matches:
                continue
            if state_hint:
                for st, _ in matches:
                    if st == state_hint:
                        key = (name, st)
                        if key not in seen:
                            seen.add(key)
                            yield name, st
                        break
                else:
                    # state hint didn't match — fall through to largest
                    pass
            # No / no-match state hint — use largest
            matches_sorted = sorted(matches, key=lambda m: -(m[1] or 0))
            st = matches_sorted[0][0]
            key = (name, st)
            if key not in seen:
                seen.add(key)
                yield name, st


def harvest(names_data_path: str = None) -> list:
    if names_data_path is None:
        here = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        names_data_path = os.path.join(here, "names_data.json")
    if not os.path.exists(names_data_path):
        print(f"  warning: {names_data_path} missing — run build_names_data.py first")
        return []
    with open(names_data_path) as f:
        data = json.load(f)
    places = {}
    for st, blob in data.items():
        for c in blob.get("cities", []):
            places.setdefault(c["name"].lower(), []).append((st, c.get("pop")))

    out = []
    for vendor, urls in VENDOR_CASE_STUDY_URLS.items():
        for url in urls:
            try:
                print(f"  case_studies: {url} ...", end="", flush=True)
                html = fetch(url)
                print(f" {len(html)} bytes")
            except Exception as e:
                print(f"  ERROR: {e}")
                continue
            text = text_from_html(html)
            alts = extract_alts(html)
            full = text + "\n" + "\n".join(alts)
            for name, st in find_places(full, places):
                out.append({
                    "vendor": vendor, "muni": name, "state": st,
                    "type": "muni", "bucket": None, "product": None,
                    "since": None,
                    "source": "case_study",
                    "evidence": url,
                    "confidence": 0.9,
                })
            time.sleep(1.0)
    # Dedupe
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
    print(f"\nharvested {len(rows)} customers from case-study pages")
    by_v = {}
    for r in rows:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")
