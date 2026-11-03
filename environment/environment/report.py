import csv
import json
import sys


def main():
    src, dst = sys.argv[1], sys.argv[2]
    totals = {}
    with open(src) as f:
        for row in csv.DictReader(f):
            region = row["region"]
            totals[region] = totals.get(region, 0) + float(row["unit_price"])
    with open(dst, "w") as f:
        json.dump(totals, f)


if __name__ == "__main__":
    main()
