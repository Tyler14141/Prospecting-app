"""
DNS fingerprint connector — actively probe muni website patterns to detect
known vendor stacks.

How it works
------------
For each muni in names_data.json, probe a small set of vendor-specific URL
patterns. If the page resolves and matches the vendor's tell, record a hit.

Examples of fingerprints:
  - Tyler Energov:    https://<muni>.tylerciviccess.com/
  - Tyler Munis SS:   https://<muni>.munisselfservice.com/
  - BS&A online:      https://bsaonline.com/?uid=<id>
  - Caselle CIS:      https://caselle.com/cgi-bin/cis.exe?cis=<muni>
  - Muni-Link:        https://<muni>.muni-link.com/

Coverage / limits
-----------------
- High precision when a fingerprint matches.
- Coverage limited by enumeration: we can only test patterns we know.
  Combine with crt.sh (which finds patterns for us) for best results.
- Slow at scale — rate-limit aggressively to avoid getting blocked.

Run
---
    python -m customer_intel.connectors.dns_fingerprint  --max 500

The --max flag caps the total HEAD requests across all munis. Default 500.
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request

from customer_intel import VENDOR_DOMAINS

UA = "Mozilla/5.0 (compatible; customer-intel/0.1)"

# Each fingerprint = (vendor, url_template, content_match_optional)
# Use {slug} placeholder for the muni name slug.
FINGERPRINTS = [
    ("Tyler Technologies",
     "https://{slug}.tylerciviccess.com/",
     re.compile(r"Tyler|Civic\s+Access", re.I)),
    ("Tyler Technologies",
     "https://{slug}.munisselfservice.com/",
     re.compile(r"MUNIS|Tyler", re.I)),
    ("Tyler Technologies",
     "https://{slug}.tylerportico.com/",
     None),
    ("BS&A Software",
     "https://bsaonline.com/?uid={slug}",
     re.compile(r"BS&A|BSA\s+Online", re.I)),
    ("Muni-Link",
     "https://{slug}.muni-link.com/",
     re.compile(r"Muni-?Link", re.I)),
    ("TownCloud",
     "https://{slug}.towncloud.com/",
     re.compile(r"TownCloud", re.I)),
]


def slugify(name: str) -> list:
    """Return common slug variants for a muni name."""
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9 \-]", "", n)
    parts = n.split()
    if not parts:
        return []
    return list({
        "".join(parts),                  # cedarfalls
        "-".join(parts),                 # cedar-falls
        parts[0],                        # cedar  (single-word approximation)
        "cityof" + "".join(parts),       # cityofcedarfalls
        "city-of-" + "-".join(parts),    # city-of-cedar-falls
    })


def probe(url: str, content_match=None, timeout: float = 5.0):
    req = urllib.request.Request(url, headers={"User-Agent": UA},
                                  method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if content_match is None:
                return r.status == 200
            text = r.read(8192).decode("utf-8", errors="replace")
            return content_match.search(text) is not None
    except urllib.error.HTTPError as e:
        return False
    except Exception:
        return False


def harvest(max_probes: int = 500, sleep_between: float = 0.3,
            states: list = None) -> list:
    here = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    names_path = os.path.join(here, "names_data.json")
    if not os.path.exists(names_path):
        print(f"  warning: {names_path} missing — run build_names_data.py")
        return []
    with open(names_path) as f:
        data = json.load(f)
    out = []
    probes = 0
    for st in (states or sorted(data.keys())):
        if probes >= max_probes:
            break
        for c in data[st]["cities"]:
            if probes >= max_probes:
                break
            slugs = slugify(c["name"])
            for vendor, tpl, match in FINGERPRINTS:
                if probes >= max_probes:
                    break
                for slug in slugs:
                    url = tpl.format(slug=slug)
                    probes += 1
                    if probe(url, match):
                        out.append({
                            "vendor": vendor, "muni": c["name"], "state": st,
                            "type": "muni",
                            "bucket": c.get("bucket"), "product": None,
                            "since": None,
                            "source": "dns_fingerprint",
                            "evidence": url,
                            "confidence": 0.95,
                        })
                        break  # one hit per vendor is enough
                    time.sleep(sleep_between)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=500,
                    help="max total probes (default 500)")
    ap.add_argument("--states", nargs="*",
                    help="restrict to states (e.g. --states IA NE)")
    args = ap.parse_args()
    rows = harvest(max_probes=args.max, states=args.states)
    print(f"\n{len(rows)} confirmed installs via DNS fingerprint")
    for r in rows:
        print(f"  {r['vendor']:22s} {r['muni']}, {r['state']}  ({r['evidence']})")
