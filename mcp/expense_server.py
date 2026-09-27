"""MCP server that gives the expense reviewer agent access to
cases/expense/expense.db over stdio.

Story 1.2 (this file's first version): CAP-2 (get_claim) and CAP-3
(get_employee) only. Later stories in Epic 1 add get_policy_limits,
record_decision, and the cross-claim line-item lookup to this same
server -- no policy or decision logic runs here, ever.
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


if __name__ == "__main__":
    server.run()
