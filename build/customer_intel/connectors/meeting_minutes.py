"""
Council / board meeting-minutes connector.

The highest-precision free source for vendor + dollar + date confirmation.
Council minutes record motions to approve contracts in plain language:

    "Motion to approve a 5-year agreement with Tyler Technologies for
     financial management software in the amount of $185,000 annually."

That single sentence gives us: vendor, product class, contract length,
ACV, and (combined with the meeting date) the contract start year. Plus
the council members who voted on it (names → contacts → outbound).

Pipeline
--------
For each muni:
  1. Discover the meetings/agendas index page (try ~12 common paths)
  2. Extract links to recent minute PDFs (last 24 months by default)
  3. Download each PDF (capped at MAX_PDFS_PER_MUNI = 12)
  4. Extract text via pdfplumber / pypdf / pdftotext fallback
  5. Pattern-match for vendor approvals + buying signals
  6. Output customer records and (optional) signal records

Coverage
--------
Smaller munis usually publish minutes in PDF format on a clerk page.
~70-85% of munis have a public minutes archive. Of those, vendor
approvals appear in 20-40% of any given 6-month window (most munis
make ~1 software-related decision per year). So combined recall
across recent minutes is solid.

Tradeoffs vs. other connectors:
  + Highest precision (verbatim quote with $ amount and date)
  + Picks up replaced incumbents, not just current
  + Captures vote rosters → council member names for outbound
  - Slowest connector by ~10x (PDF download + text extraction)
  - Per-muni: 30-90s; budget 1-3 hours per 1000 munis at 20 threads

Run
---
    python -m customer_intel.connectors.meeting_minutes --top-prospects
    python -m customer_intel.connectors.meeting_minutes --states IA NE KS --threads 20
    python -m customer_intel.connectors.meeting_minutes --top 100 --max-pdfs 8
"""

import argparse
import concurrent.futures as cf
import csv
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "customer-intel-minutes/0.1 (https://example.com/bot)"

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAMES_PATH = os.path.join(HERE, "names_data.json")
GREENFIELD_PATH = os.path.normpath(os.path.join(
    HERE, "..", "TAM", "greenfield_data.json"))


# ---- Discovery patterns --------------------------------------------------

# Likely paths under a muni root that index meeting minutes
MEETINGS_PATHS = [
    "/agendas", "/meetings", "/minutes", "/clerk", "/clerk/meetings",
    "/clerk/minutes", "/board-of-trustees", "/city-council",
    "/council", "/council/agendas", "/council/minutes",
    "/government/city-council", "/government/agendas-and-minutes",
    "/agenda-center", "/AgendaCenter",
]

# Same URL discovery patterns we use in muni_website
URL_PATTERNS = [
    "https://www.cityof{slug}.gov", "https://cityof{slug}.gov",
    "https://www.cityof{slug}.org", "https://cityof{slug}.org",
    "https://www.cityof{slug}.com",
    "https://www.{slug}.gov", "https://{slug}.gov",
    "https://www.{slug}{st}.gov", "https://{slug}{st}.gov",
    "https://www.{slug}-{st}.gov", "https://www.{slug}.{st}.gov",
    "https://www.townof{slug}.gov", "https://townof{slug}.org",
    "https://www.villageof{slug}.gov",
    "https://www.{slug}.us", "https://www.{slug}.org", "https://{slug}.org",
]


# ---- Extraction patterns -------------------------------------------------

# Vendor name detection in minutes text
VENDOR_PATTERNS = [
    (re.compile(r"Tyler\s+Technolog(?:y|ies)(?:,?\s*Inc\.?)?", re.I), "Tyler Technologies"),
    (re.compile(r"\bMUNIS\b"),                                        "Tyler Technologies"),
    (re.compile(r"New\s+World\s+Systems",                       re.I), "Tyler Technologies"),
    (re.compile(r"EnerGov",                                     re.I), "Tyler Technologies"),
    (re.compile(r"BS\s*&?\s*A\s+Software(?:,?\s*Inc\.?)?",      re.I), "BS&A Software"),
    (re.compile(r"\bBS\s*&\s*A\b"),                                   "BS&A Software"),
    (re.compile(r"Caselle(?:,?\s*Inc\.?)?",                     re.I), "Caselle"),
    (re.compile(r"\bgWorks\b"),                                       "gWorks"),
    (re.compile(r"Banyon\s+Data\s+Systems",                     re.I), "gWorks"),
    (re.compile(r"Pontem\s+Software",                            re.I), "gWorks"),
    (re.compile(r"Muni-?Link",                                  re.I), "Muni-Link"),
    (re.compile(r"TownCloud",                                   re.I), "TownCloud"),
]

# Vendor -> product hint when a generic vendor name is mentioned
VENDOR_DEFAULT_PRODUCT = {
    "Tyler Technologies": "Munis ERP",
    "BS&A Software":      "Financial Mgmt",
    "Caselle":            "Caselle Connect",
    "gWorks":             "gWorks Suite",
    "Muni-Link":          "Utility Billing",
    "TownCloud":          "TownCloud Suite",
}

# Motion / approval / award patterns. Match a sentence-sized window
# around the verb. Used to find the specific vendor approval.
APPROVAL_PHRASES = [
    re.compile(r"motion\s+to\s+approve",                        re.I),
    re.compile(r"award(?:ed)?\s+(?:of\s+)?(?:the\s+)?contract", re.I),
    re.compile(r"authoriz(?:e|ed)\s+(?:the\s+)?(?:city|town|village)\s+(?:manager|administrator|clerk)", re.I),
    re.compile(r"approv(?:al|e|ed)\s+(?:of\s+)?(?:the\s+)?(?:contract|agreement|professional\s+services)", re.I),
    re.compile(r"(?:execute|enter\s+into)\s+(?:a\s+)?contract\s+with",  re.I),
    re.compile(r"renewal\s+of\s+(?:the\s+)?(?:license|maintenance|software)\s+agreement", re.I),
    re.compile(r"software\s+(?:license|maintenance|subscription)\s+agreement", re.I),
    re.compile(r"recommendation\s+to\s+award",                    re.I),
    re.compile(r"RFP\s+(?:no\.?\s+)?\d+(?:[-/]\d+)?\s+(?:was\s+)?awarded\s+to", re.I),
]

# Dollar-amount extraction
DOLLAR_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|M|thousand|K)?", re.I)

# Date extraction (2020-2030 era)
DATE_RE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+(20\d{2})", re.I)

YEAR_ONLY_RE = re.compile(r"\b(20\d{2})\b")

# Buying-signal patterns (separate from incumbent confirmations).
# These extract one signal per pattern-match per PDF. The intent
# patterns are the highest-value: they catch pre-RFP buying intent
# in meeting minutes BEFORE the public RFP is issued.
SIGNAL_PHRASES = [
    # ===== INTENT — pre-RFP buying intent (highest value) =====
    # Each pattern is independently triggerable. We don't require a
    # leading "decision verb" because the trigger phrase itself
    # (motion to issue RFP, modernization study, scope of work for
    # ERP RFP, capital budget for software, etc.) is enough evidence.

    # Motion to issue RFP
    (re.compile(
        r"(?:motion|approv\w*|authoriz\w*|direct\w*|vote[d]?)"
        r"[\s\S]{0,120}?"
        r"issue\s+(?:an?\s+)?(?:RFP|RFI|request\s+for\s+proposal|request\s+for\s+information)",
        re.I), "intent"),
    # Issue RFP (without preceding verb — still strong signal)
    (re.compile(
        r"(?:issue|will\s+issue|to\s+issue)\s+(?:an?\s+)?"
        r"(?:RFP|RFI|request\s+for\s+proposal)\s+for\s+"
        r"(?:ERP|software|financial|IT|technology|utility\s+billing|permitting)",
        re.I), "intent"),
    # Selection committee
    (re.compile(
        r"(?:authoriz\w*|approv\w*|establish\w*|form\w*|create\w*|direct\w*)"
        r"[\s\S]{0,80}?(?:technology|ERP|software|IT|vendor)\s+"
        r"(?:selection\s+)?committee",
        re.I), "intent"),
    # Modernization / assessment / feasibility study
    (re.compile(
        r"(?:motion|approv\w*|authoriz\w*|commission\w*|conduct\w*|undertake)"
        r"[\s\S]{0,80}?"
        r"(?:technology|modernization|assessment|feasibility|ERP)\s+study",
        re.I), "intent"),
    # Modernization study standalone (no verb required)
    (re.compile(
        r"(?:technology|modernization|ERP)\s+study\s+"
        r"(?:to\s+commence|will\s+commence|will\s+begin)",
        re.I), "intent"),
    # Reserve fund / budget for software
    (re.compile(
        r"(?:establish\w*|approv\w*|create\w*|set\s+aside|design\w*)"
        r"[\s\S]{0,60}?"
        r"(?:reserve|fund|budget\s+line\s+item|appropriation|allocation)"
        r"[\s\S]{0,60}?"
        r"(?:software|ERP|financial\s+system|technology|IT\s+modernization)",
        re.I), "intent"),
    # Capital budget / appropriation $X for ERP/software
    (re.compile(
        r"capital\s+(?:budget|appropriation|line\s+item)"
        r"[\s\S]{0,60}?\$[\d,]+"
        r"[\s\S]{0,40}?(?:ERP|software|financial|IT|technology|modernization)",
        re.I), "intent"),
    # Scope of work for ERP RFP
    (re.compile(
        r"scope\s+of\s+work"
        r"[\s\S]{0,80}?(?:ERP|RFP|software|financial|IT)",
        re.I), "intent"),
    # Vendor presentation received
    (re.compile(
        r"(?:received?|heard)\s+(?:a\s+|the\s+)?(?:vendor\s+|sales\s+|product\s+)?"
        r"presentation\s+(?:from|by)\s+([A-Z][A-Za-z&\.\-' ]{2,40})",
        re.I), "intent"),
    # Non-renewal / contract termination
    (re.compile(
        r"(?:non[-\s]renewal\s+(?:notice|letter)|"
        r"(?:terminate|end|discontinue|cancel)\s+(?:the\s+|our\s+|current\s+)?"
        r"(?:contract|agreement)\s+with\s+[A-Z])",
        re.I), "intent"),
    # Discussion of replacement/modernization (intent — not vendor EOL)
    (re.compile(
        r"(?:discuss\w*|consider\w*|evaluat\w*|explor\w*)"
        r"[\s\S]{0,40}?"
        r"(?:replacing|modernizing|upgrading|replacement\s+of)"
        r"[\s\S]{0,40}?"
        r"(?:financial|ERP|software|system|billing|permitting|vendor|tax)",
        re.I), "intent"),

    # ===== RFP committee / formal process =====
    (re.compile(r"RFP\s+committee", re.I),                    "rfp"),
    (re.compile(r"request\s+for\s+proposal\s+(?:was\s+)?(?:issued|published|posted)",
                 re.I), "rfp"),

    # ===== Vendor EOL / replacement =====
    (re.compile(r"replac(?:e|ement|ing)\s+(?:our|the)\s+(?:current|existing)?\s*"
                 r"(?:legacy\s+)?(?:financial|ERP|software|system|vendor)",
                 re.I), "vendor_eol"),
    (re.compile(r"end\s+of\s+life|sunsetting?|EOL\s+notice", re.I), "vendor_eol"),

    # ===== Cyber =====
    (re.compile(r"cyber(?:\s*security)?\s+incident", re.I),    "cyber"),
    (re.compile(r"(?:ransomware|data\s+breach|network\s+intrusion)", re.I),
     "cyber"),

    # ===== Leadership =====
    (re.compile(r"appoint(?:ed|ing)?\s+(?:a\s+)?new\s+"
                 r"(?:finance\s+director|city\s+manager|town\s+manager|"
                 r"administrator|CFO|CIO|IT\s+director|clerk-?treasurer)",
                 re.I), "leadership"),
    (re.compile(r"welcome\s+(?:our\s+)?new\s+(?:finance\s+director|CFO|CIO)",
                 re.I), "leadership"),

    # ===== Audit =====
    (re.compile(r"audit\s+(?:finding|deficienc|material\s+weakness)", re.I),
     "audit"),
    (re.compile(r"(?:state|external)\s+auditor\s+(?:identified|cited|flagged)",
                 re.I), "audit"),

    # ===== Bond / capex =====
    (re.compile(r"(?:GO|general\s+obligation)\s+bond.*(?:software|IT|technology|ERP)",
                 re.I), "bond"),
    (re.compile(r"capital\s+appropriation.*(?:software|IT|ERP)",
                 re.I), "bond"),
]


# Words that indicate the muni is the SUBJECT of the intent (not just
# discussing some other entity). Used to filter out false positives like
# "the State of NY plans to issue an RFP for ..." (not relevant).
INTENT_QUALIFIERS = re.compile(
    r"\b(?:city|town|village|borough|township|county|board|council|"
    r"municipal(?:ity)?|administration)\b", re.I)


def slugify(name):
    n = re.sub(r"[^a-z0-9 \-']", "", name.lower())
    n = n.replace("'", "").replace(" ", "").replace("-", "")
    return n


def _today_iso():
    from datetime import date
    return date.today().isoformat()


# ---- HTTP helpers --------------------------------------------------------

def fetch_text(url, timeout=8.0, max_bytes=750_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            return ""
        body = r.read(max_bytes)
        ctype = r.headers.get("Content-Type", "")
        charset = r.headers.get_content_charset() or "utf-8"
        if "html" not in ctype and not ctype.startswith("text/"):
            return ""
        return body.decode(charset, errors="replace")


def fetch_bytes(url, timeout=15.0, max_bytes=8_000_000):
    """Download a binary blob (PDF). Caps at max_bytes."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            return b""
        return r.read(max_bytes)


def discover_url(slug, state, timeout=4.0):
    """Probe URL_PATTERNS until one resolves; return base URL."""
    st = state.lower()
    for pat in URL_PATTERNS:
        url = pat.format(slug=slug, st=st)
        try:
            socket.gethostbyname(urllib.parse.urlparse(url).netloc)
        except socket.gaierror:
            continue
        try:
            req = urllib.request.Request(url, method="HEAD",
                                          headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if 200 <= r.status < 400:
                    return url.rstrip("/")
        except urllib.error.HTTPError as e:
            if e.code in (200, 301, 302, 403):
                return url.rstrip("/")
        except Exception:
            pass
    return None


# ---- Meetings page discovery + PDF link extraction -----------------------

PDF_LINK_RE = re.compile(
    r'href=["\']([^"\']+\.(?:pdf|PDF))(?:["\']|\?)', re.I)


def find_meeting_pdfs(base_url, timeout=8.0, max_pdfs=12):
    """Return list of PDF URLs found by walking the meetings index."""
    pdfs = []
    seen = set()
    for path in MEETINGS_PATHS:
        if len(pdfs) >= max_pdfs:
            break
        index_url = base_url + path
        try:
            html = fetch_text(index_url, timeout=timeout)
        except Exception:
            continue
        if not html:
            continue
        # Find PDF links in the page
        for m in PDF_LINK_RE.finditer(html):
            href = m.group(1)
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = base_url + href
            elif not href.startswith("http"):
                href = base_url + path + "/" + href
            if href in seen:
                continue
            seen.add(href)
            pdfs.append(href)
            if len(pdfs) >= max_pdfs:
                break
    return pdfs


def extract_pdf_text(pdf_bytes):
    """Extract text from a PDF blob. Tries pdfplumber, pypdf, pdftotext."""
    if not pdf_bytes:
        return ""
    # pdfplumber (best quality)
    try:
        import io
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:30]:  # cap at 30 pages
                t = page.extract_text() or ""
                text_parts.append(t)
        return "\n".join(text_parts)
    except ImportError:
        pass
    except Exception:
        pass
    # pypdf
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "")
                          for p in reader.pages[:30])
    except ImportError:
        pass
    except Exception:
        pass
    # pdftotext fallback (system binary)
    try:
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        try:
            r = subprocess.run(["pdftotext", "-layout", tmp_path, "-"],
                                capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                return r.stdout
        finally:
            os.unlink(tmp_path)
    except Exception:
        pass
    return ""


# ---- Pattern extraction --------------------------------------------------

def _amount_to_int(amt_str, suffix):
    n = float(amt_str.replace(",", ""))
    if suffix.lower() in ("million", "m"):
        n *= 1_000_000
    elif suffix.lower() in ("thousand", "k"):
        n *= 1_000
    return int(n)


def extract_approvals(text, source_url):
    """Return list of confirmed customer records found in the text."""
    out = []
    # Find every approval-phrase position; for each, look in a 600-char
    # window for vendor name + dollar amount.
    for ap_pat in APPROVAL_PHRASES:
        for m in ap_pat.finditer(text):
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 600)
            window = text[start:end]
            for v_pat, vendor in VENDOR_PATTERNS:
                vm = v_pat.search(window)
                if not vm:
                    continue
                # Pull dollar amount near the vendor mention
                dm = DOLLAR_RE.search(window)
                amount = None
                if dm:
                    amount = _amount_to_int(dm.group(1), dm.group(2) or "")
                # Pull a year near the approval (often the meeting date)
                year_match = YEAR_ONLY_RE.search(window)
                year = int(year_match.group(1)) if year_match else None
                snippet = re.sub(r"\s+", " ", window).strip()[:240]
                out.append({
                    "vendor": vendor,
                    "product": VENDOR_DEFAULT_PRODUCT.get(vendor),
                    "amount": amount,
                    "since": year,
                    "snippet": snippet,
                    "source_url": source_url,
                    "confidence": 0.97 if amount else 0.88,
                })
                break  # one vendor per approval mention
    # Dedupe within this PDF — same (vendor, amount) might be repeated
    seen = set()
    deduped = []
    for r in out:
        k = (r["vendor"], r["amount"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)
    return deduped


def extract_signals(text, source_url):
    """Return list of buying-signal records found in the text. Each
    record carries a verbatim snippet with ~250 chars of context, which
    is what gets surfaced in the Lead Discovery card. Intent signals
    include a meeting date if extractable."""
    out = []
    seen = set()
    for sig_pat, sig_type in SIGNAL_PHRASES:
        for m in sig_pat.finditer(text):
            if sig_type in seen:
                break
            seen.add(sig_type)
            # Wider context window for intent signals (the language matters)
            window = 250 if sig_type == "intent" else 180
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + window)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            # Intent signals: confirm the muni (not some other entity) is
            # the subject. Reject if no muni qualifier appears in window.
            if sig_type == "intent" and not INTENT_QUALIFIERS.search(snippet):
                continue
            # Try to extract a meeting date
            date_m = DATE_RE.search(snippet) or YEAR_ONLY_RE.search(snippet)
            meeting_date = None
            if date_m:
                try:
                    meeting_date = date_m.group(0)
                except IndexError:
                    pass
            out.append({
                "type": sig_type,
                "snippet": snippet,
                "meeting_date": meeting_date,
                "source_url": source_url,
                "headline": _headline_for_intent(snippet, sig_type),
                "severity": _severity_for(sig_type, snippet),
            })
            break  # one signal of each type per PDF is enough
    return out


def _headline_for_intent(snippet, sig_type):
    """Build a short, sales-friendly headline from a signal snippet."""
    if sig_type == "intent":
        # Pick the verbiest fragment around 'motion to ...' or 'authoriz...'
        m = re.search(r"motion\s+to\s+\w[\w\s\-]{4,80}", snippet, re.I)
        if m:
            h = m.group(0).strip()
            return h[:90] + ("..." if len(h) > 90 else "")
        m = re.search(r"authoriz\w+\s+\w[\w\s\-]{4,80}", snippet, re.I)
        if m:
            return m.group(0).strip()[:90]
        m = re.search(r"establish(?:ed|ing)?\s+\w[\w\s\-]{4,80}", snippet, re.I)
        if m:
            return m.group(0).strip()[:90]
        return "Pre-RFP buying intent in council minutes"
    return {
        "rfp": "RFP committee / public RFP discussion",
        "vendor_eol": "Vendor replacement / EOL discussion",
        "cyber": "Cyber incident reported",
        "leadership": "New leadership / staff change",
        "audit": "Audit finding flagged",
        "bond": "Capital bond with IT line item",
    }.get(sig_type, "Buying signal")


def _severity_for(sig_type, snippet):
    """Heuristic severity. RFP committee + motion to issue = high.
    Discussion / consideration = medium. Vague = low."""
    if re.search(r"motion\s+to\s+(?:issue|approve|authoriz)|vote\s+\d+", snippet, re.I):
        return "high"
    if re.search(r"discussion|consider|evaluate|presentation", snippet, re.I):
        return "medium"
    return "low"


# ---- Per-muni harvest ----------------------------------------------------

def scan_muni(name, state, pop=None, bucket=None,
               max_pdfs=12, per_pdf_delay=0.8):
    """Returns (customer_records, signal_records) for one muni."""
    slug = slugify(name)
    if not slug:
        return [], []
    base = discover_url(slug, state)
    if not base:
        return [], []
    pdfs = find_meeting_pdfs(base, max_pdfs=max_pdfs)
    if not pdfs:
        return [], []

    customers = []
    signals = []
    for pdf_url in pdfs:
        try:
            blob = fetch_bytes(pdf_url, timeout=15.0)
        except Exception:
            continue
        if not blob:
            continue
        text = extract_pdf_text(blob)
        if not text:
            continue
        # Approvals -> customer records
        for r in extract_approvals(text, pdf_url):
            customers.append({
                "vendor": r["vendor"],
                "muni": name, "state": state, "type": "muni",
                "bucket": bucket,
                "product": r["product"],
                "since": r["since"],
                "award_amount": r["amount"],
                "source": "meeting_minutes",
                "evidence": f"{pdf_url}: ...{r['snippet']}...",
                "confidence": r["confidence"],
                "pop": pop,
            })
        # Signals -> records shaped to drop into signals.SIGNALS directly.
        for s in extract_signals(text, pdf_url):
            signals.append({
                "id": f"mm_{state}_{slug}_{s['type']}_{abs(hash(pdf_url)) % 100000}",
                "muni": name, "state": state,
                "population": pop, "bucket": bucket,
                "type": s["type"],
                "severity": s["severity"],
                # Always ISO date — meeting_date is extracted but kept in
                # `meeting_date` so the parser can still parse the
                # 'detected' field.
                "detected": _today_iso(),
                "meeting_date_text": s.get("meeting_date"),
                "expires": None,
                "headline": s["headline"],
                "details":  s["snippet"],
                "source": f"Council meeting minutes ({pdf_url})",
                "url": pdf_url,
                "incumbent": None,    # connector caller may enrich later
                "demo": False,
            })
        time.sleep(per_pdf_delay)

    # Dedupe per muni: keep highest-confidence per (vendor, product)
    keyed = {}
    for r in customers:
        k = (r["vendor"], r.get("product"))
        if k not in keyed or r["confidence"] > keyed[k]["confidence"]:
            keyed[k] = r
    return list(keyed.values()), signals


# ---- Bulk runner ---------------------------------------------------------

def load_targets(states=None, top_n=None, top_prospects=False):
    if top_prospects:
        if not os.path.exists(GREENFIELD_PATH):
            sys.exit(f"  ERROR: {GREENFIELD_PATH} missing — run "
                      "build_greenfield_data.py first")
        with open(GREENFIELD_PATH) as f:
            gf = json.load(f)
        rows = []
        for p in gf.get("top_prospects", []):
            if states and p["state"] not in states:
                continue
            rows.append((p["muni"], p["state"], p.get("pop"), p.get("bucket")))
            if top_n and len(rows) >= top_n:
                break
        return rows
    with open(NAMES_PATH) as f:
        names = json.load(f)
    out = []
    for st, blob in names.items():
        if states and st not in states:
            continue
        for c in blob.get("cities", []):
            out.append((c["name"], st, c.get("pop"), c.get("bucket")))
    out.sort(key=lambda r: (r[2] is None, -(r[2] or 0)))
    if top_n:
        out = out[:top_n]
    return out


def harvest(states=None, top_n=None, top_prospects=False,
             threads=10, max_pdfs=12):
    targets = load_targets(states=states, top_n=top_n,
                            top_prospects=top_prospects)
    print(f"  scanning {len(targets):,} munis (threads={threads}, "
          f"max_pdfs={max_pdfs}/muni)")
    customers = []
    signals = []
    t0 = time.time()
    completed = 0
    found_munis = 0
    with cf.ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(scan_muni, n, st, p, b,
                              max_pdfs=max_pdfs): (n, st)
                   for n, st, p, b in targets}
        for fut in cf.as_completed(futures):
            completed += 1
            try:
                cust, sigs = fut.result()
            except Exception as e:
                cust, sigs = [], []
            if cust:
                customers.extend(cust)
                found_munis += 1
            signals.extend(sigs)
            if completed % 25 == 0:
                elapsed = time.time() - t0
                rate = completed / max(elapsed, 0.001)
                eta = (len(targets) - completed) / max(rate, 0.001)
                print(f"    {completed:,}/{len(targets):,}  "
                      f"({rate:.2f}/s, ETA {eta/60:.1f} min, "
                      f"{found_munis} munis with confirmed approvals, "
                      f"{len(customers)} customer hits, "
                      f"{len(signals)} signals)")
    print(f"  done in {(time.time() - t0)/60:.1f} min")
    print(f"  {found_munis} munis returned at least one approval")
    print(f"  {len(customers)} customer hits, {len(signals)} signals")
    # Dedupe customers across munis: (vendor, muni, state) — pick highest conf
    keyed = {}
    for r in customers:
        k = (r["vendor"], r["muni"], r["state"])
        if k not in keyed or r["confidence"] > keyed[k]["confidence"]:
            keyed[k] = r
    return list(keyed.values()), signals


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="*")
    ap.add_argument("--top", type=int)
    ap.add_argument("--top-prospects", action="store_true",
                    help="scan greenfield rows from greenfield_data.json")
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--max-pdfs", type=int, default=12,
                    help="max PDFs to download per muni")
    ap.add_argument("--out", default="meeting_minutes_hits.csv")
    ap.add_argument("--out-signals", default="meeting_minutes_signals.csv")
    args = ap.parse_args()

    customers, signals = harvest(states=args.states, top_n=args.top,
                                   top_prospects=args.top_prospects,
                                   threads=args.threads,
                                   max_pdfs=args.max_pdfs)
    print(f"\n{len(customers)} unique customer hits")
    by_v = {}
    for r in customers:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")

    if customers:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(customers[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for r in customers:
                w.writerow(r)
        print(f"\nwrote {args.out}")

    if signals:
        with open(args.out_signals, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(signals[0].keys()),
                                extrasaction="ignore")
            w.writeheader()
            for s in signals:
                w.writerow(s)
        print(f"wrote {args.out_signals}")
