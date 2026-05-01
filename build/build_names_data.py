"""
Pre-bake US counties + cities ≥15K population from geonamescache.

Output: names_data.json — consumed by the workbook + dashboard. Keeps the
dashboard self-contained (no client-side fetch).
"""

import json
import os

import geonamescache

from data import BUCKETS, STATES


HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "names_data.json")


def bucket_for(pop: int) -> str:
    """Return bucket label for a given population."""
    for label, lo, hi, _ in BUCKETS:
        if hi is None:
            if pop >= lo:
                return label
        else:
            if lo <= pop < hi:
                return label
    return BUCKETS[0][0]


def build():
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()
    counties = gc.get_us_counties()

    by_state = {s: {"counties": [], "cities": []} for s in STATES}

    # Counties
    for c in counties:
        st = c.get("state")
        if st in by_state:
            by_state[st]["counties"].append({
                "name": c["name"],
                "fips": c.get("fips", ""),
            })

    # Cities (≥15K pop only — keeps the JSON size sane and matches dashboard
    # filtering)
    for c in cities.values():
        if c.get("countrycode") != "US":
            continue
        pop = int(c.get("population", 0) or 0)
        if pop < 15000:
            continue
        st = c.get("admin1code")
        if st not in by_state:
            continue
        by_state[st]["cities"].append({
            "name": c["name"],
            "pop": pop,
            "bucket": bucket_for(pop),
            "lat": c.get("latitude"),
            "lon": c.get("longitude"),
        })

    # Sort
    for st in by_state:
        by_state[st]["counties"].sort(key=lambda x: x["name"])
        by_state[st]["cities"].sort(key=lambda x: -x["pop"])

    total_cities = sum(len(b["cities"]) for b in by_state.values())
    total_counties = sum(len(b["counties"]) for b in by_state.values())

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_state, f, separators=(",", ":"))

    print(f"Wrote {OUT_PATH}")
    print(f"  cities (≥15K pop):  {total_cities}")
    print(f"  counties:           {total_counties}")
    return by_state


if __name__ == "__main__":
    build()
