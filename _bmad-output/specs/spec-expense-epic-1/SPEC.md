---
id: SPEC-expense-epic-1
companions: [../../../cases/expense/POLICY.md, ../../../cases/expense/BRIEF.md]
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 1: expense data and tools foundation

## Why

The Expense Claim Reviewer's whole premise — a person can trust that policy gets applied the same way every time — depends on an agent that can actually reach the claim, employee, and policy data through a stable tool contract. Epic 1 builds that foundation: no decisions get made yet, but Epic 2 (the reviewer agent) and Epic 3 (the eval) cannot be built or tested until this data is queryable and these tools exist. This mirrors the shape of Saturday's triage Epic 1 exactly — schema and loader first, agent second.

## Capabilities

- **CAP-1**
  - **intent:** A person can load `cases/expense/seed/*.csv` into a local SQLite database with one command.
  - **success:** Running the load command creates tables matching the CSV columns for `claims`, `employees`, `limits`, and `line_items`; running it twice produces an identical database.

- **CAP-2**
  - **intent:** An MCP tool returns a claim's employee and line items.
  - **success:** `get_claim(claim_id)` called against a known seed claim ID returns the correct `employee_id` and the full list of that claim's line items with all their fields.

- **CAP-3**
  - **intent:** An MCP tool returns an employee's level and city.
  - **success:** `get_employee(employee_id)` called against a known seed employee ID returns the correct `level` and `city`.

- **CAP-4**
  - **intent:** An MCP tool returns the policy limits for a given level and city.
  - **success:** `get_policy_limits(level, city)` returns the correct per-category limit values from `limits.csv` for that level/city pair.

- **CAP-5**
  - **intent:** An MCP tool records one decision against a line item.
  - **success:** `record_decision(line_id, decision, clause)` writes exactly one row to a `decisions` table with the given line ID, decision, and clause.

- **CAP-6**
  - **intent:** An MCP tool returns an employee's line items across all of their existing claims in the dataset, so duplicate detection (`POLICY.md` §5.1) can compare a line item against everything already on record for that employee. This is a plain query over the existing `claims`/`line_items` tables joined by `employee_id` — not a separate history log or temporal tracking mechanism.
  - **success:** Called against a seed employee with more than one claim, the tool returns line items from every one of that employee's existing claims, not just a single `claim_id`'s worth.

## Constraints

- Python 3.12 or newer, with `uv`.
- `cases/expense/seed/`, `POLICY.md`, `BRIEF.md`, and `eval/labelled.csv` are read-only.
- No network calls and no API keys in this epic — data loading and tool-contract work only, no LLM involved.
- Saturday's triage code and `app.db` stay untouched; this epic's database and MCP server are new, separate artifacts, not additions to the existing triage schema.

## Non-goals

- Not deciding any line item — no `POLICY.md` precedence logic runs in this epic.
- Not the LangChain agent that will call these tools — that's Epic 2.
- Not the eval harness, judge, or MLflow scoring — that's Epic 3.
- Not the $500 human-approval gate — that's FR-2 logic, and it lives in Epic 2.

## Success signal

Running the load command twice produces byte-for-byte the same database. Each of the six MCP tools, called by hand against known seed data, returns exactly the shape this SPEC describes — including CAP-6 returning items from more than one claim for an employee who has more than one. Nothing decides, flags, or rejects anything; the foundation is queryable, nothing more.

## Assumptions

- New MCP server module lives at `mcp/expense_server.py`, separate from `mcp/triage_server.py`, and this epic's database is a new file separate from `app.db` — `BRIEF.md` names neither; this keeps the two workshop cases isolated per the repo's own convention (`AGENTS.md`: "Keep Saturday's triage code working; don't change it for Sunday's case").

## Open Questions

- Exact tool name/signature for CAP-6 — e.g. `get_employee_line_items(employee_id)`, or an extended return shape on `get_claim`? The underlying approach is settled (plain join over existing data, no separate tracking mechanism); only the naming/signature is still a build-time call.
