# Fix the sales report script

`/app/report.py` is supposed to turn a CSV of sales rows into a JSON revenue summary per region, but it produces wrong results. Fix it.

## Usage

```
python3 /app/report.py INPUT.csv OUTPUT.json
```

The script must keep this command-line interface. A small example input is at `/app/sample.csv`.

## Input format

The CSV has a header row and these columns:

| column       | meaning                                   |
|--------------|-------------------------------------------|
| `region`     | sales region name                         |
| `product`    | product name (not needed for the report)  |
| `quantity`   | whole number of units sold                |
| `unit_price` | price per unit, a decimal like `19.99`    |
| `status`     | order status, e.g. `shipped`, `cancelled` |

Real files are messy: region names and statuses can have inconsistent capitalisation and stray leading or trailing spaces, and some lines may have every field blank.

## Required behaviour

1. The revenue of a row is `quantity * unit_price`.
2. Ignore rows whose `status`, after trimming spaces and ignoring capitalisation, is `cancelled`.
3. Ignore rows where every field is blank or only spaces.
4. Treat region names as the same region if they match after trimming spaces and lowercasing. Use the trimmed, lowercased name as the key.
5. Write `OUTPUT.json` as a single JSON object mapping each region to its total revenue, as a JSON number rounded to 2 decimal places.
6. Keys must be in alphabetical order.
7. A region with no counted rows must not appear in the output.
8. A file containing only the header row produces `{}`.

Your script will be run on other input files than the sample, so it must work in general. Do not hardcode results.
