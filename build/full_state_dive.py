"""
Full state dive — scan every sub-15K muni in NY, PA, ME, OH for buying-
intent signals in council/board meeting minutes. Writes results to
build/harvested_signals.json, which build_lead_discovery_data.py
automatically merges into the dashboard's Lead Discovery feed.

What it does
------------
1. Loads names_data.json (16,834 US munis, including ~13,468 sub-15K
   towns from the lutangar mirror plus 3,366 geonamescache cities >=15K).
2. Filters to NY/PA/ME/OH, sub-15K populations (configurable).
3. For each muni: discovers official website, walks the meetings/agendas
   index, downloads up to N recent PDF minutes, runs the buying-intent
   extractor in customer_intel.connectors.meeting_minutes.
4. Aggregates intent signals, dedupes (one signal per muni-type), writes
   the merged set to harvested_signals.json.
5. The next time build_lead_discovery_data.py runs, those signals
   appear in the Lead Discovery feed alongside the seeded set.

Run
---
    cd build
    python3 full_state_dive.py                                # default: NY/PA/ME/OH, sub-15K, top-200 per state
    python3 full_state_dive.py --states NY PA ME OH --max-per-state 500
    python3 full_state_dive.py --states OH --pop-max 10000 --threads 25

Time
----
At default settings (4 states × 200 munis × 10 PDFs each × 1.5s polite
delay × 20 threads): ~2-3 hours wall-time. Slower than dns_strict
because each muni's website is a different host and PDFs are downloaded
sequentially. For a quick test run use `--max-per-state 25`.

Output
------
build/harvested_signals.json — list of intent/signal records ready to
ingest. Each one becomes a card in the Lead Discovery feed. Source URL
is preserved in each card so you can verify the quote against the
original PDF.
"""

import argparse
import json
import os
import sys
import time

# Make customer_intel importable when this script is run from /build
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from customer_intel.connectors import meeting_minutes


NAMES_PATH = os.path.join(HERE, "names_data.json")
OUT_PATH = os.path.join(HERE, "harvested_signals.json")


def load_targets(states, pop_max, max_per_state):
    """Build the muni list — sub-15K munis across the chosen states."""
    with open(NAMES_PATH) as f:
        data = json.load(f)
    targets = []
    by_state = {st: [] for st in states}
    for st in states:
        blob = data.get(st, {})
        for c in blob.get("cities", []):
            pop = c.get("pop")
            # Include both: populations < pop_max, AND the sub-15K
            # placeholder rows (pop=None from the lutangar mirror).
            if pop is not None and pop >= pop_max:
                continue
            by_state[st].append((c["name"], st, pop, c.get("bucket")))
    for st in states:
        sel = by_state[st][:max_per_state]
        targets.extend(sel)
        print(f"  {st}: {len(sel)} munis selected (cap {max_per_state})")
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="*", default=["NY", "PA", "ME", "OH"])
    ap.add_argument("--pop-max", type=int, default=15000)
    ap.add_argument("--max-per-state", type=int, default=200)
    ap.add_argument("--max-pdfs", type=int, default=10,
                    help="max meeting PDFs to download per muni")
    ap.add_argument("--threads", type=int, default=20)
    args = ap.parse_args()

    print(f"\nFULL STATE DIVE — states={args.states} pop<{args.pop_max} "
          f"max_per_state={args.max_per_state} max_pdfs={args.max_pdfs} "
          f"threads={args.threads}\n")

    targets = load_targets(args.states, args.pop_max, args.max_per_state)
    print(f"\nTotal munis to scan: {len(targets):,}")
    print(f"Estimated wall time: {len(targets) * args.max_pdfs * 1.5 / args.threads / 60:.0f} min")
    print()

    # Reuse the meeting_minutes harvest entry point. It's set up to
    # accept a target list via load_targets — we pre-filter and then
    # let it scan one-by-one in parallel.
    import concurrent.futures as cf
    t0 = time.time()
    customers, signals = [], []
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.threads) as ex:
        futs = {ex.submit(meeting_minutes.scan_muni, n, st, p, b,
                           max_pdfs=args.max_pdfs): (n, st)
                for n, st, p, b in targets}
        for fut in cf.as_completed(futs):
            done += 1
            try:
                cust, sigs = fut.result()
            except Exception as e:
                cust, sigs = [], []
            customers.extend(cust)
            signals.extend(sigs)
            if done % 25 == 0:
                elapsed = time.time() - t0
                rate = done / max(elapsed, 0.001)
                eta_min = (len(targets) - done) / max(rate, 0.001) / 60
                hit_munis = len({(s["muni"], s["state"]) for s in signals})
                print(f"  {done:,}/{len(targets):,}  "
                      f"({rate:.2f}/s, ETA {eta_min:.0f} min, "
                      f"{hit_munis} munis with intent signals, "
                      f"{len(signals)} signal rows)")

    print(f"\nDone in {(time.time() - t0)/60:.1f} min")
    print(f"  {len(customers)} confirmed customer approvals (verbatim $)")
    print(f"  {len(signals)} buying-intent / signal rows")

    # Dedupe near-duplicates while preserving distinct evidence threads.
    # Keep up to 3 rows per (muni, state, type), keyed by headline+details.
    keyed = {}
    per_type_count = {}
    for s in signals:
        group = (s["muni"], s["state"], s["type"])
        sig_text = (str(s.get("headline", "")) + "|" + str(s.get("details", ""))).lower()
        norm = "".join(ch if ch.isalnum() else " " for ch in sig_text)
        k = group + (" ".join(norm.split())[:180],)
        if k not in keyed:
            if per_type_count.get(group, 0) >= 3:
                continue
            keyed[k] = s
            per_type_count[group] = per_type_count.get(group, 0) + 1
    deduped = list(keyed.values())
    print(f"  {len(deduped)} unique muni-x-signal-type rows after dedupe")

    # Breakdown by signal type
    from collections import Counter
    by_type = Counter(s["type"] for s in deduped)
    print()
    print("Signals by type:")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t:14s}: {n}")

    # Also write the confirmed customers — these feed customer_intel/merge.py
    if customers:
        cust_path = os.path.join(HERE, "meeting_minutes_customers.csv")
        import csv
        with open(cust_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(customers[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for r in customers:
                w.writerow(r)
        print(f"\nWrote {cust_path}")

    # Save signals
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "harvested_at": _today_iso(),
            "states_scanned": args.states,
            "pop_max": args.pop_max,
            "munis_scanned": len(targets),
            "signals": deduped,
        }, f, separators=(",", ":"))
    print(f"Wrote {OUT_PATH}")
    print()
    print("Next: re-run the dashboard refresh pipeline to surface these")
    print("signals in the Lead Discovery tab:")
    print("    bash refresh_after_scan.sh")


def _today_iso():
    from datetime import date
    return date.today().isoformat()


if __name__ == "__main__":
    main()
