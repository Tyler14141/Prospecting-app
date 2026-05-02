"""
Bake greenfield_data.json for the dashboard.

Output structure:
    {
      "today": "2026-05-02",
      "top_prospects": [score_muni(...), ...]   # sorted desc, top 1500
      "all_personas": { bucket: [{title, role}], ... },
      "renewal_status_buckets": { status: count }
    }

Top-1500 cap keeps the dashboard JSON ≤ ~600KB.
"""

import json
import os
from collections import Counter

from greenfield import build_indices, score_muni
from personas import PERSONAS_BY_BUCKET
from renewals import TODAY


HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_PATH = os.path.join(HERE, "names_data.json")
OUT = os.path.normpath(os.path.join(HERE, "..", "TAM", "greenfield_data.json"))

TOP_N = 1000
MIN_SCORE = 35


def build():
    with open(NAMES_PATH) as f:
        names = json.load(f)

    indices = build_indices()
    rows = []
    for st, blob in names.items():
        for c in blob.get("cities", []):
            rows.append(score_muni(c["name"], st, c.get("pop"),
                                     c.get("bucket"), indices))
    rows.sort(key=lambda r: -r["score"])
    top = [r for r in rows if r["score"] >= MIN_SCORE][:TOP_N]

    # Status counts across the whole population
    status_counts = Counter()
    for r in rows:
        rw = r.get("renewal")
        if rw:
            status_counts[rw["status"]] += 1
        elif r["incumbent"] is None:
            status_counts["greenfield"] += 1

    # Compact persona dict for the dashboard (bucket -> primary 3 titles)
    persona_short = {b: [t for t, _ in titles[:3]]
                      for b, titles in PERSONAS_BY_BUCKET.items()}

    # Compact each row — strip large embeddable fields, keep only what
    # the dashboard renders.
    state_dirhints = {}
    compact = []
    for r in top:
        rw = r.get("renewal")
        compact.append({
            "muni": r["muni"], "state": r["state"], "pop": r["pop"],
            "bucket": r["bucket"], "type": r.get("entity_type", "muni"),
            "score": r["score"],
            "components": r["components"],
            "incumbent": (
                {"vendor": r["incumbent"]["vendor"],
                 "product": r["incumbent"].get("product"),
                 "since":   r["incumbent"].get("since")}
                if r["incumbent"] else None
            ),
            "renewal_status": rw["status"] if rw else (
                "greenfield" if r["incumbent"] is None else "unknown"),
            "renewal_label": rw["label"] if rw else None,
            "next_renewal_min": rw["next_renewal_min"] if rw else None,
            "next_renewal_max": rw["next_renewal_max"] if rw else None,
            "personas": [t for t, _ in r["personas"][:3]],
            "signals_n": len(r.get("signals", [])),
        })
        # Stash directory hints once per state
        if r["state"] not in state_dirhints:
            state_dirhints[r["state"]] = [
                {"label": label, "url": url}
                for label, url in r["directory_hints"]
            ]

    payload = {
        "today": TODAY.isoformat(),
        "top_prospects": compact,
        "personas_by_bucket": persona_short,
        "directory_hints_by_state": state_dirhints,
        "status_counts": dict(status_counts),
        "total_scored": len(rows),
        "min_score": MIN_SCORE,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {OUT} ({os.path.getsize(OUT)/1024:.1f} KB)")
    print(f"  scored {len(rows):,} munis")
    print(f"  top-{TOP_N} retained")
    print(f"  status counts: {dict(status_counts)}")
    print(f"  top score: {top[0]['score']}")
    print(f"  cutoff score (#{TOP_N}): {top[-1]['score']}")


if __name__ == "__main__":
    build()
