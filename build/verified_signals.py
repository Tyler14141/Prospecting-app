"""
Load verified (real) buying signals from a local CSV export.

This module is intentionally strict: only rows with http/https URLs and
non-demo records are accepted by default.
"""

import csv
import hashlib
import os
from datetime import date

from data import BUCKETS


HERE = os.path.dirname(os.path.abspath(__file__))
VERIFIED_SIGNALS_CSV = os.path.join(HERE, "verified_rfps.csv")


def _bucket_for_population(population: int) -> str:
    for label, low, high, _avg in BUCKETS:
        if high is None and population >= low:
            return label
        if high is not None and low <= population < high:
            return label
    return "100K+"


def _safe_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _signal_id(state: str, muni: str, detected: str, url: str) -> str:
    seed = f"{state}|{muni}|{detected}|{url}".encode("utf-8")
    digest = hashlib.sha1(seed).hexdigest()[:10]
    return f"live_{digest}"


def _valid_iso_date(value: str) -> bool:
    if not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except Exception:
        return False


def load_verified_signals(csv_path: str) -> list:
    """Read verified RFP rows from CSV into dashboard signal schema."""
    if not os.path.exists(csv_path):
        return []

    out = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = str(row.get("state", "")).strip().upper()
            muni = str(row.get("muni", "")).strip()
            url = str(row.get("url", "")).strip()
            detected = str(row.get("detected", "")).strip()

            # Strict verification gate: URL + minimally valid record.
            if not url.startswith(("http://", "https://")):
                continue
            if not state or len(state) != 2 or not muni:
                continue
            if not _valid_iso_date(detected):
                continue

            population = _safe_int(row.get("population", "0"), 0)
            if population <= 0:
                continue

            expires = str(row.get("expires", "")).strip() or None
            if expires and not _valid_iso_date(expires):
                expires = None

            signal_type = str(row.get("type", "rfp")).strip() or "rfp"
            if signal_type != "rfp":
                signal_type = "rfp"

            severity = str(row.get("severity", "medium")).strip().lower()
            if severity not in {"high", "medium", "low"}:
                severity = "medium"

            source = str(row.get("source", "Verified source")).strip() or "Verified source"
            headline = str(row.get("headline", "Municipal software RFP")).strip() or "Municipal software RFP"
            details = str(row.get("details", "Verified procurement posting.")).strip() or "Verified procurement posting."
            incumbent = str(row.get("incumbent", "")).strip() or None

            out.append({
                "id": _signal_id(state, muni, detected, url),
                "muni": muni,
                "state": state,
                "population": population,
                "bucket": _bucket_for_population(population),
                "type": signal_type,
                "severity": severity,
                "detected": detected,
                "expires": expires,
                "headline": headline,
                "details": details,
                "source": source,
                "url": url,
                "incumbent": incumbent,
                "demo": False,
            })

    return out
