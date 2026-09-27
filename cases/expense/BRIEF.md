# Case A: expense claim reviewer

## The problem

Finance reviews every expense claim by hand. It takes a week, and two reviewers often reach different answers on the same claim. They want an agent that reviews each line item against the policy, cites the clause behind every decision, and leaves the money in a person's hands for big items.

## What the agent does

For each claim: read it, look up the employee, look up the limits that apply, then decide every line item: **approve**, **flag** or **reject**, with the clause from `POLICY.md`. It records each decision in a `decisions` table. Any approved item over $500 waits for a person's yes before it's paid.

## What's in this folder

- `POLICY.md`: the expense policy, with numbered clauses. It covers every edge case in the data.
- `seed/claims.csv`, `seed/line_items.csv`, `seed/employees.csv`, `seed/limits.csv`: 40 claims and 159 line items.
- `eval/labelled.csv`: the right decision and clause for every line item on the first 30 claims. Build and test against these.

The last 10 claims have no labels here. They're the holdout set, scored live during the demos.

## Tools the agent needs

Build these in an MCP server over a SQLite database you load from `seed/`:

| Tool | Returns |
|---|---|
| `get_claim(claim_id)` | the employee ID and the line items |
| `get_employee(employee_id)` | their level and city |
| `get_policy_limits(level, city)` | the limit for each category |
| `record_decision(line_id, decision, clause)` | writes one decision to the `decisions` table |

## How it's checked

- Code checks: the decision matches on every line item, the cited clause matches the label, and each claim's reimbursable total (the sum of approved items) matches.
- One judge: is each explanation clear, and does it cite the right clause?

## Out of scope

Paying anyone, emailing employees, and any interface beyond the dashboard at 3:00.
