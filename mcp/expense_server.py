"""MCP server that gives the expense reviewer agent access to
cases/expense/expense.db over stdio.

Story 1.2 added CAP-2 (get_claim) and CAP-3 (get_employee). Story 1.3
added CAP-4 (get_policy_limits). Story 1.4 adds CAP-5 (record_decision).
A later story adds the cross-claim line-item lookup. No policy or
decision logic runs here, ever -- the tools just make data queryable
and let a decision get written down; deciding what to write is Epic 2's
job.

Decision on get_policy_limits, level/city not in limits.csv (flagged as
an open risk in SPEC-expense-epic-1's Story 3): reject with ValueError,
the same way get_claim/get_employee reject an unknown ID, rather than
silently falling back to a default or an adjacent city's limits. A
missing combo means the policy data itself is incomplete for that
employee, and that should surface loudly, not get guessed at by a tool.
In today's seed data every level x city combo is present (checked: 4
levels x 5 cities = 20/20), so this only bites if limits.csv changes.

The `decisions` table isn't in any seed CSV (load_seed.py only loads
read-only seed data), so record_decision creates it itself, once, with
CREATE TABLE IF NOT EXISTS. Each call inserts exactly one row -- no
upsert, no dedup -- per CAP-5's success criteria; anything smarter than
that (e.g. re-deciding a line item) is Epic 2/3 territory.
"""

import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "cases" / "expense" / "expense.db"

server = FastMCP("expense", log_level="WARNING")


def _query(sql: str, *params: str) -> list[dict]:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "expense.db not found. Load the data first: uv run python cases/expense/load_seed.py"
        )
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql, params)]


@server.tool()
def get_claim(claim_id: str) -> dict:
    """Return one expense claim by its ID (for example CL-2001): the employee_id and every line item on it."""
    claims = _query(
        "SELECT claim_id, employee_id, submitted_at, purpose FROM claims WHERE claim_id = ?",
        claim_id,
    )
    if not claims:
        raise ValueError(f"No claim with ID {claim_id}")
    claim = claims[0]
    claim["line_items"] = _query("SELECT * FROM line_items WHERE claim_id = ?", claim_id)
    return claim


@server.tool()
def get_employee(employee_id: str) -> dict:
    """Return an employee's level and city, given their employee_id (for example E-101)."""
    employees = _query(
        "SELECT employee_id, level, city FROM employees WHERE employee_id = ?", employee_id
    )
    if not employees:
        raise ValueError(f"No employee with ID {employee_id}")
    return employees[0]


@server.tool()
def get_policy_limits(level: str, city: str) -> dict:
    """Return the per-category CAD limits (meals, hotel, flight, ground) for a level and city."""
    rows = _query(
        "SELECT category, limit_cad FROM limits WHERE level = ? AND city = ?", level, city
    )
    if not rows:
        raise ValueError(f"No policy limits defined for level={level}, city={city}")
    return {row["category"]: row["limit_cad"] for row in rows}


@server.tool()
def record_decision(line_id: str, decision: str, clause: str) -> dict:
    """Record one decision (approve, flag, or reject) against a line item, citing the POLICY.md clause that decided it."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "expense.db not found. Load the data first: uv run python cases/expense/load_seed.py"
        )
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS decisions (line_id TEXT, decision TEXT, clause TEXT)"
        )
        conn.execute(
            "INSERT INTO decisions (line_id, decision, clause) VALUES (?, ?, ?)",
            (line_id, decision, clause),
        )
        conn.commit()
    return {"line_id": line_id, "decision": decision, "clause": clause}


if __name__ == "__main__":
    server.run()
