"""
Merge harvested customer-intel CSV into the running competitor_customers.py.

Usage
-----
    python -m customer_intel.merge customer_intel_merged.csv

Behavior
--------
- Loads existing CUSTOMERS list from competitor_customers.py
- Adds new (vendor, muni, state) records from the CSV that aren't already
  represented (case-insensitive match on muni + state).
- New records are flagged demo=False (they came from real sources).
- Existing demo rows are NOT removed automatically — run with `--prune-demo`
  to remove demo-only rows that the harvester confirmed via real sources.
- Confidence threshold filter (--min-confidence; default 0.7) drops noisy
  candidates.

After merging, the script prints a unified diff of competitor_customers.py
so you can review before committing. Pass `--write` to actually save.
"""

import argparse
import csv
import difflib
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
TARGET = os.path.join(PARENT, "competitor_customers.py")


def load_existing():
    """Import competitor_customers as a module and return its CUSTOMERS list."""
    sys.path.insert(0, PARENT)
    try:
        import competitor_customers as cc
        return cc.CUSTOMERS
    finally:
        sys.path.pop(0)


def existing_keys(customers):
    return {(c["vendor"], c["muni"].lower(), c["state"]) for c in customers}


def csv_rows(path: str, min_conf: float):
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                if float(r.get("confidence") or 0) < min_conf:
                    continue
            except ValueError:
                continue
            if not r.get("vendor") or not r.get("muni") or not r.get("state"):
                continue
            yield r


def render_record(r) -> str:
    """Render a CUSTOMERS list entry as a Python literal."""
    def _q(v):
        if v is None or v == "":
            return "None"
        if isinstance(v, (int, float)):
            return str(v)
        return repr(str(v))
    return ("    {"
            f'"vendor": {_q(r["vendor"])}, '
            f'"muni": {_q(r["muni"])}, '
            f'"state": {_q(r["state"])}, '
            f'"type": {_q(r.get("type") or "muni")}, '
            f'"bucket": {_q(r.get("bucket"))}, '
            f'"product": {_q(r.get("product"))}, '
            f'"since": {_q(r.get("since"))}, '
            f'"source": {_q(r.get("source") or "harvest")}, '
            f'"demo": False'
            "},")


def insert_records(target_path: str, new_records: list) -> str:
    """Read competitor_customers.py, splice new records before the closing
    `]` of the CUSTOMERS list, return the modified file content."""
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Find the closing bracket of CUSTOMERS list. Heuristic: last "\n]\n"
    # in the file, since CUSTOMERS is the only top-level list.
    end_idx = content.rfind("\n]")
    if end_idx == -1:
        raise RuntimeError("could not find closing ']' of CUSTOMERS list")
    block = ("\n    # ---- harvested via customer_intel "
              f"({len(new_records)} new) ----\n"
              + "\n".join(render_record(r) for r in new_records)
              + "\n")
    return content[:end_idx] + block + content[end_idx:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="path to merged CSV from harvest.py")
    ap.add_argument("--min-confidence", type=float, default=0.7)
    ap.add_argument("--write", action="store_true",
                    help="actually write competitor_customers.py "
                          "(default: dry run with diff)")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"ERROR: {args.csv} not found")
        sys.exit(2)
    if not os.path.exists(TARGET):
        print(f"ERROR: {TARGET} not found")
        sys.exit(2)

    existing = load_existing()
    keys = existing_keys(existing)
    print(f"Existing customers: {len(existing)}")

    new_records = []
    for r in csv_rows(args.csv, args.min_confidence):
        key = (r["vendor"], r["muni"].lower(), r["state"])
        if key in keys:
            continue
        keys.add(key)
        new_records.append(r)
    print(f"New records to add: {len(new_records)}")

    if not new_records:
        print("Nothing to merge.")
        return

    with open(TARGET, "r", encoding="utf-8") as f:
        before = f.read()
    after = insert_records(TARGET, new_records)

    if args.write:
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(after)
        print(f"WROTE {TARGET}  (+{len(new_records)} customers)")
        print("Next: re-run add_competitor_tab.py and build_dashboard_v2.py")
    else:
        diff = difflib.unified_diff(before.splitlines(keepends=True),
                                     after.splitlines(keepends=True),
                                     fromfile=TARGET, tofile=TARGET + ".new",
                                     n=2)
        sys.stdout.writelines(diff)
        print("\n(dry run — re-run with --write to apply)")


if __name__ == "__main__":
    main()
