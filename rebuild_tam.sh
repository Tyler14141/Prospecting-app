#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/build"

if [[ ! -d "$BUILD_DIR" ]]; then
  echo "Build directory not found: $BUILD_DIR" >&2
  exit 1
fi

cd "$BUILD_DIR"

python3 build_workbook.py
python3 add_competitor_tab.py
python3 build_names_data.py
python3 build_signals_data.py
python3 build_dashboard_v2.py
python3 build_brief.py
python3 recalc.py
python3 validate.py

echo "TAM rebuild complete. Outputs are in $ROOT_DIR/TAM"
