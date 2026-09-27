# Case A: expense claim reviewer

## Done when

- An MCP server over a local SQLite database (loaded from `seed/`) exposes four tools: `get_claim(claim_id)`, `get_employee(employee_id)`, `get_policy_limits(level, city)`, `record_decision(line_id, decision, clause)`.
- For every line item on a claim, the agent records exactly one decision (`approve`, `flag`, `reject`) and the `POLICY.md` clause that decided it, applying clauses in the precedence order `POLICY.md` sets out: section 3, then 5.1, then 1.2, then 4.1, then the limits (sections 2 and 6), then 1.3.
- Any `approve` decision on a line item over $500 is recorded but held — it is not treated as paid until a person says yes. The agent decides; it never releases money on its own.
- Run against `eval/labelled.csv` (the first 30 claims), the agent's output passes:
  - **Code checks:** decision matches on **[ASSUMPTION: 90%]** of line items, cited clause matches on **[ASSUMPTION: 90%]** of line items, and each claim's reimbursable total (sum of approved items) matches exactly for **[ASSUMPTION: 90%]** of the 30 claims.
  - **Judge:** mean score of **[ASSUMPTION: 0.8 out of 1]** across explanation clarity and correct-clause citation.
- The last 10 claims (no labels provided) score live in the same way during the 3:00pm demo.

## Must not change

- Python 3.12 or newer, with `uv`.
- `POLICY.md`, `seed/`, and `eval/labelled.csv` inside `cases/expense/` are read-only.
- Architecture: a LangChain agent over MCP tools, traced and evaluated in MLflow (`sqlite:///mlflow.db`).
- The $500 human-approval gate is not optional, in any build shortcut or demo path.

## Open architecture question

- Same-day aggregation (meals, ground transport), duplicate detection across an employee's claim history, and per-night/per-trip math are inherently cross-item. Whether that logic lives inside the agent's reasoning loop or gets pushed into a tool (e.g. `get_claim` pre-aggregates, or a dedicated `check_duplicates` tool) is not yet decided — resolve this before `/bmad-spec` locks the contract.

## Out of scope

- Actually paying anyone.
- Emailing employees.
- Any interface beyond the 3:00pm demo dashboard.
