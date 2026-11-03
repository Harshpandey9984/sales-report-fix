#!/bin/bash
# Oracle: writes a correct report.py. Used only to prove the task is solvable.
set -euo pipefail

cat > /app/report.py << 'PY'
import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def main():
    src, dst = sys.argv[1], sys.argv[2]
    totals = {}
    with open(src, newline="") as f:
        for row in csv.DictReader(f):
            if all((v or "").strip() == "" for v in row.values()):
                continue
            if (row["status"] or "").strip().lower() == "cancelled":
                continue
            region = (row["region"] or "").strip().lower()
            revenue = int(row["quantity"].strip()) * Decimal(row["unit_price"].strip())
            totals[region] = totals.get(region, Decimal("0")) + revenue
    out = {
        k: float(totals[k].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k in sorted(totals)
    }
    with open(dst, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    main()
PY
