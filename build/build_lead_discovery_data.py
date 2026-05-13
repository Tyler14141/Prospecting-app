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

from greenfield import build_indices, score_muni
from lead_discovery import (pain_points_for, recommended_approach,
                              primary_persona)
from pricing import acv_for
from signals import SIGNALS, SIGNAL_TYPES, signal_score, TODAY


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "TAM", "lead_discovery_data.json"))


def build():
    # Pre-compute greenfield score per muni so we can attach it
    indices = build_indices()

    leads = []
    for s in SIGNALS:
        score = signal_score(s, TODAY)
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
        sig_type = s["type"]
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
        print(f"    {r['signal_score']:>5.2f}  {r['muni']:18s} "
              f"{r['state']}  pop={r['population']:>6,}  "
              f"{r['signal_label']:18s}  inc={inc}")


if __name__ == "__main__":
    build()
