# sales-report-fix

A small agent-evaluation task in the Harbor / Terminal-Bench format. An agent is given a broken Python script and must fix it so it turns messy sales CSV files into a correct JSON revenue report. Success is decided by a hidden pytest suite, not by the agent's own claim.

## Layout

```
instruction.md          prompt shown to the agent
task.toml               timeouts and metadata
environment/            what the agent starts with (Dockerfile, broken report.py, sample.csv)
solution/solve.sh       reference ("oracle") solution, proves the task is solvable
tests/test.sh           verifier entrypoint, writes 1 or 0 to /logs/verifier/reward.txt
tests/test_outputs.py   hidden pytest suite
```

## What the task checks

The script must compute `quantity * unit_price` per row, ignore cancelled and blank rows, merge region names that differ only by case or spaces, round to 2 decimals, and emit alphabetically sorted JSON.

## Design decisions

- **Hidden, generated test data.** Besides handcrafted edge cases, the tests build random CSVs (10 to 3000 rows) at verification time, so hardcoding the sample's answer cannot pass.
- **Independent reference implementation** in `test_outputs.py`, using `Decimal`, so expected values are exact and are not produced by the same float math the agent may use.
- **Tests only check what `instruction.md` states.** Every rule in the instruction has a test, and nothing is tested that the instruction does not promise.
- **No network at verification time.** pytest is pinned in the Dockerfile.

## How the task was validated

| Solution | Result |
|---|---|
| Original broken script | reward 0 (16 of 17 tests fail) |
| Reference solution (`solution/solve.sh`) | reward 1 (17 of 17 pass) |
| Float-based alternative solution | reward 1 |
| `csv.reader` + `Decimal` alternative solution | reward 1 |
| 8 deliberately wrong variants (no lowercase, no sorting, no strip on status, case-sensitive status, drops zero totals, no rounding, hardcoded output, string values) | reward 0 for all |

## Run it

With Harbor installed (check the Harbor docs for the exact flags of your version):

```
harbor run -p ./sales-report-fix -a <agent> -m <model>
```

Without Harbor, to check the verifier by hand inside the built image:

```
docker build -t sales-report-fix environment/
docker run --rm -v "$PWD/tests:/tests" -v "$PWD/solution:/solution" sales-report-fix \
  bash -c "mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh && cat /logs/verifier/reward.txt"
```
