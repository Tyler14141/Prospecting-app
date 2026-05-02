"""
Persona / title overlay — who actually buys local-gov software, by entity
size and product.

Most small munis don't have a CIO. The buyer is often the City Clerk,
Finance Director, or City Manager — sometimes the same person wearing all
three hats. This module returns the most-likely buying titles for any
(entity_type, bucket, product) combination.

# refreshed 2026-05-02
"""

# Population-bucket -> ordered list of likely buying-decision titles for a
# generic ERP / financial-management deal. The first title is the primary
# economic buyer; subsequent titles are influencers / approvers.
PERSONAS_BY_BUCKET = {
    "small (<15K)": [
        ("Town / Village Clerk", "primary"),
        ("Town / Village Treasurer", "primary"),
        ("Mayor / Council Member", "approver"),
    ],
    "<1K": [
        ("Village Clerk-Treasurer", "primary"),
        ("Mayor", "approver"),
    ],
    "1K-5K": [
        ("City Clerk", "primary"),
        ("City Treasurer", "primary"),
        ("City Manager / Administrator", "approver"),
    ],
    "5K-10K": [
        ("Finance Director", "primary"),
        ("City Clerk", "influencer"),
        ("City Manager / Administrator", "approver"),
    ],
    "10K-20K": [
        ("Finance Director", "primary"),
        ("IT Coordinator / Manager", "influencer"),
        ("City Manager / Administrator", "approver"),
    ],
    "20K-50K": [
        ("Finance Director", "primary"),
        ("IT Director", "influencer"),
        ("City Manager / Administrator", "approver"),
        ("Assistant City Manager", "influencer"),
    ],
    "50K-100K": [
        ("CFO / Finance Director", "primary"),
        ("CIO / IT Director", "influencer"),
        ("City Manager", "approver"),
        ("Procurement / Purchasing Manager", "approver"),
    ],
    "100K+": [
        ("CIO", "primary"),
        ("CFO", "primary"),
        ("City Manager / Mayor's Chief of Staff", "approver"),
        ("Procurement Director", "approver"),
        ("Innovation / Digital Services Director", "influencer"),
    ],
}

# Product-line -> primary buyer override + supporting titles
PERSONAS_BY_PRODUCT = {
    "ERP / Financials":     ["Finance Director", "CFO", "Comptroller"],
    "Utility Billing":      ["Utilities Director", "Public Works Director",
                             "Customer Service Manager"],
    "Permitting / EnerGov": ["Chief Building Official", "Planning Director",
                             "Director of Community Development"],
    "Courts / Justice":     ["Court Administrator", "Clerk of Court",
                             "Sheriff (counties)"],
    "Public Safety":        ["Police Chief", "Fire Chief",
                             "Emergency Mgmt Director"],
    "Tax / Assessing":      ["Tax Assessor", "Treasurer", "City Clerk"],
    "GIS":                  ["GIS Coordinator", "IT Director",
                             "Public Works Director"],
}

# Entity-type override (counties have different titles)
PERSONAS_BY_ENTITY_TYPE = {
    "county": [
        ("County Administrator / Manager", "approver"),
        ("County Auditor", "primary"),
        ("County Clerk", "influencer"),
        ("Director of Information Technology", "influencer"),
    ],
    "township": [
        ("Township Supervisor", "approver"),
        ("Township Clerk", "primary"),
        ("Township Treasurer", "primary"),
    ],
    "special_district": [
        ("General Manager / District Manager", "approver"),
        ("Finance Manager", "primary"),
        ("Board President", "approver"),
    ],
}

# Where to find these contacts publicly (no scraping required to start)
DIRECTORY_HINTS = {
    "default": [
        ("State League of Cities directory",
         "https://www.nlc.org/state-municipal-leagues/"),
        ("National Assoc. of County Clerks",
         "https://www.naco.org/"),
        ("GFOA member directory",
         "https://www.gfoa.org/"),
    ],
    "MI": [("Michigan Municipal League directory", "https://mml.org/")],
    "TX": [("Texas Municipal League directory", "https://www.tml.org/")],
    "CA": [("League of California Cities", "https://www.cacities.org/")],
    "NY": [("NY Conference of Mayors", "https://www.nycom.org/")],
    "FL": [("Florida League of Cities", "https://www.floridaleagueofcities.com/")],
    "PA": [("PA State Assoc. of Boroughs / PSATS",
            "https://www.psab.org/")],
    "OH": [("Ohio Municipal League", "https://www.omlohio.org/")],
    "IL": [("Illinois Municipal League", "https://www.iml.org/")],
    "IA": [("Iowa League of Cities", "https://www.iowaleague.org/")],
    "NE": [("League of Nebraska Municipalities", "https://www.lonm.org/")],
}


def personas_for(entity_type: str, bucket: str, product: str = None):
    """Return ordered list of (title, role) tuples — most-likely buyers
    for this entity x size x product combination."""
    out = []
    seen = set()

    def _add(title, role):
        if title in seen:
            return
        seen.add(title)
        out.append((title, role))

    # Entity-type override (counties / townships / SDs use different titles)
    et_titles = PERSONAS_BY_ENTITY_TYPE.get(entity_type, [])
    for t, r in et_titles:
        _add(t, r)

    # Bucket-default titles (apply to munis primarily)
    if entity_type == "muni" or not et_titles:
        for t, r in PERSONAS_BY_BUCKET.get(bucket or "small (<15K)", []):
            _add(t, r)

    # Product-line specific overrides take precedence at the front
    if product:
        prod_key = _match_product(product)
        if prod_key:
            prod_titles = PERSONAS_BY_PRODUCT[prod_key]
            # Insert product-specific titles at front
            existing = [(t, r) for t, r in out if t not in prod_titles]
            out = [(t, "primary") for t in prod_titles] + existing
    return out[:5]


def _match_product(product: str):
    """Map a vendor product string to one of PERSONAS_BY_PRODUCT keys."""
    p = (product or "").lower()
    if any(k in p for k in ("munis", "erp", "financial", "financials",
                              "general ledger", "gl", "fund acct",
                              "fund accounting", "caselle connect",
                              "gworks suite", "banyon")):
        return "ERP / Financials"
    if any(k in p for k in ("utility billing", "water billing",
                              "muni-link")):
        return "Utility Billing"
    if any(k in p for k in ("energov", "permit", "planning",
                              "civic access", "code enforcement")):
        return "Permitting / EnerGov"
    if any(k in p for k in ("court", "odyssey")):
        return "Courts / Justice"
    if any(k in p for k in ("public safety", "cad", "rms",
                              "new world", "brazos")):
        return "Public Safety"
    if any(k in p for k in ("tax", "assess")):
        return "Tax / Assessing"
    if any(k in p for k in ("gis", "mapping")):
        return "GIS"
    return None


def directory_links_for(state: str):
    out = list(DIRECTORY_HINTS.get(state, []))
    out.extend(DIRECTORY_HINTS["default"])
    return out


if __name__ == "__main__":
    print("Personas for a 5K-pop muni, ERP product:")
    for t, r in personas_for("muni", "1K-5K", "Munis ERP"):
        print(f"  [{r:10s}] {t}")
    print()
    print("Personas for a county, courts product:")
    for t, r in personas_for("county", "100K+", "Odyssey Courts"):
        print(f"  [{r:10s}] {t}")
    print()
    print("Personas for utility billing in 30K-pop city:")
    for t, r in personas_for("muni", "20K-50K", "Utility Billing"):
        print(f"  [{r:10s}] {t}")
