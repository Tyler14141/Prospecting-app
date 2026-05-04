"""
Pre-bake US counties + ALL US municipalities + townships + special districts.

Sources:
  1. geonamescache — cities >= 15K population (with population data)
  2. lutangar/cities.json — comprehensive ~17K US named places
     (no population data; everything not in geonamescache is treated as
     a sub-15K muni and goes in the special "small (<15K)" bucket)
  3. STATE_COUNTS in data.py — for township + special-district COUNT
     placeholders. Real names require the Census Gazetteer county-
     subdivision file (`2023_Gaz_cousubs_national.txt`) and a state-by-
     state special-district registry — both hard to fetch from a
     locked-down sandbox. Drop those files into ./data_extras/ and
     re-run; this script will use them when present.

Output: names_data.json — consumed by the dashboard.
"""

import csv
import json
import os
import urllib.request

import geonamescache

from data import BUCKETS, STATE_COUNTS, STATES


HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "names_data.json")
ALL_CITIES_PATH = os.path.join(HERE, "all_cities.json")
ALL_CITIES_URL = ("https://raw.githubusercontent.com/lutangar/cities.json/"
                   "master/cities.json")
DATA_EXTRAS = os.path.join(HERE, "data_extras")
COUSUBS_PATH = os.path.join(DATA_EXTRAS, "2023_Gaz_cousubs_national.txt")
SPECIAL_DISTRICTS_PATH = os.path.join(DATA_EXTRAS, "special_districts.csv")

SMALL_BUCKET = "small (<15K)"


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


def ensure_all_cities():
    if os.path.exists(ALL_CITIES_PATH):
        return
    print(f"  fetching {ALL_CITIES_URL} (one-time, ~21MB)...")
    urllib.request.urlretrieve(ALL_CITIES_URL, ALL_CITIES_PATH)
    print(f"  saved to {ALL_CITIES_PATH}")


def build():
    gc = geonamescache.GeonamesCache()
    gnc_cities = gc.get_cities()
    counties = gc.get_us_counties()

    by_state = {s: {"counties": [], "cities": [],
                     "townships": [], "special_districts": []}
                for s in STATES}

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
    ensure_all_cities()
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

    # --- Townships ---
    # Try Census Gazetteer county-subdivisions file if user dropped it in
    # data_extras/. Otherwise emit count-based placeholders.
    township_real = 0
    if os.path.exists(COUSUBS_PATH):
        with open(COUSUBS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                st = (row.get("USPS") or "").strip()
                if st not in by_state:
                    continue
                name = (row.get("NAME") or "").strip()
                # Census includes "(no county subdivisions)" placeholders;
                # filter to actual organized townships.
                fc = (row.get("FUNCSTAT") or "").strip()
                if fc not in ("A", "B"):  # active organized
                    continue
                if not name:
                    continue
                by_state[st]["townships"].append({
                    "name": name,
                    "geoid": (row.get("GEOID") or "").strip(),
                    "real": True,
                })
                township_real += 1
        print(f"  {township_real} real townships from Census Gazetteer")
    else:
        # No Gazetteer file — emit a small preview of placeholders + a
        # metadata count so the dashboard can render the panel without
        # bloating the JSON. The dashboard shows "X total townships;
        # only Y named (drop Census Gazetteer for full list)".
        PREVIEW_CAP = 12
        for st in by_state:
            count = STATE_COUNTS[st][2]
            for i in range(min(count, PREVIEW_CAP)):
                by_state[st]["townships"].append({
                    "name": f"Township subdivision #{i + 1}",
                    "geoid": None,
                    "real": False,
                })
            by_state[st]["_township_count"] = count
        print(f"  {COUSUBS_PATH} not found — using placeholders for townships")
        print(f"    Drop the Census Gazetteer 2023_Gaz_cousubs_national.txt")
        print(f"    into ./data_extras/ and re-run for real names.")

    # --- Special districts ---
    sd_real = 0
    if os.path.exists(SPECIAL_DISTRICTS_PATH):
        with open(SPECIAL_DISTRICTS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                st = (row.get("state") or "").strip()
                if st not in by_state:
                    continue
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                by_state[st]["special_districts"].append({
                    "name": name,
                    "type": (row.get("type") or "").strip(),
                    "real": True,
                })
                sd_real += 1
        print(f"  {sd_real} real special districts from local registry")
    else:
        PREVIEW_CAP = 12
        for st in by_state:
            count = STATE_COUNTS[st][3]
            for i in range(min(count, PREVIEW_CAP)):
                by_state[st]["special_districts"].append({
                    "name": f"Special District #{i + 1}",
                    "type": None,
                    "real": False,
                })
            by_state[st]["_sd_count"] = count
        print(f"  {SPECIAL_DISTRICTS_PATH} not found — using placeholders for SDs")
        print(f"    Drop a CSV with columns 'state,name,type' into")
        print(f"    ./data_extras/ and re-run for real names.")

    # Sort: cities by pop desc (None at end), counties alphabetically
    for st in by_state:
        by_state[st]["counties"].sort(key=lambda x: x["name"])
        by_state[st]["cities"].sort(
            key=lambda x: (x["pop"] is None, -(x["pop"] or 0), x["name"]))
        by_state[st]["townships"].sort(key=lambda x: x["name"])
        by_state[st]["special_districts"].sort(key=lambda x: x["name"])

    total_cities = sum(len(b["cities"]) for b in by_state.values())
    total_counties = sum(len(b["counties"]) for b in by_state.values())
    total_townships = sum(len(b["townships"]) for b in by_state.values())
    total_sds = sum(len(b["special_districts"]) for b in by_state.values())
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
    print(f"  townships:                    {total_townships:,}  "
          f"(real={township_real})")
    print(f"  special districts:            {total_sds:,}  "
          f"(real={sd_real})")
    return by_state


if __name__ == "__main__":
    build()
