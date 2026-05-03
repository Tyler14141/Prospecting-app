#!/usr/bin/env bash
# After dns_strict scan finishes, merge results into competitor_customers.py,
# rebake all derived data, regenerate dashboard, and validate.
# Used after: python3 -m customer_intel.connectors.dns_strict --threads 200

set -euo pipefail
cd "$(dirname "$0")"

echo "=== merging dns_strict_hits.csv into competitor_customers.py ==="
python3 -m customer_intel.merge dns_strict_hits.csv --min-confidence 0.85 --write

echo
echo "=== regenerating workbook + JSON ==="
python3 build_workbook.py
python3 add_competitor_tab.py
python3 build_signals_data.py
python3 build_greenfield_data.py

echo
echo "=== rebuilding dashboard ==="
python3 build_dashboard_v2.py

echo
echo "=== recalculating workbook formulas ==="
python3 recalc.py

echo
echo "=== validating ==="
python3 validate.py
