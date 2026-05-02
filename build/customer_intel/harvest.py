"""
Run all customer-intel connectors, merge results, dedupe, write CSV.

Usage
-----
    cd build
    python -m customer_intel.harvest               # runs free connectors
    python -m customer_intel.harvest --skip jobs   # skip a connector
    python -m customer_intel.harvest --only crt_sh
    python -m customer_intel.harvest --cafr-dir /path/to/pdfs
    python -m customer_intel.harvest --max-probes 1000

Outputs
-------
    customer_intel_raw.csv     — all raw finds (one row per source mention)
    customer_intel_merged.csv  — deduped (one row per vendor+muni+state)
"""

import argparse
import csv
import os
import sys

from customer_intel.connectors import (case_studies, crt_sh, dns_fingerprint,
                                         dns_strict, job_postings,
                                         meeting_minutes, muni_website)


CONNECTORS = {
    "crt_sh": ("Certificate Transparency log search",
                lambda args: crt_sh.harvest()),
    "case_studies": ("Vendor case-study page scraper",
                      lambda args: case_studies.harvest()),
    "dns_fingerprint": ("DNS / URL pattern fingerprint",
                         lambda args: dns_fingerprint.harvest(
                             max_probes=args.max_probes)),
    "dns_strict": ("Strict-DNS vendor subdomain probe",
                    lambda args: dns_strict.harvest(
                        threads=args.dns_threads,
                        top_n=args.dns_top,
                        states=args.states)),
    "job_postings": ("Public job-board scraper (Indeed)",
                      lambda args: job_postings.harvest()),
    "muni_website": ("Muni website fingerprint (high-leverage for filling in incumbents)",
                      lambda args: muni_website.harvest(
                          states=args.states,
                          top_n=args.muni_top,
                          top_prospects=args.muni_top_prospects,
                          concurrency=args.muni_concurrency)),
    "meeting_minutes": ("Council/board meeting-minute PDF extraction (highest precision)",
                         lambda args: _run_meeting_minutes(args)),
}


def _run_meeting_minutes(args):
    """meeting_minutes returns (customers, signals); customers go to the
    raw CSV, signals are saved separately for review (not auto-merged
    because they need a richer schema than the harvest CSV)."""
    customers, sigs = meeting_minutes.harvest(
        states=args.states,
        top_n=args.minutes_top,
        top_prospects=args.minutes_top_prospects,
        threads=args.minutes_threads,
        max_pdfs=args.minutes_max_pdfs,
    )
    if sigs:
        import csv as _csv
        out_sigs = "meeting_minutes_signals.csv"
        with open(out_sigs, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=list(sigs[0].keys()),
                                  extrasaction="ignore")
            w.writeheader()
            for s in sigs:
                w.writerow(s)
        print(f"  meeting_minutes: {len(sigs)} buying signals saved to {out_sigs}")
    return customers

# CAFR PDF connector is opt-in (needs a PDF directory)
def _run_cafr(args):
    if not args.cafr_dir:
        return []
    from customer_intel.connectors import cafr_pdf
    return cafr_pdf.harvest(args.cafr_dir)


CONNECTORS["cafr_pdf"] = ("CAFR / ACFR PDF vendor mention extraction",
                           _run_cafr)


FIELDS = ["vendor", "muni", "state", "type", "bucket", "product",
           "since", "source", "evidence", "confidence"]


def merge_rows(rows: list) -> list:
    """Dedupe by (vendor, muni, state). Higher-confidence row wins.
    Concatenates `source` fields when multiple sources confirm same install."""
    bucket = {}
    for r in rows:
        key = (r["vendor"], (r.get("muni") or "").lower(),
                r.get("state") or "")
        existing = bucket.get(key)
        if existing is None:
            bucket[key] = dict(r)
            bucket[key]["sources"] = {r["source"]}
            continue
        existing["sources"].add(r["source"])
        # Higher confidence wins for non-null fields
        if r["confidence"] > existing["confidence"]:
            for k in ("type", "bucket", "product", "since", "evidence"):
                if r.get(k):
                    existing[k] = r[k]
            existing["confidence"] = r["confidence"]
    out = []
    for v in bucket.values():
        v["source"] = ",".join(sorted(v.pop("sources")))
        out.append(v)
    out.sort(key=lambda r: (-r["confidence"], r["vendor"], r["state"] or "",
                             r["muni"]))
    return out


def write_csv(path: str, rows: list, fields: list = FIELDS):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*",
                    help="run only these connectors (default: all free)")
    ap.add_argument("--skip", nargs="*", default=[],
                    help="skip these connectors")
    ap.add_argument("--states", nargs="*",
                    help="filter to specific states (used by dns_strict, "
                          "muni_website, meeting_minutes)")
    ap.add_argument("--max-probes", type=int, default=500,
                    help="DNS-fingerprint connector max probes")
    ap.add_argument("--dns-threads", type=int, default=200,
                    help="dns_strict thread count")
    ap.add_argument("--dns-top", type=int, default=None,
                    help="dns_strict: limit to top-N munis")
    ap.add_argument("--muni-top", type=int, default=None,
                    help="muni_website: limit to top-N munis")
    ap.add_argument("--muni-top-prospects", action="store_true",
                    help="muni_website: only scan greenfield prospects")
    ap.add_argument("--muni-concurrency", type=int, default=12,
                    help="muni_website concurrent connections (be polite)")
    ap.add_argument("--minutes-top", type=int, default=None,
                    help="meeting_minutes: limit to top-N munis")
    ap.add_argument("--minutes-top-prospects", action="store_true",
                    help="meeting_minutes: scan greenfield prospects only")
    ap.add_argument("--minutes-threads", type=int, default=10,
                    help="meeting_minutes thread count (slow per muni)")
    ap.add_argument("--minutes-max-pdfs", type=int, default=12,
                    help="meeting_minutes: max PDFs to download per muni")
    ap.add_argument("--cafr-dir",
                    help="directory of CAFR PDFs (enables cafr_pdf)")
    ap.add_argument("--out", default="customer_intel_raw.csv")
    ap.add_argument("--out-merged", default="customer_intel_merged.csv")
    args = ap.parse_args()

    # Default selection: free connectors, exclude cafr_pdf (needs PDFs).
    # Also exclude:
    #   - dns_fingerprint (deprecated — dns_strict is the better successor)
    #   - meeting_minutes (slow; opt-in via --only meeting_minutes)
    selected = (args.only or [k for k in CONNECTORS
                              if k not in ("cafr_pdf", "dns_fingerprint",
                                             "meeting_minutes")])
    selected = [c for c in selected if c not in args.skip]

    print(f"Connectors selected: {selected}")
    raw = []
    for name in selected:
        if name not in CONNECTORS:
            print(f"  skipping unknown connector: {name}")
            continue
        desc, fn = CONNECTORS[name]
        print(f"\n=== {name} — {desc} ===")
        try:
            rows = fn(args) or []
        except Exception as e:
            print(f"  ERROR: {name} failed: {e}")
            rows = []
        print(f"  -> {len(rows)} rows")
        raw.extend(rows)

    print(f"\n{len(raw)} total raw rows across {len(selected)} connectors")
    write_csv(args.out, raw)
    print(f"  wrote {args.out}")

    merged = merge_rows(raw)
    print(f"{len(merged)} unique (vendor, muni, state) combos after merge")
    write_csv(args.out_merged, merged)
    print(f"  wrote {args.out_merged}")

    # Summary
    by_v = {}
    for r in merged:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    print("\nBy vendor:")
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")

    print("\nNext step:  python -m customer_intel.merge "
          + args.out_merged)


if __name__ == "__main__":
    main()
