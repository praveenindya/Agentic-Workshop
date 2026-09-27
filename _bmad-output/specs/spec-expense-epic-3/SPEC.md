---
id: SPEC-expense-epic-3
companions: [../../../cases/expense/BRIEF.md, ../spec-expense-epic-2/SPEC.md]
sources: [../../planning-artifacts/prds/prd-Agentic-Workshop-2026-09-27/prd.md]
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 3: measure the agent

## Why

Epic 2 gives the expense case an agent that decides; nothing yet says how well it decides. `POLICY.md` is a deterministic rule set — every line item has exactly one correct decision and clause — so this isn't a soft quality bar, it's a correctness check. Epic 3 closes the loop: an MLflow eval that runs the agent over the 30 labelled claims, scores every line item in code plus once by an independent LLM judge, and reports the numbers, so the 3:00pm demo has a measured baseline before the holdout claims run live.

## Capabilities

- **CAP-1**
  - **intent:** A person can run one command to evaluate the Epic 2 agent over every labelled line item.
  - **success:** `uv run python cases/expense/eval/run_eval.py` builds inputs from every row of `cases/expense/eval/labelled.csv`, drives the Epic 2 agent through `mlflow.genai.evaluate`, and logs exactly one MLflow run under the `expense-reviewer` experiment.

- **CAP-2**
  - **intent:** Every line item's decision is checked against its label.
  - **success:** `decision_match` scores 1 when the agent's `decision` for a line item equals `expected_decision`, 0 otherwise, across every labelled row.

- **CAP-3**
  - **intent:** Every line item's cited clause is checked against its label.
  - **success:** `clause_match` scores 1 when the agent's cited clause equals `expected_clause`, 0 otherwise.

- **CAP-4**
  - **intent:** Each labelled claim's reimbursable total is checked for correctness, not just its individual line items.
  - **success:** `reimbursable_total_match` scores 1 per claim when the sum of that claim's `line_items.csv` amounts on rows labelled `expected_decision == approve` equals the sum of amounts the agent itself decided `approve` for that claim, 0 otherwise.

- **CAP-5**
  - **intent:** An independent LLM judges whether each decision's explanation is clear and cites the right clause.
  - **success:** `rationale_judge` calls `ChatGroq` with the model from `JUDGE_MODEL` (default `openai/gpt-oss-120b`) and the key from `GROQ_API_KEY`, returning `pass`/`fail` plus a one-line reason for each labelled line item. It never reads `GEMINI_API_KEY`.

- **CAP-6**
  - **intent:** After the run, a person can see and reuse the eval's scores and the held-for-approval count without opening the MLflow UI.
  - **success:** The script prints the mean of `decision_match`, `clause_match`, `reimbursable_total_match`, and `rationale_judge`, plus the count of line items held for approval (`decision == approve and amount > 500`) across the run, and writes the same numbers to `cases/expense/eval/latest_report.json`.

## Constraints

- Built with `mlflow.genai.evaluate`, not a hand-rolled scoring loop.
- Read-only, unchanged: `eval/labelled.csv`, `POLICY.md`, and Epic 2's agent — `run_eval.py` calls the existing agent as-is, never edits its decision logic or prompts.
- `rationale_judge` always calls `ChatGroq` via `JUDGE_MODEL`/`GROQ_API_KEY`, regardless of the agent's `PROVIDER` setting — never reads `GEMINI_API_KEY`, so it never competes for the agent's Gemini quota.
- No scorer or report step treats `flag` as a safe default — defaulting ambiguous items to `flag` would inflate `decision_match` on some rows while producing an agent nobody trusts (PRD's SM-C1 counter-metric).
- Only the 30 labelled claims are scored by this epic. The 10 holdout claims are scored live at the demo using this same harness, not a separate one.
- `cases/expense/eval/latest_report.json` is the only new file this epic writes outside MLflow's own store — a separate path from triage's `eval/latest_report.json` so the two cases' reports never collide.

## Non-goals

- Dashboards, CI, and hosting.
- Tuning the agent to raise its score.
- Scoring the 10 holdout claims as part of this epic's own success signal — that happens live at the demo, using the harness this epic builds.

## Success signal

`uv run python cases/expense/eval/run_eval.py` runs start to finish with no person present, scoring all 30 labelled claims' line items on all four scorers. `decision_match` and `clause_match` and `reimbursable_total_match` read 100% against `eval/labelled.csv` (a deterministic rule set has no room for a passing-but-wrong score), `rationale_judge` reads at least 0.75, and the printed/JSON report shows all four means plus the held-for-approval count.

## Assumptions

- `decision_match`, `clause_match`, and `reimbursable_total_match` targets are 100%, per the PRD — hard targets, not soft goals, since `POLICY.md` is deterministic.
- The PRD's SM-3 covers both clause citation and judge quality under one label; disambiguated here as two separate scorers — `clause_match` (exact match, 100%) and `rationale_judge` (LLM judge, 0.75 mean, `pass`=1/`fail`=0, matching triage's `rationale_judge` convention).
- The held-for-approval count in the report is computed the same way Epic 2 computes it (`decision == approve and amount > 500`), read from the run's outputs, not a new stored field.

## Open Questions

None carried forward from Epic 2 apply directly to this epic's own scope; Epic 2's precedence-tie open question would surface here as a `decision_match`/`clause_match` shortfall if it exists, not as a new question for this spec.
