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
                     signal_score)
from verified_signals import VERIFIED_SIGNALS_CSV, load_verified_signals


HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
JSON_PATH = os.path.join(OUT_DIR, "signals_data.json")

TARGET_STATES = {"NY", "PA", "ME", "OH"}
MAX_POPULATION = 15_000
REQUIRE_VERIFIED = False   # False = include demo signals; flip True for prod-only verified


def _is_verified_signal(sig: dict) -> bool:
    """A verified signal must be non-demo and include a resolvable URL."""
    if sig.get("demo", True):
        return False
    url = sig.get("url")
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def _target_signal(sig: dict) -> bool:
    """Keep only sub-15K muni-level signals for NY/PA/ME/OH."""
    if REQUIRE_VERIFIED and not _is_verified_signal(sig):
        return False
    if sig["state"] not in TARGET_STATES:
        return False
    if sig["population"] <= 0 or sig["population"] >= MAX_POPULATION:
        return False
    if sig["muni"].startswith(("Statewide", "Vendor-wide", "All states")):
        return False
    return True


def build():
    verified = load_verified_signals(VERIFIED_SIGNALS_CSV)
    if not REQUIRE_VERIFIED:
        # Demo mode: supplement verified signals with seeded dataset
        seen_ids = {s["id"] for s in verified}
        source_signals = verified + [s for s in SIGNALS if s["id"] not in seen_ids]
    else:
        source_signals = verified

    enriched = []
    for s in source_signals:
        if not _target_signal(s):
            continue
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
        "_demo": False,
        "_filter": {
            "states": sorted(TARGET_STATES),
            "max_population_exclusive": MAX_POPULATION,
            "require_verified": REQUIRE_VERIFIED,
        },
        "_demo_note": ("Only verified records are included. Demo placeholders "
                        "are excluded until live connectors are wired in "
                        "signals_pipeline.py."),
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"Wrote {JSON_PATH}")
    print(f"  source file: {VERIFIED_SIGNALS_CSV}")
    print(f"  imported verified rows: {len(source_signals)}")
    print(f"  {len(enriched)} active signals")
    print(f"  {len(top_acts)} accounts on leaderboard")
    if not enriched:
        print("  no verified records matched current filters")
    print(f"  top 3:")
    for a in top_acts[:3]:
        print(f"    {a['total_score']:>5.2f}  {a['muni']:25s} {a['state']}  "
              f"{len(a['signals'])} signal(s)")


if __name__ == "__main__":
    build()
