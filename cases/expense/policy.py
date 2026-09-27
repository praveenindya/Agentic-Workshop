"""Deterministic POLICY.md decision engine (CAP-3, CAP-4).

This is NOT an MCP tool -- it's a local, pure-Python function the agent
calls directly (like a LangChain @tool, but never exposed over stdio),
so it doesn't touch Epic 1's closed five-tool MCP surface. It exists
because POLICY.md's precedence order, limit-percentage math, same-day
aggregation, and cross-claim duplicate detection are all exactly
specified and must match 100% -- that's not a bar an LLM's free-form
arithmetic should be trusted to hit run after run, so the actual
decision is computed here; the agent's job is orchestration (fetching
context via MCP tools, calling this, recording the result, and writing
a human-readable explanation for the judge).

Precedence order (POLICY.md, "When more than one clause applies"):
    section 3 -> 5.1 -> 1.2 -> 4.1 -> limits (2, 6) -> 1.3 -> fallback approve.

The limits step only "fires" (overrides later clauses) when the amount is
OVER the limit (flag/reject per 2.4); at-or-under is not a firing -- it
falls through to the 1.3 receipt check, then the fallback approve. Both
the limits-approve and fallback-approve paths cite the same category
clause, so no separate code path is needed for them.
"""

from __future__ import annotations

from datetime import date, datetime

NOT_REIMBURSABLE_CLAUSES = {"alcohol": "3.1", "personal": "3.2", "fine": "3.3"}
CATEGORY_CLAUSE = {"meals": "2.1", "hotel": "2.2", "flight": "2.3", "ground": "6.1"}
AGGREGATE_CATEGORIES = {"meals", "ground"}  # summed per day; hotel/flight are per-line
RECEIPT_THRESHOLD = 25
OVERAGE_FLAG_CEILING = 1.20  # over the limit by up to 20% -> flag; beyond that -> reject
DUPLICATE_WINDOW_DAYS = 60


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _is_duplicate(line_item: dict, employee_history: list[dict]) -> bool:
    """POLICY.md 5.1: same date+merchant+amount as an EARLIER item from the same employee."""
    this_date = _parse_date(line_item["date"])
    this_key = (this_date, line_item["merchant"], float(line_item["amount"]))
    for other in employee_history:
        if other["line_id"] == line_item["line_id"]:
            continue
        other_key = (_parse_date(other["date"]), other["merchant"], float(other["amount"]))
        if other_key != this_key:
            continue
        # "earlier" = earlier date, or same date and a lower line_id (seed data's insertion order).
        if other_key[0] < this_key[0] or (other_key[0] == this_key[0] and other["line_id"] < line_item["line_id"]):
            return True
    return False


def _too_old(line_item: dict, claim: dict) -> bool:
    """POLICY.md 1.2: dated more than 60 days before the claim's submission date."""
    days_before = (_parse_date(claim["submitted_at"]) - _parse_date(line_item["date"])).days
    return days_before > DUPLICATE_WINDOW_DAYS


def _has_it_approval(description: str) -> bool:
    """POLICY.md 4.1: description includes an IT approval code, ITA- followed by digits."""
    import re

    return bool(re.search(r"ITA-\d+", description or ""))


def _needs_receipt_flag(line_item: dict) -> bool:
    """POLICY.md 1.3: over $25 without a receipt."""
    return float(line_item["amount"]) > RECEIPT_THRESHOLD and line_item.get("has_receipt") == "no"


def _day_total(line_item: dict, claim_line_items: list[dict]) -> float:
    """Sum of every line item in this claim, same date and category (POLICY.md 2.1, 6.1)."""
    category = line_item["category"]
    this_date = line_item["date"]
    return sum(
        float(item["amount"])
        for item in claim_line_items
        if item["category"] == category and item["date"] == this_date
    )


def _limit_decision(amount: float, limit: float) -> str | None:
    """None means 'within limit, does not override' -- precedence falls through."""
    if amount <= limit:
        return None
    if amount <= limit * OVERAGE_FLAG_CEILING:
        return "flag"
    return "reject"


def decide_line_item(
    line_item: dict,
    claim: dict,
    limits: dict,
    employee_history: list[dict],
    claim_line_items: list[dict],
) -> tuple[str, str]:
    """Return (decision, clause) for one line item, per POLICY.md's fixed precedence.

    - line_item: this row (line_id, claim_id, date, city, category, merchant, amount, has_receipt, description)
    - claim: the claim it belongs to (needs submitted_at)
    - limits: {category: limit_cad} for the employee's level/city, from get_policy_limits
    - employee_history: every line item across ALL of the employee's existing claims
      (from get_employee_line_items), including this claim's own items
    - claim_line_items: every line item on this specific claim (for same-day aggregation)
    """
    category = line_item["category"]

    if category in NOT_REIMBURSABLE_CLAUSES:
        return "reject", NOT_REIMBURSABLE_CLAUSES[category]

    if _is_duplicate(line_item, employee_history):
        return "reject", "5.1"

    if _too_old(line_item, claim):
        return "reject", "1.2"

    if category in ("software", "equipment"):
        if _has_it_approval(line_item.get("description", "")):
            return "approve", "4.1"
        return "reject", "4.1"

    if category in limits:
        amount = _day_total(line_item, claim_line_items) if category in AGGREGATE_CATEGORIES else float(line_item["amount"])
        limit_verdict = _limit_decision(amount, limits[category])
        if limit_verdict is not None:
            return limit_verdict, CATEGORY_CLAUSE[category]

    if _needs_receipt_flag(line_item):
        return "flag", "1.3"

    return "approve", CATEGORY_CLAUSE.get(category, "1.1")
