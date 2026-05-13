"""
Lead Discovery — generates rich lead context per prospect.

For each (muni, signal) pair, produces:
  - Pain Points: 3-5 bullets derived from incumbent vendor, bucket size,
    and signal type. These are the "why now" reasons the prospect is
    likely to buy.
  - Recommended Approach: a short outreach playbook — primary buyer to
    contact, opening message, differentiator to lead with, social proof
    to reference.

Pain points are templated by (incumbent_vendor, bucket, signal_type)
with sensible defaults. Each template references a real, observed
friction point for the relevant combination.
"""

from typing import Optional


# ---- Pain-point templates by incumbent vendor ---------------------------
PAIN_POINTS_BY_INCUMBENT = {
    "Tyler Technologies": [
        "Tyler Munis pricing has crept above small-muni budget bands (6-8% annual uplift)",
        "Implementation timelines (6-18 months) misaligned with sub-10K staff capacity",
        "Premium feature set carries premium cost — many small munis use <30% of capability",
        "Migration path from acquired products (New World, Eden, Incode) requires re-purchase",
    ],
    "BS&A Software": [
        "Harris/Constellation ownership driving product line consolidation concerns",
        "Cloud migration path unclear; many munis still on legacy on-prem install",
        "Heavily MI-centric vendor — limited regional reference customers outside Michigan",
        "Tax/assessing focus leaves gaps in modern utility billing + permitting",
    ],
    "Caselle": [
        "DOS-era legacy suite approaching end-of-support",
        "On-prem deployment model creates IT burden for towns with no IT staff",
        "Limited modern integrations (no GIS, no permitting, no citizen portal)",
        "Long-tenured staff aging out; institutional knowledge departing with them",
    ],
    "gWorks": [
        "Roll-up integration debt (Banyon + Pontem + Compu-Strategies) frustrates users",
        "Sales motion still direct-only — no implementation partner channel",
        "Reporting limitations cited in user community for mid-sized customers (10-20K)",
        "GIS module less mature than dedicated providers (Esri, Cartegraph)",
    ],
    "Muni-Link": [
        "Single-vertical (utility billing only) requires separate ERP — multi-vendor stack",
        "Per-account pricing increases penalize growing utility customer base",
        "Limited reporting flexibility vs. full-suite ERPs",
        "Integration with other muni systems requires custom development",
    ],
    "TownCloud": [
        "Newer vendor — limited reference base; long-term viability concerns for risk-averse buyers",
        "Functional depth in tax/assessing still maturing",
        "Implementation partner ecosystem thin",
        "Pricing model (per-resident SaaS) misunderstood by traditional procurement",
    ],
}

PAIN_POINTS_GREENFIELD = [
    "Manual processes — likely Excel + paper for core financial and utility billing workflows",
    "No integrated system — staff duplicates data entry across 3-5 disconnected tools",
    "Audit findings recurring due to lack of automated controls",
    "Citizen-services digitization initiatives blocked by absence of modern back office",
]


PAIN_POINTS_BY_BUCKET = {
    "<1K": [
        "Single clerk-treasurer wears all hats — limited capacity to evaluate vendors",
        "Sub-$10K software budgets favor SaaS over enterprise systems",
    ],
    "1K-5K": [
        "Two-person finance team typical — software must minimize training overhead",
        "Procurement thresholds often <$50K direct-award eligible (vendor relationship advantage)",
    ],
    "5K-10K": [
        "Finance director typically reports to City/Town Manager — single approval chain",
        "Annual capex line item in $20-40K range — full ERP within reach",
    ],
    "10K-20K": [
        "Mid-market sweet spot — full ERP justified by transaction volume",
        "Pressure from elected officials for citizen-facing portals (payments, permits)",
    ],
}


PAIN_POINTS_BY_SIGNAL = {
    "rfp": [
        "Public RFP issued — clear timeline, public competition",
        "Procurement department managing process — bid response must hit compliance bar",
    ],
    "installed_base": [
        "Incumbent footprint confirmed from public artifacts — account is in a known replacement cycle",
        "Displacement motion can target integration gaps, support friction, or price pressure",
    ],
    "intent": [
        "Council has formally signaled intent — RFP not yet public, low competitor density",
        "Window to influence requirements before they're locked into a public spec",
    ],
    "vendor_eol": [
        "Forced migration creates non-discretionary buying window",
        "Vendor in disruption — incumbent relationship is unusually breakable right now",
    ],
    "cyber": [
        "Recent incident drives cloud-migration discussion and security-first criteria",
        "Insurance carrier or state may require remediation timeline",
    ],
    "leadership": [
        "New finance director / manager in first 90 days — stack review is standard",
        "Incoming buyer wants to make their mark — modernization is a typical first project",
    ],
    "audit": [
        "Material weakness must be remediated per state auditor — fixed timeline",
        "Pressure from council to demonstrate corrective action",
    ],
    "bond": [
        "Capital appropriation includes software line item — money is committed",
        "Bond covenants often require milestones — accelerated procurement",
    ],
    "compliance": [
        "State-mandated deadline — buying is non-discretionary",
        "Penalties for non-compliance create urgency the vendor can lean on",
    ],
}


# ---- Recommended Approach -----------------------------------------------
APPROACH_BY_SIGNAL = {
    "installed_base": (
        "Start with displacement discovery: reach out to the {persona} with a concise"
        " incumbent-gap checklist for {bucket} municipalities in {state}."
        " Ask for a 20-minute operational review and anchor on measurable wins"
        " (time-to-close, month-end speed, resident payment UX)."
    ),
    "intent": (
        "Reach out to the {persona} this week — RFP isn't public yet, "
        "so competitor density is near zero. Lead with: 'I noticed your "
        "{detail_short}. We're solving that for similar {bucket}-pop munis "
        "in {state}.' Offer a 30-minute demo focused on their stated "
        "concern. Goal: influence RFP scope before it goes public."
    ),
    "rfp": (
        "Submit a strong response before the {deadline} deadline. Have "
        "the {persona} on a call BEFORE submitting — even a 15-minute "
        "clarifying-questions session positions you as the front-runner. "
        "Reference {nearby_customer} as social proof in the response."
    ),
    "vendor_eol": (
        "Time-sensitive: {incumbent} is in transition. Reach out to the "
        "{persona} this week with a clear migration playbook: 90-day "
        "cutover from {incumbent}, data migration, parallel-run support. "
        "Quantify savings vs. their forced upgrade path."
    ),
    "cyber": (
        "Lead with security and cloud-migration framing. Connect "
        "{persona} with your CISO or security lead for a 30-minute session "
        "on your security posture and incident-response SLAs. Reference "
        "your SOC 2 / cyber-insurance status up front."
    ),
    "leadership": (
        "Welcome-aboard outreach to the new {persona} in their first 90 "
        "days. Don't sell — offer to share peer benchmarks from similar "
        "{bucket} munis in {state}. Convert to a discovery call once "
        "trust is built (typically 30-60 days)."
    ),
    "audit": (
        "Position as remediation partner, not just vendor. Lead with: "
        "'We've helped {nearby_customer} resolve a similar finding in "
        "under 90 days.' Bring a sample audit-response document to the "
        "first meeting."
    ),
    "bond": (
        "Money is allocated — execution risk is the buyer's concern, not "
        "price. Lead with implementation track record and PM methodology. "
        "Bring a sample project timeline to the first meeting."
    ),
    "compliance": (
        "Frame as deadline-coverage: 'Here's our path to your "
        "{deadline_short} requirement.' Reference any state/regional "
        "customers already in compliance with the same mandate."
    ),
}


# Per-state nearby-customer references — used in approach text
NEARBY_CUSTOMERS_BY_STATE = {
    "NY": ["Boston MA (Tyler Munis)", "Henrico County VA (Tyler Munis)"],
    "PA": ["Pittsburgh PA (Tyler Munis)", "Erie PA (Muni-Link)"],
    "ME": ["Boston MA (Tyler Munis)", "Bath ME peer reference"],
    "OH": ["Akron OH (Muni-Link)", "Toledo OH (BS&A)"],
}


# ---- Public API ---------------------------------------------------------
def pain_points_for(incumbent_vendor: Optional[str],
                     bucket: Optional[str],
                     signal_type: Optional[str]) -> list:
    """Return ordered list of pain-point bullets for this prospect."""
    out = []
    seen = set()

    def _add(text):
        key = text[:60]
        if key in seen:
            return
        seen.add(key)
        out.append(text)

    # Incumbent-vendor pain (top of list)
    if incumbent_vendor and incumbent_vendor in PAIN_POINTS_BY_INCUMBENT:
        for p in PAIN_POINTS_BY_INCUMBENT[incumbent_vendor][:3]:
            _add(p)
    elif not incumbent_vendor:
        for p in PAIN_POINTS_GREENFIELD[:2]:
            _add(p)

    # Signal-type pain
    if signal_type and signal_type in PAIN_POINTS_BY_SIGNAL:
        for p in PAIN_POINTS_BY_SIGNAL[signal_type][:2]:
            _add(p)

    # Bucket pain
    if bucket and bucket in PAIN_POINTS_BY_BUCKET:
        for p in PAIN_POINTS_BY_BUCKET[bucket][:1]:
            _add(p)

    return out[:5]


def recommended_approach(signal_type: Optional[str],
                          persona: Optional[str],
                          state: Optional[str],
                          bucket: Optional[str],
                          incumbent: Optional[str],
                          deadline: Optional[str],
                          detail: Optional[str],
                          nearby_customer: Optional[str] = None) -> str:
    """Render the recommended-approach text by filling the template."""
    template = APPROACH_BY_SIGNAL.get(signal_type, APPROACH_BY_SIGNAL["intent"])
    detail_short = (detail or "")[:90]
    if not nearby_customer:
        candidates = NEARBY_CUSTOMERS_BY_STATE.get(state or "", [])
        nearby_customer = candidates[0] if candidates else "a comparable muni"
    return template.format(
        persona=persona or "primary buyer",
        state=state or "the region",
        bucket=bucket or "similar-size",
        incumbent=incumbent or "their current vendor",
        deadline=deadline or "the upcoming",
        deadline_short=deadline or "upcoming deadline",
        detail_short=detail_short,
        nearby_customer=nearby_customer,
    )


def primary_persona(bucket: Optional[str], product: Optional[str] = None,
                     entity_type: str = "muni") -> str:
    """Primary buyer title for this entity / size / product."""
    from personas import personas_for
    titles = personas_for(entity_type, bucket, product)
    return titles[0][0] if titles else "Finance Director"


if __name__ == "__main__":
    pp = pain_points_for("Caselle", "5K-10K", "intent")
    print("Caselle 5K-10K intent pain points:")
    for p in pp:
        print(" -", p)
    print()
    ra = recommended_approach(
        "intent", "Finance Director", "NY", "5K-10K", "Caselle",
        None, "council motion to issue RFP for new financial system",
        nearby_customer="Belfast ME")
    print("Recommended approach:")
    print(" ", ra)
