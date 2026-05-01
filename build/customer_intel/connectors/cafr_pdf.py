"""
CAFR / ACFR PDF vendor-mention extractor.

Most municipalities publish an Annual Comprehensive Financial Report (ACFR,
formerly CAFR). The notes section, IT capex schedules, and vendor disclosure
appendices commonly name the financial-system vendor by product. Search for
vendor product names in PDF text → confirmed customer.

Usage
-----
1. Drop CAFR PDFs into a directory. File naming convention:
       <ST>_<MuniName>_<Year>.pdf
   Example:  IA_Cedar Falls_2023.pdf
   The connector parses state + muni from the filename.

2. Run:
       python -m customer_intel.connectors.cafr_pdf /path/to/cafr_dir

Coverage
--------
CAFRs are public for every muni — coverage potential is enormous. Bottleneck
is gathering the PDFs. Sources:
  - munistat.com (free)
  - EMMA (MSRB) — bond-issuing munis post CAFR/ACFR there
  - Individual muni websites (manual scraping or a Census of Govts
    cross-walk)

Scaling
-------
For ~100 PDFs this script is fine. For ~10K PDFs use a job queue and store
extracted vendor mentions in a database. The vendor product strings below
are the fingerprint set — extend as you find new product naming.
"""

import json
import os
import re
import sys

# Vendor product fingerprints. Pattern -> vendor.
# Order matters — most-specific first (so "Tyler Munis" matches before
# "Tyler" alone).
VENDOR_FINGERPRINTS = [
    # Tyler — most products
    (re.compile(r"\bTyler[\s-]?Munis\b", re.I), "Tyler Technologies", "Munis ERP"),
    (re.compile(r"\bTyler\s+Enterprise\s+ERP\b", re.I), "Tyler Technologies", "Enterprise ERP"),
    (re.compile(r"\bTyler\s+Technologies?\b", re.I), "Tyler Technologies", None),
    (re.compile(r"\bMUNIS\b"), "Tyler Technologies", "Munis ERP"),
    (re.compile(r"\bNew\s+World\s+Systems?\b", re.I), "Tyler Technologies", "New World"),
    (re.compile(r"\bIncode\b", re.I), "Tyler Technologies", "Incode"),
    (re.compile(r"\bEden\s+Financial\b", re.I), "Tyler Technologies", "Eden"),
    (re.compile(r"\bEnerGov\b", re.I), "Tyler Technologies", "EnerGov"),
    (re.compile(r"\bSocrata\b", re.I), "Tyler Technologies", "Socrata"),
    (re.compile(r"\bExecuTime\b", re.I), "Tyler Technologies", "ExecuTime"),
    (re.compile(r"\bBrazos\b", re.I), "Tyler Technologies", "Brazos"),

    # BS&A
    (re.compile(r"\bBS&?A\s+Software\b", re.I), "BS&A Software", "Financial Mgmt"),
    (re.compile(r"\bBS&?A\b"), "BS&A Software", None),

    # Caselle
    (re.compile(r"\bCaselle\b", re.I), "Caselle", "Caselle Connect"),
    (re.compile(r"\bClarity\s+Caselle\b", re.I), "Caselle", "Clarity"),

    # gWorks (and acquired)
    (re.compile(r"\bgWorks\b", re.I), "gWorks", "gWorks Suite"),
    (re.compile(r"\bBanyon\s+Data\s+Systems?\b", re.I), "gWorks", "Banyon"),
    (re.compile(r"\bPontem\s+Software\b", re.I), "gWorks", "Pontem"),
    (re.compile(r"\bCompu-?Strategies\b", re.I), "gWorks", "Compu-Strategies"),

    # Muni-Link
    (re.compile(r"\bMuni-?Link\b", re.I), "Muni-Link", "Utility Billing"),

    # TownCloud
    (re.compile(r"\bTownCloud\b", re.I), "TownCloud", "TownCloud Suite"),
]

# Filename pattern: <ST>_<MuniName>_<Year>.pdf or <ST>-<MuniName>-<Year>.pdf
FILENAME_PAT = re.compile(
    r"^([A-Z]{2})[_\-\s]+([A-Z][A-Za-z\.\' \-]+?)[_\-\s]+(\d{4})\.pdf$"
)


def extract_text(path: str) -> str:
    """Extract text from a PDF. Tries pdfplumber, then pypdf, then pdftotext."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text_parts.append(t)
        return "\n".join(text_parts)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except ImportError:
        pass
    # Fallback to system pdftotext
    import subprocess
    try:
        r = subprocess.run(["pdftotext", "-layout", path, "-"],
                            capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    raise RuntimeError("Need pdfplumber, pypdf, or pdftotext to read PDFs. "
                        "Install one: pip install pdfplumber")


def parse_filename(filename: str):
    """Try to derive (state, muni, year) from the filename. Returns
    (None, None, None) if unparseable."""
    m = FILENAME_PAT.match(filename)
    if not m:
        return None, None, None
    return m.group(1), m.group(2).strip(), int(m.group(3))


def find_vendor_mentions(text: str) -> list:
    """Return list of (vendor, product, snippet)."""
    out = []
    for pat, vendor, product in VENDOR_FINGERPRINTS:
        for m in pat.finditer(text):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            snippet = text[start:end].replace("\n", " ").strip()
            out.append((vendor, product, snippet))
            break  # one mention per vendor per doc is enough
    return out


def harvest(directory: str) -> list:
    if not os.path.isdir(directory):
        print(f"  ERROR: {directory} is not a directory")
        return []
    out = []
    files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    print(f"  cafr_pdf: scanning {len(files)} PDFs in {directory}")
    for f in files:
        st, muni, year = parse_filename(f)
        path = os.path.join(directory, f)
        try:
            text = extract_text(path)
        except Exception as e:
            print(f"    WARN: {f}: {e}")
            continue
        for vendor, product, snippet in find_vendor_mentions(text):
            out.append({
                "vendor": vendor,
                "muni": muni or os.path.splitext(f)[0],
                "state": st,
                "type": None, "bucket": None,
                "product": product,
                "since": year,
                "source": "cafr_pdf",
                "evidence": f"{f}: ...{snippet}...",
                "confidence": 0.95 if st and muni else 0.6,
            })
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m customer_intel.connectors.cafr_pdf <pdf_dir>")
        sys.exit(2)
    rows = harvest(sys.argv[1])
    print(f"\n{len(rows)} vendor mentions extracted")
    by_v = {}
    for r in rows:
        by_v[r["vendor"]] = by_v.get(r["vendor"], 0) + 1
    for v, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {n:>5}")
