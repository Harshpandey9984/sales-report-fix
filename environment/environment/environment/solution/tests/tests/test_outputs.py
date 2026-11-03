"""Hidden tests for the sales-report-fix task.

Design rules followed here:
  * Every test input is created at verification time. The agent never sees these files.
  * Expected values come from an independent reference implementation using Decimal,
    so float rounding noise in the agent's solution cannot hide behind float noise here.
  * Tests check behaviour that instruction.md states. Nothing is checked that the
    instruction does not promise.
"""
import json
import random
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest

SCRIPT = "/app/report.py"
HEADER = "region,product,quantity,unit_price,status\n"


# ---------- reference implementation (the specification, in code) ----------
def reference(csv_text):
    lines = csv_text.splitlines()
    totals = {}
    for line in lines[1:]:
        cells = line.split(",")
        if all(c.strip() == "" for c in cells):
            continue
        region, _product, qty, price, status = cells
        if status.strip().lower() == "cancelled":
            continue
        key = region.strip().lower()
        totals[key] = totals.get(key, Decimal("0")) + int(qty.strip()) * Decimal(price.strip())
    return {
        k: totals[k].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for k in sorted(totals)
    }


# ---------- helpers ----------
def run_report(tmp_path, csv_text, cwd=None):
    src = tmp_path / "input.csv"
    dst = tmp_path / "output.json"
    src.write_text(csv_text, newline="")
    proc = subprocess.run(
        [sys.executable, SCRIPT, str(src), str(dst)],
        cwd=str(cwd or tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"script exited {proc.returncode}\nstderr:\n{proc.stderr}"
    assert dst.exists(), "script did not create the output file"
    raw = dst.read_text()
    ordered = json.loads(raw, object_pairs_hook=lambda pairs: pairs)
    return ordered


def assert_matches(ordered_pairs, expected):
    assert isinstance(ordered_pairs, list), "output must be a JSON object"
    keys = [k for k, _ in ordered_pairs]
    assert keys == sorted(expected), f"keys wrong or not alphabetical: {keys} vs {sorted(expected)}"
    for key, value in ordered_pairs:
        assert isinstance(value, (int, float)) and not isinstance(value, bool), (
            f"value for {key!r} must be a JSON number, got {type(value).__name__}"
        )
        assert round(value, 2) == value, f"value for {key!r} not rounded to 2 places: {value!r}"
        assert abs(value - float(expected[key])) < 1e-9, (
            f"region {key!r}: expected {expected[key]}, got {value}"
        )


def check(tmp_path, csv_text, cwd=None):
    assert_matches(run_report(tmp_path, csv_text, cwd), reference(csv_text))


# ---------- handcrafted cases ----------
def test_example_from_instructions(tmp_path):
    text = (
        HEADER
        + "North,Widget,2,10.50,shipped\n"
        + "north ,Gadget,1,5.25,Shipped\n"
        + "South,Widget,3,10.50,CANCELLED\n"
        + "South,Gizmo,4,2.00,pending\n"
        + ",,,,\n"
        + "East,Widget,1,10.50,cancelled \n"
    )
    ordered = run_report(tmp_path, text)
    assert dict(ordered) == {"north": 26.25, "south": 8.0}
    assert_matches(ordered, reference(text))


def test_quantity_is_multiplied(tmp_path):
    check(tmp_path, HEADER + "a,p,5,3.00,shipped\n")


def test_header_only_gives_empty_object(tmp_path):
    assert run_report(tmp_path, HEADER) == []


def test_all_rows_cancelled_gives_empty_object(tmp_path):
    check(tmp_path, HEADER + "a,p,1,1.00,cancelled\nb,p,2,2.00,  CANCELLED  \n")


def test_region_with_only_cancelled_rows_is_omitted(tmp_path):
    text = HEADER + "keep,p,1,4.00,shipped\ndrop,p,9,9.00,Cancelled\n"
    ordered = run_report(tmp_path, text)
    assert [k for k, _ in ordered] == ["keep"]


def test_whitespace_and_case_variants_merge(tmp_path):
    text = (
        HEADER
        + "  West,p,1,1.00,shipped\n"
        + "WEST ,p,1,1.00,shipped\n"
        + "west,p,1,1.00,shipped\n"
    )
    ordered = run_report(tmp_path, text)
    assert dict(ordered) == {"west": 3.0}


def test_blank_and_whitespace_only_rows_are_skipped(tmp_path):
    text = HEADER + "a,p,1,2.00,shipped\n,,,,\n  ,  ,  ,  ,  \n\na,p,1,2.00,shipped\n"
    check(tmp_path, text)


def test_zero_quantity_region_still_appears(tmp_path):
    ordered = run_report(tmp_path, HEADER + "zero,p,0,5.00,shipped\n")
    assert dict(ordered) == {"zero": 0.0}


def test_float_noise_is_rounded_away(tmp_path):
    # 3 * 0.10 and 7 * 19.99 are classic cases where plain floats print long tails.
    text = HEADER + "a,p,3,0.10,shipped\nb,p,7,19.99,shipped\nc,p,3,1.10,shipped\n"
    ordered = run_report(tmp_path, text)
    assert dict(ordered) == {"a": 0.3, "b": 139.93, "c": 3.3}


def test_keys_are_alphabetical_not_input_order(tmp_path):
    text = HEADER + "zulu,p,1,1.00,shipped\nalpha,p,1,1.00,shipped\nmike,p,1,1.00,shipped\n"
    ordered = run_report(tmp_path, text)
    assert [k for k, _ in ordered] == ["alpha", "mike", "zulu"]


def test_works_from_a_different_working_directory(tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    check(tmp_path, HEADER + "a,p,2,2.50,shipped\n", cwd=other)


# ---------- generated cases: defeat hardcoding ----------
REGION_FORMS = ["North", "north", " NORTH ", "South", "south ", "East", " east", "WEST", "west", "  Central  "]
STATUS_FORMS = ["shipped", "Shipped", "pending", "PENDING", "returned", "cancelled", "CANCELLED", " Cancelled ", "cancelled  "]
BLANK_FORMS = [",,,,", "  ,  ,  ,  ,  ", " , , , , "]


def make_csv(seed, n_rows):
    rng = random.Random(seed)
    lines = []
    for _ in range(n_rows):
        if rng.random() < 0.05:
            lines.append(rng.choice(BLANK_FORMS))
            continue
        region = rng.choice(REGION_FORMS)
        qty = rng.randint(0, 40)
        price = f"{rng.randint(1, 20000) / 100:.2f}"
        lines.append(f"{region},prod{rng.randint(1, 9)},{qty},{price},{rng.choice(STATUS_FORMS)}")
    return HEADER + "\n".join(lines) + "\n"


@pytest.mark.parametrize("seed,n_rows", [(1, 10), (2, 50), (3, 200), (4, 1000), (5, 3000)])
def test_random_files(tmp_path, seed, n_rows):
    check(tmp_path, make_csv(seed, n_rows))


def test_no_trailing_newline_and_crlf_line_endings(tmp_path):
    text = (HEADER + "a,p,2,2.00,shipped\nb,p,1,1.50,shipped").replace("\n", "\r\n")
    src = tmp_path / "input.csv"
    dst = tmp_path / "output.json"
    src.write_bytes(text.encode())
    proc = subprocess.run([sys.executable, SCRIPT, str(src), str(dst)], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(dst.read_text()) == {"a": 4.0, "b": 1.5}
