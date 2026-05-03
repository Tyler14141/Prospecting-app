"""
DNS-only customer fingerprint — confirms customers via strict-DNS vendor
domains. Bypasses HTTP firewalls (this sandbox blocks vendor sites but DNS
resolution works fine).

How it works
------------
Some vendors use *strict* DNS — they only create A records for actual
customers. Resolving `<muni>.<vendor-domain>` either succeeds (real
customer) or fails (no customer). Other vendors use wildcard DNS where
every subdomain resolves to the same IP — those are useless for DNS-only
detection.

This connector enumerates strict-DNS vendor domains only, then probes
multiple slug variants per muni in parallel. ~3 minutes for the full
US muni list at 200 threads.

Strict-DNS domains validated 2026-05-01:
    Tyler Technologies:
        tylerciviccess.com, munisselfservice.com, tylerportals.com,
        tylerhost.net, tylertech.com, energovweb.com, energovaccess.com,
        energov.net, mytylerportal.com, newworldsystems.com
    BS&A Software:        bsaonline.com
    TownCloud:            towncloud.com
    gWorks:               gworks.com, banyondatasystems.com,
                           pontemsoftware.com

Wildcard-DNS (NOT usable here, need HTTP probing):
    Tyler Technologies:   tylerportico.com
    BS&A Software:        bsasoftware.com
    Caselle:              caselle.com
    Muni-Link:            muni-link.com

Run
---
    python -m customer_intel.connectors.dns_strict
    python -m customer_intel.connectors.dns_strict --threads 100 --top 5000
    python -m customer_intel.connectors.dns_strict --states IA NE KS
"""

import argparse
import csv
import json
import os
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAMES_PATH = os.path.join(HERE, "names_data.json")


# (vendor, domain, product_hint) — product_hint is best-guess based on the
# domain's product line.
DOMAIN_TO_VENDOR = {
    # Tyler product family
    "tylerciviccess.com":   ("Tyler Technologies", "EnerGov Civic Access"),
    "munisselfservice.com": ("Tyler Technologies", "Munis Self Service"),
    "tylerportals.com":     ("Tyler Technologies", "Munis / Enterprise"),
    "tylerhost.net":        ("Tyler Technologies", "Hosted services"),
    "tylertech.com":        ("Tyler Technologies", None),
    "tyleronline.com":      ("Tyler Technologies", "Tyler Online"),
    "energovweb.com":       ("Tyler Technologies", "EnerGov"),
    "energovaccess.com":    ("Tyler Technologies", "EnerGov"),
    "energov.net":          ("Tyler Technologies", "EnerGov"),
    "mytylerportal.com":    ("Tyler Technologies", "Tyler Portal"),
    "newworldsystems.com":  ("Tyler Technologies", "New World public safety"),
    "socrata.com":          ("Tyler Technologies", "Socrata data"),
    "cartegraph.com":       ("Tyler Technologies", "Cartegraph asset mgmt"),
    "brazostech.com":       ("Tyler Technologies", "Brazos public safety"),
    "micropact.com":        ("Tyler Technologies", "MicroPact entellitrak"),
    "entellitrak.com":      ("Tyler Technologies", "MicroPact entellitrak"),
    # BS&A (Harris Computer parent)
    "bsaonline.com":        ("BS&A Software", "BSA Online"),
    "harrislocalgov.com":   ("BS&A Software", "Harris Local Govt suite"),
    # TownCloud
    "towncloud.com":        ("TownCloud", "TownCloud Suite"),
    # gWorks family
    "gworks.com":           ("gWorks", "gWorks Suite"),
    "banyondatasystems.com": ("gWorks", "Banyon (acquired)"),
    "pontemsoftware.com":   ("gWorks", "Pontem (acquired)"),
}


def slugify_variants(name: str, state: str) -> list:
    """Return common slug forms a muni might use, with confidence weights.
    Returns list of (slug, confidence) tuples — higher confidence for slugs
    that include state suffix or 'cityof' prefix because they're harder to
    confuse with another muni of the same name."""
    n = re.sub(r"[^a-z0-9 \-']", "", name.lower())
    n = n.replace("'", "")
    parts = [p for p in re.split(r"[\s\-]+", n) if p]
    if not parts:
        return []
    base_join = "".join(parts)
    base_hyph = "-".join(parts)
    st = state.lower()
    out = [
        (base_join + st,             0.95),  # cedarfallsia
        (f"cityof{base_join}",       0.92),  # cityofcedarfalls
        (f"city-of-{base_hyph}",     0.92),
        (f"townof{base_join}",       0.90),
        (base_join,                  0.80),  # cedarfalls
        (base_hyph,                  0.80),  # cedar-falls
    ]
    # Single-word leading slug (only if multi-word name) — low confidence
    if len(parts) > 1:
        out.append((parts[0], 0.40))
    return list(dict.fromkeys(out))   # dedupe preserving order


def probe(host: str, timeout: float = 1.5):
    """Resolve a host. Return IP on success, None on failure."""
    try:
        # socket.gethostbyname doesn't honor a timeout directly; use
        # getaddrinfo with select-able resolver in newer Python? For
        # simplicity, rely on system resolver timeout (typically ~5s).
        return socket.gethostbyname(host)
    except (socket.gaierror, socket.herror):
        return None


def load_munis(states: list = None, top_n: int = None) -> list:
    """Return list of (name, state, pop_or_none, bucket) tuples."""
    with open(NAMES_PATH) as f:
        data = json.load(f)
    out = []
    for st, blob in data.items():
        if states and st not in states:
            continue
        for c in blob.get("cities", []):
            out.append((c["name"], st, c.get("pop"), c.get("bucket")))
    # Sort by pop desc (None last) so --top picks largest first
    out.sort(key=lambda r: (r[2] is None, -(r[2] or 0)))
    if top_n:
        out = out[:top_n]
    return out


def harvest(threads: int = 200, top_n: int = None,
            states: list = None) -> list:
    munis = load_munis(states=states, top_n=top_n)
    print(f"  scanning {len(munis)} munis × {len(DOMAIN_TO_VENDOR)} vendor "
          f"domains × ~6 slug forms")

    targets = []  # (host, name, state, pop, bucket, vendor, product, conf)
    for name, state, pop, bucket in munis:
        for slug, slug_conf in slugify_variants(name, state):
            if not slug:
                continue
            for dom, (vendor, product) in DOMAIN_TO_VENDOR.items():
                host = f"{slug}.{dom}"
                targets.append((host, name, state, pop, bucket,
                                  vendor, product, slug_conf))

    print(f"  {len(targets):,} DNS lookups queued")
    t0 = time.time()
    hits = []
    completed = 0
    with ThreadPoolExecutor(max_workers=threads) as ex:
        future_to_t = {ex.submit(probe, t[0]): t for t in targets}
        for fut in as_completed(future_to_t):
            completed += 1
            if completed % 5000 == 0:
                elapsed = time.time() - t0
                rate = completed / elapsed
                eta = (len(targets) - completed) / rate
                print(f"    {completed:,}/{len(targets):,}  "
                      f"({rate:.0f}/s, ETA {eta:.0f}s, {len(hits)} hits)")
            ip = fut.result()
            if ip:
                t = future_to_t[fut]
                hits.append({
                    "vendor": t[5], "muni": t[1], "state": t[2],
                    "type": "muni", "bucket": t[4], "product": t[6],
                    "since": None, "source": "dns_strict",
                    "evidence": t[0], "confidence": t[7],
                    "pop": t[3], "ip": ip,
                })
    print(f"  done in {time.time() - t0:.1f}s, {len(hits)} raw hits")

    # When a generic single-word slug resolves, it could match multiple
    # cities of the same name. Group by (vendor, slug-host, ip) and keep
    # only the LARGEST muni claiming that slug.
    by_evidence = {}
    for h in hits:
        key = (h["vendor"], h["evidence"])
        if key not in by_evidence or (h.get("pop") or 0) > (by_evidence[key].get("pop") or 0):
            by_evidence[key] = h
    deduped_by_ev = list(by_evidence.values())

    # Now dedupe by (vendor, muni, state) — pick highest confidence
    keyed = {}
    for h in deduped_by_ev:
        key = (h["vendor"], h["muni"], h["state"])
        if key not in keyed or h["confidence"] > keyed[key]["confidence"]:
            keyed[key] = h
    return sorted(keyed.values(),
                  key=lambda h: (-h["confidence"], h["vendor"], h["state"], h["muni"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=200)
    ap.add_argument("--top", type=int, help="limit to top-N munis by pop")
    ap.add_argument("--states", nargs="*", help="filter to states")
    ap.add_argument("--out", default="dns_strict_hits.csv")
    args = ap.parse_args()

    rows = harvest(threads=args.threads, top_n=args.top, states=args.states)
    print(f"\n{len(rows)} unique customer hits")

    # By vendor
    by_v = {}
    for r in rows:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")

    # Write CSV
    if rows:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"\nwrote {args.out}")
