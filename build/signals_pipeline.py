"""
Connector stubs for live buying-signal sources.

Each connector follows the same contract:

    def fetch_<source>(config: dict, since: date) -> list[Signal]

Where Signal is a dict with these keys (matching signals.SIGNALS schema):

    id, muni, state, population, bucket, type, severity,
    detected (ISO date str), expires (ISO date str or None),
    headline, details, source, url, incumbent, demo (False once live)

Wire-up checklist:

  1. Pick a connector below.
  2. Read the SOURCE_HINTS docstring — it lists the API/feed endpoint,
     auth model, recommended polling cadence, and a parsing skeleton.
  3. Implement the fetch function. Keep `demo=False` once it's live.
  4. Add the connector to `run_all()` at the bottom of this file.
  5. Schedule via cron / GitHub Actions / your task runner. Recommend
     hourly for RFPs, daily for leadership/cyber/bond, weekly for audit
     and vendor_eol.

# refreshed 2026-05-01
"""

from datetime import date, timedelta


# ============================================================================
# RFP feeds — highest signal density, the keystone source for outbound.
# ============================================================================

def fetch_rfps_bidnet(config, since):
    """
    SOURCE_HINTS:
      Endpoint: https://www.bidnetdirect.com/  (login + saved-search export)
      Auth: Username + password; saved searches export to email/CSV.
      Cadence: Hourly during business days.
      Filter strategy: Keyword sets per product line:
         ERP: 'enterprise resource planning', 'financial management',
              'general ledger', 'fund accounting'
         Utility billing: 'utility billing', 'water billing', 'meter reading'
         Permitting: 'permitting', 'building department', 'code enforcement'
         GIS: 'GIS', 'mapping system'
      Parsing skeleton:
         row -> {
           "muni": row["agency_name"],
           "state": row["state_code"],
           "type": "rfp",
           "severity": "high" if row["estimated_value"] >= 50_000 else "medium",
           "detected": row["posted_date"],
           "expires": row["due_date"],
           "headline": row["title"],
           "details": row["description"][:200],
           "source": "BidNet Direct",
           "url": row["solicitation_url"],
         }
    """
    raise NotImplementedError("Wire to BidNet saved-search export")


def fetch_rfps_demandstar(config, since):
    """
    SOURCE_HINTS:
      Endpoint: https://www.demandstar.com/  (subscription + API addon)
      Auth: API key (paid tier).
      Cadence: Hourly. Demandstar has tighter coverage in NE/MW/SE munis.
      Notes: Many small munis ONLY post here — complementary to BidNet.
    """
    raise NotImplementedError("Wire to Demandstar API")


def fetch_rfps_periscope(config, since):
    """
    SOURCE_HINTS:
      Endpoint: https://www.periscopeholdings.com/ / Bonfire portal.
      Auth: Vendor account (free for response, paid for early notification).
      Cadence: Daily.
    """
    raise NotImplementedError("Wire to Periscope/Bonfire feed")


def fetch_rfps_govwin(config, since):
    """
    SOURCE_HINTS:
      Endpoint: GovWin IQ (Deltek). Pre-RFP intelligence — highest value.
      Auth: Paid subscription, ~$15K/year.
      Cadence: Daily.
      Notes: Captures RFP-pre-release activity (forecasted opportunities,
             agency budgets). Best ROI for small-muni outbound if budget
             allows.
    """
    raise NotImplementedError("Wire to GovWin IQ API")


# ============================================================================
# Leadership change — proxies new-decision-maker buying windows.
# ============================================================================

def fetch_leadership_linkedin(config, since):
    """
    SOURCE_HINTS:
      Endpoint: LinkedIn Sales Navigator saved search export.
      Filter: title in {Finance Director, City Manager, IT Director, CIO,
              CFO, City Clerk, Town Manager, Village Administrator},
              location = your target states,
              tenure < 6 months,
              employer keywords: "city of", "county of", "town of", "village of".
      Cadence: Daily.
      Auth: Sales Nav account ($99/seat/month).
      Parsing: profile.recent_role.start_date < since to flag new hires.
      Severity heuristic:
         high   = Finance Director or CFO (controls software budget)
         medium = City Manager or CIO
         low    = Clerk-level
    """
    raise NotImplementedError("Wire to LinkedIn Sales Nav export")


def fetch_leadership_municode_press(config, since):
    """
    SOURCE_HINTS:
      Endpoint: Aggregate of city-press-release RSS feeds.
      Approach: maintain a list of muni RSS endpoints; parse for keywords
                like 'appoints', 'hires', 'new finance director'.
      Cadence: Daily. Lower precision than LinkedIn but free.
    """
    raise NotImplementedError("Wire to muni RSS aggregator")


# ============================================================================
# Cyber incidents — forces cloud / SaaS migration discussions.
# ============================================================================

def fetch_cyber_msisac(config, since):
    """
    SOURCE_HINTS:
      Endpoint: MS-ISAC member portal alerts (Center for Internet Security).
      Auth: MS-ISAC membership (free for state/local govt; vendors require
            partnership). Many incidents are member-only — partner with a
            customer or rely on news scraping.
      Cadence: Daily.
    """
    raise NotImplementedError("Wire to MS-ISAC alerts (or news scraper)")


def fetch_cyber_state_breach_registries(config, since):
    """
    SOURCE_HINTS:
      Endpoint: State AG breach-notification portals. Public.
        - CA: https://oag.ca.gov/privacy/databreach/list
        - NY: https://ag.ny.gov/internet/data-breach
        - WA: https://www.atg.wa.gov/data-breach-notifications
        - MA, IL, TX: similar.
      Cadence: Daily.
      Filter: organization_type contains 'city', 'county', 'town', 'village',
              'school district' (exclude SD if out-of-scope).
    """
    raise NotImplementedError("Wire to state AG breach-registry scrapers")


def fetch_cyber_news(config, since):
    """
    SOURCE_HINTS:
      Endpoint: Google News API / NewsAPI / Mediastack with query:
                ('city of' OR 'county of' OR 'township of') AND
                ('ransomware' OR 'cyberattack' OR 'data breach' OR
                 'network outage').
      Cadence: Hourly.
      Notes: Lower-precision than registries; use NER to extract muni name.
    """
    raise NotImplementedError("Wire to news API + NER pipeline")


# ============================================================================
# Bond issuances — proxies capex headroom.
# ============================================================================

def fetch_bonds_emma(config, since):
    """
    SOURCE_HINTS:
      Endpoint: MSRB EMMA https://emma.msrb.org/  (free, public).
      Bulk download: https://emma.msrb.org/Datafeed/Index/  (dataset access).
      Cadence: Weekly.
      Filter strategy:
        - issue_type in ('GO bond', 'revenue bond', 'COP')
        - issuer_type in ('city', 'county', 'town', 'village', 'township')
        - keyword search of OS docs for 'enterprise resource planning',
          'financial management system', 'IT modernization', 'software'
      Severity:
        high   = OS docs explicitly mention software/ERP capex
        medium = capex bond with discretionary IT line item
        low    = general operating bond
    """
    raise NotImplementedError("Wire to EMMA dataset feed + OS doc parser")


# ============================================================================
# Compliance deadlines — schedule-driven, not event-driven.
# ============================================================================

def fetch_compliance_deadlines(config, since):
    """
    SOURCE_HINTS:
      Maintain a curated list of state + federal mandates:
        - GASB pronouncements (87 leases, 96 SBITAs, 99-103 followups)
        - State cybersecurity acts (TX SB820, OH HB23, NC HB199, etc.)
        - State data-protection laws (CA, NY, IL, MA)
        - Federal: CISA cyber incident reporting (CIRCIA), HIPAA refreshes.
      Cadence: Quarterly review; quarterly add new mandates.
      Severity: align with deadline proximity (high if <6mo, medium if <12mo).
    """
    raise NotImplementedError("Maintain a curated compliance YAML; load here")


# ============================================================================
# Vendor EOL / M&A — competitor watch.
# ============================================================================

def fetch_vendor_intel(config, since):
    """
    SOURCE_HINTS:
      Composite of:
        - Competitor SEC filings (Tyler 10-Q, 10-K — public).
        - Competitor press releases / blog (RSS).
        - SaaSBase / G2 changelog of vendor pricing.
        - Customer-review-site complaints (G2, Capterra) — sentiment shifts.
      Cadence: Weekly.
      Severity:
        high   = announced product line EOL
        medium = pricing model change, M&A integration friction
        low    = roadmap slippage, executive change
    """
    raise NotImplementedError("Curate competitor watch list + RSS pipe")


# ============================================================================
# Audit findings — forces remediation, often via new vendor.
# ============================================================================

def fetch_audit_findings(config, since):
    """
    SOURCE_HINTS:
      Endpoint: State auditor/comptroller websites (per state, public).
      Cadence: Monthly.
      Filter: report_type in ('material weakness', 'significant deficiency',
              'finding') AND keyword in ('financial system', 'reconciliation',
              'general ledger', 'IT controls').
    """
    raise NotImplementedError("Per-state auditor scrapers")


# ============================================================================
# Aggregator
# ============================================================================

def run_all(config: dict, since: date | None = None) -> list:
    """Pull all sources, dedupe by id, return chronological list."""
    if since is None:
        since = date.today() - timedelta(days=30)

    out = []
    for fetcher in (
        fetch_rfps_bidnet,
        fetch_rfps_demandstar,
        fetch_rfps_periscope,
        fetch_rfps_govwin,
        fetch_leadership_linkedin,
        fetch_leadership_municode_press,
        fetch_cyber_msisac,
        fetch_cyber_state_breach_registries,
        fetch_cyber_news,
        fetch_bonds_emma,
        fetch_compliance_deadlines,
        fetch_vendor_intel,
        fetch_audit_findings,
    ):
        try:
            out.extend(fetcher(config, since))
        except NotImplementedError:
            pass  # not yet wired; skip silently
        except Exception as e:
            print(f"connector {fetcher.__name__} failed: {e}")

    # Dedupe by id (last-write wins)
    by_id = {s["id"]: s for s in out}
    return sorted(by_id.values(), key=lambda s: s["detected"], reverse=True)


if __name__ == "__main__":
    print("Connectors registered:")
    print("  RFPs:        bidnet, demandstar, periscope, govwin")
    print("  Leadership:  linkedin, municode_press")
    print("  Cyber:       msisac, state_breach_registries, news")
    print("  Bonds:       emma")
    print("  Compliance:  curated_list")
    print("  Vendor EOL:  competitor_watch")
    print("  Audit:       per_state_auditors")
    print()
    print("All currently raise NotImplementedError. Wire one at a time.")
    print("See each connector's SOURCE_HINTS docstring.")
