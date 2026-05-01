"""
Recalculate Local_Government_TAM.xlsx and report any formula errors
(#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A, #NUM!, #NULL!).

Uses the `formulas` package (LibreOffice unavailable in this environment).
Writes the recalculated values back into the workbook so opening it in Excel
shows cached results immediately.
"""

import os
import re

import formulas
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.normpath(os.path.join(HERE, "..", "TAM",
                                            "Local_Government_TAM.xlsx"))

ERROR_TOKENS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?",
                "#N/A", "#NUM!", "#NULL!")


def recalc():
    print(f"Recalculating {XLSX_PATH}")
    xl_model = formulas.ExcelModel().loads(XLSX_PATH).finish()
    sol = xl_model.calculate()

    errors = []
    written = 0
    wb = load_workbook(XLSX_PATH)

    # Map ('SheetName', 'A1') -> value
    for key, val in sol.items():
        # keys look like "'[Local_Government_TAM.xlsx]Summary'!A1"
        m = re.match(r"'?\[.*?\](.*?)'?!(\$?[A-Z]+\$?\d+)", key)
        if not m:
            continue
        sheet_name = m.group(1)
        cell_ref = m.group(2).replace("$", "")
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        try:
            v = val.value if hasattr(val, "value") else val
            # formulas returns numpy arrays for single cells
            if hasattr(v, "tolist"):
                v = v.tolist()
                if isinstance(v, list) and len(v) == 1:
                    v = v[0]
                if isinstance(v, list) and len(v) == 1:
                    v = v[0]
        except Exception:
            v = val

        if isinstance(v, str) and v in ERROR_TOKENS:
            errors.append((sheet_name, cell_ref, v))
        # Write only if the cell currently holds a formula (preserve inputs)
        cell = ws[cell_ref]
        if isinstance(cell.value, str) and cell.value.startswith("="):
            try:
                cell.value = v
                written += 1
            except Exception:
                pass

    wb.save(XLSX_PATH)
    print(f"  wrote {written} computed values back into the workbook")

    if errors:
        print(f"  FORMULA ERRORS ({len(errors)}):")
        for s, c, v in errors[:50]:
            print(f"    {s}!{c}: {v}")
    else:
        print("  no formula errors detected")
    return errors


if __name__ == "__main__":
    recalc()
