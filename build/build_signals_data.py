"""
Bake signals_data.json for the dashboard.

Structure: {types, severity, today, signals[], by_state{}, top_acts[]}

`top_acts` is the Act Now leaderboard: for each (muni, state) pair with
one or more signals, compute the composite score and rank.
"""

import json
import os
from datetime import date

from signals import (HARD_DROPOFF_DAYS, RECENCY_HALFLIFE_DAYS,
                     SEVERITY_FACTOR, SIGNAL_TYPES, SIGNALS, TODAY,
                     signal_score, state_signal_density)


HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
JSON_PATH = os.path.join(OUT_DIR, "signals_data.json")


def build():
    enriched = []
    for s in SIGNALS:
        score = signal_score(s, TODAY)
        if score == 0.0:
            continue  # outside dropoff window
        enriched.append({**s, "score": score})

    by_state = {}
    for s in enriched:
        st = s["state"]
        by_state.setdefault(st, []).append(s["id"])

    # Act Now leaderboard: aggregate by (muni, state). Skip "Statewide" /
    # "Vendor-wide" / "All states" which aren't actionable accounts.
    aggregated = {}
    for s in enriched:
        if s["state"] == "ALL" or s["muni"].startswith(("Statewide",
                                                          "Vendor-wide",
                                                          "All states")):
            continue
        key = (s["muni"], s["state"])
        if key not in aggregated:
            aggregated[key] = {
                "muni": s["muni"], "state": s["state"],
                "population": s["population"], "bucket": s["bucket"],
                "incumbent": s["incumbent"],
                "signals": [], "total_score": 0.0,
            }
        aggregated[key]["signals"].append(s["id"])
        aggregated[key]["total_score"] += s["score"]
        # Keep the most-recent incumbent if any signal has one
        if s["incumbent"] and not aggregated[key]["incumbent"]:
            aggregated[key]["incumbent"] = s["incumbent"]

    top_acts = sorted(aggregated.values(),
                      key=lambda a: -a["total_score"])

    payload = {
        "today": TODAY.isoformat(),
        "halflife_days": RECENCY_HALFLIFE_DAYS,
        "dropoff_days": HARD_DROPOFF_DAYS,
        "types": SIGNAL_TYPES,
        "severity_factor": SEVERITY_FACTOR,
        "signals": enriched,
        "by_state": by_state,
        "top_acts": top_acts,
        "_demo": True,
        "_demo_note": ("Seeded demo dataset. Replace by wiring connectors in "
                        "signals_pipeline.py."),
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"Wrote {JSON_PATH}")
    print(f"  {len(enriched)} active signals")
    print(f"  {len(top_acts)} accounts on leaderboard")
    print(f"  top 3:")
    for a in top_acts[:3]:
        print(f"    {a['total_score']:>5.2f}  {a['muni']:25s} {a['state']}  "
              f"{len(a['signals'])} signal(s)")


if __name__ == "__main__":
    build()
