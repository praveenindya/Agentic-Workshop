"""Tests for cases/expense/policy.py (Story 2.2: CAP-3 precedence + CAP-4 math).

The real acceptance test: replay POLICY.md's precedence logic against
every one of the 30 labelled claims (119 line items) in
eval/labelled.csv and assert an exact decision+clause match. This is
also how the spec's flagged open question -- whether a genuine
precedence tie exists anywhere in the labelled set -- gets answered:
empirically, by running every row, rather than by hand-tracing.
"""

import csv
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = REPO_ROOT / "cases" / "expense" / "seed"
EVAL_DIR = REPO_ROOT / "cases" / "expense" / "eval"

spec = importlib.util.spec_from_file_location("expense_policy_under_test", REPO_ROOT / "cases/expense/policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


CLAIMS = {row["claim_id"]: row for row in _read_csv(SEED_DIR / "claims.csv")}
EMPLOYEES = {row["employee_id"]: row for row in _read_csv(SEED_DIR / "employees.csv")}
LINE_ITEMS = _read_csv(SEED_DIR / "line_items.csv")
LINE_ITEMS_BY_ID = {row["line_id"]: row for row in LINE_ITEMS}
LIMITS_ROWS = _read_csv(SEED_DIR / "limits.csv")
LABELLED = _read_csv(EVAL_DIR / "labelled.csv")


def _limits_for(level: str, city: str) -> dict:
    return {row["category"]: float(row["limit_cad"]) for row in LIMITS_ROWS if row["level"] == level and row["city"] == city}


def _claim_line_items(claim_id: str) -> list[dict]:
    return [row for row in LINE_ITEMS if row["claim_id"] == claim_id]


def _employee_history(employee_id: str) -> list[dict]:
    employee_claim_ids = {c["claim_id"] for c in CLAIMS.values() if c["employee_id"] == employee_id}
    return [row for row in LINE_ITEMS if row["claim_id"] in employee_claim_ids]


def _decide(line_id: str) -> tuple[str, str]:
    line_item = LINE_ITEMS_BY_ID[line_id]
    claim = CLAIMS[line_item["claim_id"]]
    employee = EMPLOYEES[claim["employee_id"]]
    # POLICY.md 2: limits depend on level and "the city where the expense
    # happened" -- the line item's own city, not the employee's home city.
    limits = _limits_for(employee["level"], line_item["city"])
    return policy.decide_line_item(
        line_item=line_item,
        claim=claim,
        limits=limits,
        employee_history=_employee_history(claim["employee_id"]),
        claim_line_items=_claim_line_items(claim["claim_id"]),
    )


def test_every_labelled_line_item_matches_exactly():
    mismatches = []
    for row in LABELLED:
        decision, clause = _decide(row["line_id"])
        if decision != row["expected_decision"] or clause != row["expected_clause"]:
            mismatches.append(
                f"{row['line_id']}: got ({decision}, {clause}), expected ({row['expected_decision']}, {row['expected_clause']})"
            )
    assert not mismatches, "\n".join(mismatches)


def test_labelled_set_is_fully_covered_no_silent_skips():
    # Guards against a typo in _decide silently matching 0 rows and the
    # loop above passing vacuously.
    assert len(LABELLED) > 100


def test_alcohol_always_rejected_under_3_1():
    alcohol_rows = [r for r in LINE_ITEMS if r["category"] == "alcohol"]
    assert alcohol_rows, "fixture sanity: seed data should contain at least one alcohol item"
    for row in alcohol_rows:
        assert _decide(row["line_id"]) == ("reject", "3.1")


def test_duplicate_wins_over_same_day_limit_aggregation():
    # CL-2016's two identical meal lines (L-3062, L-3063): the earlier one
    # is judged on the day's aggregated total (flag/2.1); the later,
    # identical one is rejected as a duplicate (5.1) even though it's
    # part of the same aggregated sum.
    assert _decide("L-3062") == ("flag", "2.1")
    assert _decide("L-3063") == ("reject", "5.1")


def test_software_with_ita_code_approved_without_it_rejected():
    assert _decide("L-3055") == ("approve", "4.1")  # has "IT approval ITA-4471"
    assert _decide("L-3051") == ("reject", "4.1")  # "Annual Figma licence", no ITA code


def test_receipt_flag_only_fires_within_limit():
    # L-3075 (CL-2019, ground/Uber): within the day's ground limit but
    # flagged for a missing receipt on an over-$25 item -- proves 1.3 is
    # reachable, not dead code always shadowed by the limits step.
    assert _decide("L-3075") == ("flag", "1.3")
