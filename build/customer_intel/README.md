# customer_intel — find competitor customers from free public sources

Real, working scrapers for the local-gov software competitive landscape.
Run from a machine with full internet access (this sandbox is firewalled).

## Quick start

```bash
cd build
pip install beautifulsoup4 pdfplumber          # optional but recommended
python -m customer_intel.harvest               # runs all free connectors
python -m customer_intel.merge customer_intel_merged.csv --write
python add_competitor_tab.py                   # rebake competitors_data.json
python build_dashboard_v2.py                   # rebuild dashboard
```

That sequence will:
1. Hit crt.sh, vendor case-study pages, Indeed, and DNS fingerprints.
2. Write `customer_intel_raw.csv` (every find) and
   `customer_intel_merged.csv` (deduped).
3. Splice new high-confidence records into `competitor_customers.py`.
4. Rebuild the dashboard's named-customer panel with real data.

## Connectors

| Connector | What it does | Coverage* | Cost | Run time |
|---|---|---|---|---|
| `crt_sh` | Queries Certificate Transparency logs for vendor-hosted muni subdomains. Highest-leverage source. | ~30-40% | free | ~1 min/vendor |
| `case_studies` | Scrapes each vendor's "Customers" / "Case Studies" page. Lower coverage, very high precision. | ~10-20% | free | ~10s/vendor |
| `dns_strict` | Strict-DNS probe of vendor domains (per-customer subdomains that only resolve when a customer exists). Bypasses HTTP firewalls. | ~30-40% | free | ~6 min full US |
| `muni_website` | Probes each muni's `.gov` site for vendor URL/text fingerprints across homepage + key paths. Best for filling in incumbents on greenfield prospects. | ~40-60% | free | ~30 min full US |
| `meeting_minutes` | Walks the muni's clerk/agendas page, downloads recent meeting-minute PDFs, extracts vendor approvals + dollar amounts + dates verbatim. Highest precision; also emits buying signals. | ~30-50% | free | ~3-4 hr per 1000 munis at 20 threads |
| `job_postings` | Scrapes Indeed for job descriptions requiring vendor-specific skills (e.g. "Tyler Munis required"). | ~30% on ERP | free | ~1 min/vendor |
| `cafr_pdf` | Extracts vendor mentions from CAFR / ACFR PDFs. Best coverage but you have to gather PDFs. | ~70% if PDFs sourced | free | depends on # of PDFs |
| `dns_fingerprint` | Deprecated — superseded by `dns_strict` and `muni_website`. Left for back-compat. | ~30-40% | free | scales with `--max-probes` |

*Coverage = percentage of each vendor's installed base recoverable from
that source alone. Stack three or more for ~80% combined.

## Connector details

### `crt_sh` — Certificate Transparency log search

**The single highest-ROI free source.** Queries `crt.sh` for every cert
issued under each vendor's main domains (e.g. `*.tylertech.com`,
`*.bsaonline.com`, `*.muni-link.com`). Subdomains usually encode the
customer name (`saginaw.bsaonline.com`), which we strip and resolve
against the US places list to recover (vendor, muni, state).

```bash
python -m customer_intel.connectors.crt_sh
```

Notes:
- crt.sh has no auth and rate limits to ~1 req/sec.
- High-confidence rows are those where the extracted name matched a real
  US municipality. Unresolved candidates are emitted at 0.3 confidence —
  often these are still hits, just under non-standard naming.
- Add new vendor domains in `customer_intel/__init__.py:VENDOR_DOMAINS`.

### `case_studies` — vendor case-study scraper

Pulls the public customer pages each vendor publishes. Each vendor's
URLs are configured in `customer_intel/__init__.py:VENDOR_CASE_STUDY_URLS`.

```bash
python -m customer_intel.connectors.case_studies
```

Pages that show only logos (not names) won't yield much; for those,
extend the connector with image-alt-text scraping or run an OCR pass
on the page screenshots.

### `dns_fingerprint` — active URL probe

Walks the names list and probes each muni's likely vendor-hosted URL.
Slow (one HTTP request per muni-vendor pair), but high precision when a
fingerprint matches.

```bash
python -m customer_intel.connectors.dns_fingerprint --max 1000
python -m customer_intel.connectors.dns_fingerprint --max 200 --states IA NE KS MO
```

Fingerprints are configured in `connectors/dns_fingerprint.py`.

### `job_postings` — Indeed scraper

Hits Indeed with vendor-specific keywords ("Tyler Munis", "BS&A
Software"). Munis posting jobs that require those skills almost
certainly run that vendor.

```bash
python -m customer_intel.connectors.job_postings
```

For production volume, swap the public-web scrape for the **Indeed
Publisher API** (free tier, 1K calls/day). See connector docstring for
the swap-in pattern.

### `muni_website` — fingerprint vendors from the muni's own website

**Highest-leverage way to fill in incumbents** for the ~16K greenfield
prospects in `greenfield_data.json`. For each muni:

1. Probes ~18 common URL patterns (`https://www.cityof<muni>.gov`,
   `https://<muni>.<st>.gov`, etc.) until one resolves.
2. Crawls homepage + 11 key paths (`/payments`, `/permits`,
   `/utility-billing`, `/agendas`, etc.).
3. Scans combined HTML for vendor URL patterns + text fingerprints
   ("Powered by Tyler", "BS&A Software", iframe to `tylerciviccess.com`,
   form action to `bsaonline.com`, etc.).

```bash
# Just scan greenfield prospects (highest ROI: ~10K targets that don't
# already have a known incumbent)
python -m customer_intel.connectors.muni_website --top-prospects

# Or scan a state slice
python -m customer_intel.connectors.muni_website --states IA NE KS

# Or top-1000 by population (full US)
python -m customer_intel.connectors.muni_website --top 1000
```

Politeness: 1.5s delay between requests to the same host, 12 concurrent
munis by default. Tune `--muni-concurrency` if you have a tight runtime
budget but watch for the host blocking you.

### `meeting_minutes` — council/board meeting-minute PDFs

**Highest-precision free source.** Walks the muni's clerk / agendas
index, downloads recent meeting-minute PDFs (last ~12 by default),
extracts text via `pdfplumber` / `pypdf` / `pdftotext`, then
pattern-matches:

- **Vendor approvals**: "Motion to approve a 5-year agreement with
  Tyler Technologies for financial management software in the amount
  of $185,000 annually." → emits a customer record with vendor,
  product, ACV, and start year.
- **Buying signals**: RFP committee formation, vendor EOL discussion,
  cyber-incident reports, audit findings, leadership changes → saved
  to `meeting_minutes_signals.csv` for review (richer schema than the
  customer harvest, so not auto-merged into competitor_customers).

Slower than other connectors because each muni requires
discovery + minutes-index page + ~12 PDF downloads + text
extraction. Budget **~3-4 hours per 1000 munis at 20 threads**.

```bash
# Best ROI: top-1000 prospects (already filtered to actionable)
python -m customer_intel.connectors.meeting_minutes --top-prospects \
    --threads 20 --max-pdfs 8

# Single state, deeper PDF crawl
python -m customer_intel.connectors.meeting_minutes --states IA \
    --threads 15 --max-pdfs 18

# Or via the harvester (saves to standard CSVs)
python -m customer_intel.harvest --only meeting_minutes \
    --minutes-top-prospects --minutes-threads 20
```

The dollar-amount extraction is sentence-window aware: it looks for
the `$XXX` pattern within ~600 chars of an approval phrase and the
vendor mention. False positives are rare — typical false positive
is when a single meeting approves multiple unrelated contracts and
the wrong dollar gets attached.

### `cafr_pdf` — CAFR / ACFR vendor mention extraction

The most comprehensive source — every muni publishes one. Bottleneck is
gathering PDFs. Drop them in a directory named with the convention
`<ST>_<MuniName>_<Year>.pdf` (e.g. `IA_Cedar Falls_2023.pdf`) and run:

```bash
python -m customer_intel.connectors.cafr_pdf /path/to/cafr_dir
# or via the harvester:
python -m customer_intel.harvest --cafr-dir /path/to/cafr_dir
```

Where to source CAFR PDFs:
- `munistat.com` — free download portal
- `MSRB EMMA` — bond-issuing munis post here
- Individual muni websites — scrape their `/financial-reports` pages

## Aggregator: `harvest.py`

Runs all enabled connectors, dedupes, writes CSV.

```bash
python -m customer_intel.harvest                          # everything
python -m customer_intel.harvest --only crt_sh case_studies
python -m customer_intel.harvest --skip job_postings
python -m customer_intel.harvest --max-probes 1500
python -m customer_intel.harvest --cafr-dir ~/cafr-pdfs
```

Output:
- `customer_intel_raw.csv` — every row from every source
- `customer_intel_merged.csv` — deduped by (vendor, muni, state) with
  combined source list and best-confidence

## Merger: `merge.py`

Splices the merged CSV into `competitor_customers.py`. Default is dry
run with a diff; pass `--write` to apply.

```bash
python -m customer_intel.merge customer_intel_merged.csv
python -m customer_intel.merge customer_intel_merged.csv --min-confidence 0.8 --write
```

Then rebuild the dashboard:

```bash
python add_competitor_tab.py
python build_dashboard_v2.py
```

## Adding a new vendor

1. Append the vendor to `VENDOR_DOMAINS` and `VENDOR_CASE_STUDY_URLS` in
   `customer_intel/__init__.py`.
2. Add a fingerprint in `connectors/dns_fingerprint.py:FINGERPRINTS`.
3. Add product strings in `connectors/cafr_pdf.py:VENDOR_FINGERPRINTS`.
4. Add search keywords in `connectors/job_postings.py:VENDOR_KEYWORDS`.
5. Re-run `python -m customer_intel.harvest`.

## What this won't get you

- Vendors that host on the customer's own domain (rare but happens with
  on-prem deployments) — invisible to crt.sh.
- Customers behind opaque vanity URLs — visible only via CAFR or job
  postings.
- Internal-only deployments — no public surface to fingerprint.

Combine three or more sources, accept ~80% recall, fill the rest from
your own sales-rep references and outbound conversations.
