"""
Local Government TAM — model inputs.
Sources: 2022 Census of Governments (entity counts), Census Annual Survey of
State and Local Government Finances 2022 (operating spend ~ $2.2T).

# refreshed 2026-05-01
"""

# ---- Population buckets ---------------------------------------------------
# Each bucket: (label, lower_inclusive, upper_exclusive_or_None, avg_pop_for_spend_math)
BUCKETS = [
    ("<1K",       0,      1000,   450),
    ("1K-5K",     1000,   5000,   2700),
    ("5K-10K",    5000,   10000,  7100),
    ("10K-20K",   10000,  20000,  14000),
    ("20K-50K",   20000,  50000,  31000),
    ("50K-100K",  50000,  100000, 70000),
    ("100K+",     100000, None,   220000),
]
BUCKET_LABELS = [b[0] for b in BUCKETS]
BUCKET_AVG_POP = [b[3] for b in BUCKETS]

# ---- Per-capita operating spend by bucket --------------------------------
# Indexed parallel to BUCKETS. Counties are U-shaped (small counties carry
# fixed admin overhead per resident; very large counties run more services).
SPEND_PER_CAPITA = {
    "munis":      [2000, 2500, 3000, 3500, 4200, 4800, 7000],
    "counties":   [3500, 3300, 2900, 2700, 2900, 3200, 3500],
    "townships":  [600,  800,  1100, 1400, 1600, 1700, 1800],
}
# Special districts: flat average annual spend per district
SPECIAL_DISTRICT_SPEND = 7_600_000  # $7.6M

# ---- National baseline bucket distributions (% of entities) ---------------
# Sum to 1.0 per row. These are the starting point; state skew factors below
# multiply per-bucket and the result is renormalized.
BASELINE_DIST = {
    "munis":     [0.35, 0.30, 0.12, 0.10, 0.08, 0.03, 0.02],
    "counties":  [0.01, 0.08, 0.11, 0.17, 0.26, 0.17, 0.20],
    "townships": [0.50, 0.32, 0.09, 0.05, 0.03, 0.01, 0.00],
}

# ---- State-level skew profiles -------------------------------------------
# Multipliers applied per-bucket to the baseline before renormalization.
# 'urban_strong' tilts mass into 20K+ buckets; 'rural_strong' tilts into <5K.
SKEW_PROFILES = {
    "urban_strong": [0.55, 0.70, 0.90, 1.10, 1.45, 1.80, 2.20],
    "urban_mild":   [0.80, 0.90, 1.00, 1.05, 1.20, 1.30, 1.45],
    "balanced":     [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
    "rural_mild":   [1.20, 1.15, 1.05, 0.95, 0.85, 0.75, 0.60],
    "rural_strong": [1.55, 1.30, 1.05, 0.85, 0.65, 0.45, 0.30],
}

# State-level multiplier on per-capita spend (cost-of-living + fiscal
# capacity proxy). Anchored to national avg = 1.00. Sourced from BEA
# Regional Price Parities + state/local own-source revenue per capita.
STATE_COST_FACTOR = {
    "AL": 0.85, "AK": 1.25, "AZ": 0.95, "AR": 0.80, "CA": 1.45, "CO": 1.05,
    "CT": 1.25, "DE": 1.00, "FL": 1.00, "GA": 0.90, "HI": 1.50, "ID": 0.95,
    "IL": 0.95, "IN": 0.85, "IA": 0.85, "KS": 0.85, "KY": 0.85, "LA": 0.90,
    "ME": 0.95, "MD": 1.15, "MA": 1.30, "MI": 0.85, "MN": 0.95, "MS": 0.80,
    "MO": 0.85, "MT": 0.95, "NE": 0.85, "NV": 1.00, "NH": 1.05, "NJ": 1.30,
    "NM": 0.85, "NY": 1.40, "NC": 0.90, "ND": 0.90, "OH": 0.85, "OK": 0.85,
    "OR": 1.05, "PA": 0.95, "RI": 1.10, "SC": 0.85, "SD": 0.85, "TN": 0.85,
    "TX": 0.95, "UT": 1.00, "VT": 1.00, "VA": 1.05, "WA": 1.15, "WV": 0.85,
    "WI": 0.90, "WY": 0.90, "DC": 1.40,
}

# Each state mapped to its skew profile.
STATE_SKEW = {
    "AL": "rural_mild",   "AK": "rural_strong", "AZ": "urban_mild",
    "AR": "rural_mild",   "CA": "urban_strong", "CO": "urban_mild",
    "CT": "urban_mild",   "DE": "urban_mild",   "FL": "urban_strong",
    "GA": "balanced",     "HI": "urban_mild",   "ID": "rural_mild",
    "IL": "urban_strong", "IN": "balanced",     "IA": "rural_strong",
    "KS": "rural_strong", "KY": "rural_mild",   "LA": "rural_mild",
    "ME": "rural_strong", "MD": "urban_mild",   "MA": "urban_strong",
    "MI": "balanced",     "MN": "balanced",     "MS": "rural_mild",
    "MO": "balanced",     "MT": "rural_strong", "NE": "rural_strong",
    "NV": "urban_mild",   "NH": "rural_mild",   "NJ": "urban_strong",
    "NM": "rural_mild",   "NY": "urban_strong", "NC": "balanced",
    "ND": "rural_strong", "OH": "balanced",     "OK": "rural_mild",
    "OR": "balanced",     "PA": "balanced",     "RI": "urban_mild",
    "SC": "balanced",     "SD": "rural_strong", "TN": "balanced",
    "TX": "urban_mild",   "UT": "urban_mild",   "VT": "rural_strong",
    "VA": "balanced",     "WA": "urban_mild",   "WV": "rural_mild",
    "WI": "balanced",     "WY": "rural_strong", "DC": "urban_strong",
}

# ---- Per-state entity counts (2022 Census of Governments) -----------------
# (counties, municipalities, townships, special_districts)
# School districts intentionally excluded per scope.
STATE_COUNTS = {
    "AL": (67, 461, 0,    540),
    "AK": (14, 148, 0,    15),
    "AZ": (15, 91,  0,    318),
    "AR": (75, 502, 0,    723),
    "CA": (58, 482, 0,    2767),
    "CO": (62, 271, 0,    2540),
    "CT": (0,  30,  149,  460),
    "DE": (3,  57,  0,    256),
    "FL": (66, 412, 0,    1134),
    "GA": (153,537, 0,    720),
    "HI": (3,  1,   0,    17),
    "ID": (44, 200, 0,    1058),
    "IL": (102,1298,1431, 3050),
    "IN": (91, 568, 1006, 1262),
    "IA": (99, 941, 0,    562),
    "KS": (103,624, 1268, 1535),
    "KY": (118,418, 0,    720),
    "LA": (60, 304, 0,    95),
    "ME": (16, 22,  467,  226),
    "MD": (23, 157, 0,    90),
    "MA": (5,  53,  298,  480),
    "MI": (83, 533, 1240, 451),
    "MN": (87, 853, 1781, 482),
    "MS": (82, 297, 0,    467),
    "MO": (114,954, 312,  1620),
    "MT": (54, 127, 0,    813),
    "NE": (93, 530, 415,  1300),
    "NV": (16, 19,  0,    175),
    "NH": (10, 13,  221,  142),
    "NJ": (21, 565, 0,    281),
    "NM": (33, 105, 0,    685),
    "NY": (57, 614, 933,  1183),
    "NC": (100,552, 0,    311),
    "ND": (53, 357, 1311, 763),
    "OH": (88, 937, 1308, 776),
    "OK": (77, 599, 0,    560),
    "OR": (36, 241, 0,    1057),
    "PA": (67, 1015,1546, 1620),
    "RI": (0,  8,   31,   84),
    "SC": (46, 271, 0,    297),
    "SD": (66, 311, 921,  350),
    "TN": (92, 345, 0,    525),
    "TX": (254,1221,0,    3100),
    "UT": (29, 248, 0,    1129),
    "VT": (14, 47,  237,  156),
    "VA": (95, 229, 0,    195),
    "WA": (39, 281, 0,    1336),
    "WV": (55, 232, 0,    358),
    "WI": (72, 596, 1255, 730),
    "WY": (23, 99,  0,    683),
    "DC": (0,  1,   0,    1),
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

# 50 states + DC
STATES = list(STATE_COUNTS.keys())

# ---- US tile-map layout (rows top-to-bottom; "" is empty cell) -----------
TILE_MAP = [
    ["",  "",  "",  "",  "",  "",  "",  "",  "",  "",  "ME"],
    ["AK","",  "",  "",  "",  "",  "",  "",  "VT","NH",""],
    ["",  "",  "",  "",  "",  "",  "",  "MI","NY","MA",""],
    ["WA","ID","MT","ND","MN","WI","",  "",  "PA","CT","RI"],
    ["OR","UT","WY","SD","IA","IL","IN","OH","WV","NJ",""],
    ["CA","NV","CO","NE","MO","KY","VA","",  "MD","DE",""],
    ["",  "AZ","NM","KS","AR","TN","NC","SC","DC","",  ""],
    ["HI","",  "",  "OK","LA","MS","AL","GA","",  "",  ""],
    ["",  "",  "",  "TX","",  "",  "",  "FL","",  "",  ""],
]

# ---- National anchors (for reconciliation checks) -------------------------
NATIONAL_ANCHORS = {
    "counties":          3031,
    "municipalities":    19495,
    "townships":         16253,
    "special_districts": 39555,
    "total_op_spend":    2_200_000_000_000,  # $2.2T
}


# ---- Helpers --------------------------------------------------------------
def state_distribution(entity_type: str, state: str):
    """Return per-bucket fractions for a given entity type and state."""
    base = BASELINE_DIST[entity_type]
    skew = SKEW_PROFILES[STATE_SKEW[state]]
    raw = [b * s for b, s in zip(base, skew)]
    total = sum(raw)
    return [r / total for r in raw]


def state_bucket_counts(entity_type: str, state: str):
    """Return absolute entity counts per bucket (rounded, sum-preserving)."""
    idx = {"counties": 0, "munis": 1, "townships": 2}[entity_type]
    total = STATE_COUNTS[state][idx]
    if total == 0:
        return [0] * len(BUCKETS)
    fractions = state_distribution(entity_type, state)
    raw = [total * f for f in fractions]
    floored = [int(x) for x in raw]
    remainder = total - sum(floored)
    # Distribute remainder to largest fractional parts
    fracs = sorted(
        ((raw[i] - floored[i], i) for i in range(len(raw))),
        reverse=True
    )
    for k in range(remainder):
        floored[fracs[k % len(fracs)][1]] += 1
    return floored


def state_spend_by_bucket(entity_type: str, state: str):
    """Spend per bucket = count × avg_bucket_pop × per_capita_spend × cost_factor."""
    counts = state_bucket_counts(entity_type, state)
    pcs = SPEND_PER_CAPITA[entity_type]
    cf = STATE_COST_FACTOR[state]
    return [counts[i] * BUCKET_AVG_POP[i] * pcs[i] * cf for i in range(len(BUCKETS))]


def state_special_district_spend(state: str):
    return int(STATE_COUNTS[state][3] * SPECIAL_DISTRICT_SPEND * STATE_COST_FACTOR[state])


def total_state_spend(state: str):
    s = sum(state_spend_by_bucket("munis", state))
    s += sum(state_spend_by_bucket("counties", state))
    s += sum(state_spend_by_bucket("townships", state))
    s += state_special_district_spend(state)
    return s


def total_state_entities(state: str):
    c, m, t, sd = STATE_COUNTS[state]
    return c + m + t + sd


# ---- Self-test (run `python data.py`) ------------------------------------
if __name__ == "__main__":
    nat_c = sum(v[0] for v in STATE_COUNTS.values())
    nat_m = sum(v[1] for v in STATE_COUNTS.values())
    nat_t = sum(v[2] for v in STATE_COUNTS.values())
    nat_sd = sum(v[3] for v in STATE_COUNTS.values())
    print(f"Counties:          {nat_c:>6}  anchor {NATIONAL_ANCHORS['counties']}")
    print(f"Municipalities:    {nat_m:>6}  anchor {NATIONAL_ANCHORS['municipalities']}")
    print(f"Townships:         {nat_t:>6}  anchor {NATIONAL_ANCHORS['townships']}")
    print(f"Special districts: {nat_sd:>6}  anchor {NATIONAL_ANCHORS['special_districts']}")
    total_spend = sum(total_state_spend(s) for s in STATES)
    print(f"Total operating spend: ${total_spend/1e12:.2f}T  anchor $2.20T")
