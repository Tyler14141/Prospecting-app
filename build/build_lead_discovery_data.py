"""
Bake lead_discovery_data.json for the dashboard.

For each active signal, produces a "lead card" record with:
  - Muni / state / pop / bucket / incumbent / ACV
  - Pain Points (from lead_discovery.pain_points_for)
  - Recommended Approach (from lead_discovery.recommended_approach)
  - Greenfield score + components (from greenfield_data.json if present)
"""

import json
import os
import csv
import hashlib

from greenfield import build_indices, score_muni
from lead_discovery import (pain_points_for, recommended_approach,
                              primary_persona)
from pricing import acv_for
from signals import SIGNALS, SIGNAL_TYPES, signal_score, TODAY
from verified_signals import VERIFIED_SIGNALS_CSV, load_verified_signals


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "TAM", "lead_discovery_data.json"))
HARVESTED_PATH = os.path.join(HERE, "harvested_signals.json")
DNS_HITS_PATH = os.path.join(HERE, "dns_strict_hits.csv")


def _load_harvested_signals():
    """Pull in harvested intent signals from full_state_dive.py output, if
    present. Format mirrors signals.SIGNALS so it concatenates cleanly."""
    if not os.path.exists(HARVESTED_PATH):
        return []
    with open(HARVESTED_PATH) as f:
        d = json.load(f)
    return d.get("signals", [])


def _safe_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _dns_signal_id(row):
    seed = "|".join([
        str(row.get("vendor", "")).strip(),
        str(row.get("muni", "")).strip(),
        str(row.get("state", "")).strip().upper(),
        str(row.get("product", "")).strip(),
        str(row.get("source", "")).strip(),
    ]).encode("utf-8")
    return "dns_" + hashlib.sha1(seed).hexdigest()[:12]


def _load_dns_signals(csv_path):
    if not os.path.exists(csv_path):
        return []
    out = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            muni = str(row.get("muni", "")).strip()
            state = str(row.get("state", "")).strip().upper()
            vendor = str(row.get("vendor", "")).strip()
            if not muni or len(state) != 2:
                continue
            bucket = str(row.get("bucket", "")).strip() or None
            population = _safe_int(row.get("pop"))
            try:
                confidence = float(row.get("confidence") or 0)
            except Exception:
                confidence = 0.0
            severity = "high" if confidence >= 0.95 else "medium" if confidence >= 0.85 else "low"
            product = str(row.get("product", "")).strip()
            evidence = str(row.get("evidence", "")).strip()
            if not evidence:
                evidence = f"Public-source incumbent footprint for {vendor or 'known vendor'}"
            source = str(row.get("source", "")).strip() or "dns_strict"
            headline = f"Incumbent footprint: {vendor}" if vendor else "Incumbent footprint confirmed"
            if product:
                headline += f" ({product})"
            out.append({
                "id": _dns_signal_id(row),
                "muni": muni,
                "state": state,
                "population": population,
                "bucket": bucket,
                "type": "installed_base",
                "severity": severity,
                "detected": TODAY.isoformat(),
                "expires": None,
                "headline": headline,
                "details": evidence,
                "source": source,
                "url": None,
                "incumbent": vendor or None,
                "demo": False,
            })
    return out


def build():
    # Pre-compute greenfield score per muni so we can attach it
    indices = build_indices()

    # Real-leads-only: skip anything flagged `demo: True`. The seeded
    # signals in signals.SIGNALS are all demo entries and shouldn't
    # appear as "leads to call" — only signals harvested from real
    # data sources (full_state_dive.py, customer_intel connectors, RFP
    # awards scraper) should populate the Lead Discovery feed.
    harvested = _load_harvested_signals()
    verified = load_verified_signals(VERIFIED_SIGNALS_CSV)
    dns_signals = _load_dns_signals(DNS_HITS_PATH)
    real_seed = [s for s in SIGNALS if not s.get("demo", True)]
    all_signals = real_seed + list(harvested) + list(verified) + list(dns_signals)
    print(f"  seeded real (non-demo) signals: {len(real_seed)}")
    print(f"  harvested signals from {HARVESTED_PATH}: {len(harvested)}")
    print(f"  verified signals from {VERIFIED_SIGNALS_CSV}: {len(verified)}")
    print(f"  incumbent footprints from {DNS_HITS_PATH}: {len(dns_signals)}")
    if not all_signals:
        print(f"  WARNING: no real leads available — Lead Discovery feed will be empty.")
        print(f"  Run `python3 full_state_dive.py` to harvest real intent signals")
        print(f"  from council meeting minutes across NY/PA/ME/OH.")

    leads = []
    for s in all_signals:
        sig_type = s.get("type", "rfp")
        score_input = s
        if sig_type not in SIGNAL_TYPES:
            # Harvested pipelines may emit auxiliary types (e.g. "intent").
            # Score them using the nearest actionable category weight.
            score_input = {**s, "type": "leadership"}
        score = signal_score(score_input, TODAY)
        if score <= 0:
            continue
        # Skip non-muni / statewide signals — they don't represent a single
        # account to call. We'll still surface compliance / vendor EOL via
        # the existing signals tab and use them in scoring.
        if s["state"] == "ALL" or s["muni"].lower().startswith(
                ("statewide", "vendor-wide", "all states")):
            continue

        muni = s["muni"]
        state = s["state"]
        bucket = s.get("bucket")
        incumbent = s.get("incumbent")
        type_meta = SIGNAL_TYPES.get(sig_type, {})

        # ACV estimate
        acv = acv_for(bucket, incumbent, None)

        # Pain points & recommended approach
        pp = pain_points_for(incumbent, bucket, sig_type)
        persona = primary_persona(bucket, None)
        ra = recommended_approach(
            sig_type, persona, state, bucket, incumbent,
            s.get("expires"), s.get("headline"),
            nearby_customer=None,
        )

        # Greenfield score components
        try:
            gf = score_muni(muni, state, s.get("population"), bucket,
                             indices)
            score_components = gf["components"]
            total_score = gf["score"]
        except Exception:
            score_components = None
            total_score = None

        leads.append({
            "lead_id": s["id"],
            "muni": muni,
            "state": state,
            "population": s.get("population"),
            "bucket": bucket,
            "type": "muni",
            "incumbent": (
                {"vendor": incumbent} if incumbent else None
            ),
            "signal_type": sig_type,
            "signal_label": type_meta.get("label", sig_type),
            "signal_color": type_meta.get("color", "#94a3b8"),
            "signal_score": score,
            "severity": s.get("severity"),
            "detected": s.get("detected"),
            "expires": s.get("expires"),
            "headline": s.get("headline"),
            "details": s.get("details"),
            "source": s.get("source"),
            "acv": acv,
            "primary_buyer": persona,
            "pain_points": pp,
            "recommended_approach": ra,
            "greenfield_score": total_score,
            "score_components": score_components,
        })

    # Sort by signal_score desc
    leads.sort(key=lambda r: -r["signal_score"])

    payload = {
        "today": TODAY.isoformat(),
        "leads": leads,
        "signal_type_meta": SIGNAL_TYPES,
        "total_leads": len(leads),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {OUT} ({os.path.getsize(OUT)/1024:.1f} KB)")
    print(f"  {len(leads)} leads baked")
    # Top 5
    print("  top 5 by signal score:")
    for r in leads[:5]:
        inc = r["incumbent"]["vendor"] if r["incumbent"] else "GREENFIELD"
        pop = r.get("population")
        pop_disp = f"{pop:>6,}" if isinstance(pop, int) else "  n/a"
        print(f"    {r['signal_score']:>5.2f}  {r['muni']:18s} "
              f"{r['state']}  pop={pop_disp}  "
              f"{r['signal_label']:18s}  inc={inc}")


if __name__ == "__main__":
    build()
