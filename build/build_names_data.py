"""
Pre-bake US counties + ALL US municipalities from two sources:

  1. geonamescache — cities >= 15K population (with population data)
  2. lutangar/cities.json — comprehensive ~17K US named places
     (no population data; everything not in geonamescache is treated as
     a sub-15K muni and goes in the special "small (<15K)" bucket)

Output: names_data.json — consumed by the dashboard. Keeps the dashboard
self-contained (no client-side fetch).
"""

import json
import os

import geonamescache

from data import BUCKETS, STATES


HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "names_data.json")
ALL_CITIES_PATH = os.path.join(HERE, "all_cities.json")  # lutangar mirror

SMALL_BUCKET = "small (<15K)"  # special bucket for sub-15K munis


def bucket_for(pop):
    if pop is None or pop <= 0:
        return SMALL_BUCKET
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
    gnc_cities = gc.get_cities()
    counties = gc.get_us_counties()

    by_state = {s: {"counties": [], "cities": []} for s in STATES}

    # --- Counties ---
    for c in counties:
        st = c.get("state")
        if st in by_state:
            by_state[st]["counties"].append({
                "name": c["name"],
                "fips": c.get("fips", ""),
            })

    # --- Cities >= 15K from geonamescache (with population) ---
    seen = set()  # (state, name_lower) to dedupe
    for c in gnc_cities.values():
        if c.get("countrycode") != "US":
            continue
        pop = int(c.get("population", 0) or 0)
        if pop < 15000:
            continue
        st = c.get("admin1code")
        if st not in by_state:
            continue
        key = (st, c["name"].lower())
        if key in seen:
            continue
        seen.add(key)
        by_state[st]["cities"].append({
            "name": c["name"],
            "pop": pop,
            "bucket": bucket_for(pop),
            "lat": c.get("latitude"),
            "lon": c.get("longitude"),
        })

    # --- Smaller US places from lutangar mirror (no population) ---
    if os.path.exists(ALL_CITIES_PATH):
        with open(ALL_CITIES_PATH, "r", encoding="utf-8") as f:
            all_places = json.load(f)
        added_small = 0
        for p in all_places:
            if p.get("country") != "US":
                continue
            st = p.get("admin1")
            if st not in by_state:
                continue
            name = p.get("name", "").strip()
            if not name:
                continue
            key = (st, name.lower())
            if key in seen:
                continue
            seen.add(key)
            by_state[st]["cities"].append({
                "name": name,
                "pop": None,                       # unknown
                "bucket": SMALL_BUCKET,
                "lat": float(p["lat"]) if p.get("lat") else None,
                "lon": float(p["lng"]) if p.get("lng") else None,
            })
            added_small += 1
        print(f"  {added_small} small munis added from lutangar mirror")
    else:
        print(f"  warning: {ALL_CITIES_PATH} not found — skipping sub-15K munis")

    # Sort: cities by pop desc (None at end), counties alphabetically
    for st in by_state:
        by_state[st]["counties"].sort(key=lambda x: x["name"])
        by_state[st]["cities"].sort(
            key=lambda x: (x["pop"] is None, -(x["pop"] or 0), x["name"]))

    total_cities = sum(len(b["cities"]) for b in by_state.values())
    total_counties = sum(len(b["counties"]) for b in by_state.values())
    total_named = sum(1 for st in by_state for c in by_state[st]["cities"]
                      if c["pop"] is not None)
    total_small = total_cities - total_named

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_state, f, separators=(",", ":"))

    print(f"Wrote {OUT_PATH} ({os.path.getsize(OUT_PATH)/1024:.1f} KB)")
    print(f"  counties:                     {total_counties:,}")
    print(f"  munis with population (>=15K):{total_named:,}")
    print(f"  munis without population:     {total_small:,}")
    print(f"  total munis:                  {total_cities:,}")
    return by_state


if __name__ == "__main__":
    build()
