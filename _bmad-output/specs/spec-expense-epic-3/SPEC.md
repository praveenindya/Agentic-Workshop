---
id: SPEC-expense-epic-3
companions: [../spec-expense-epic-2/SPEC.md, ../../../cases/expense/POLICY.md, ../../../cases/expense/BRIEF.md, ../../../cases/expense/eval/labelled.csv]
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 3: measure the expense agent

## Why

Epic 2 gives the case an agent that decides; nothing yet says how well it decides. Epic 3 closes the loop: an MLflow eval that runs the agent over the 30 hand-labelled claims, scores every line item against `eval/labelled.csv` in code plus once by an independent judge, and reports the numbers — so the PRD's SM-1/SM-2/SM-3 targets are measured, not asserted. It also has to serve the 3pm demo directly: the last 10 claims are unlabelled and get scored live, one at a time, in front of the room.

## Capabilities

- **CAP-1**
  - **intent:** A person can run an entrypoint to evaluate the Epic 2 agent over every claim in `eval/labelled.csv` in one pass.
  - **success:** The script builds inputs from all 30 labelled claims, drives the Epic 2 agent, and logs exactly one MLflow run.

- **CAP-2**
  - **intent:** Every line item's decision is checked against its label.
  - **success:** `decision_match` scores 1 when a line item's decision equals `expected_decision`, 0 otherwise, across all labelled line items.

- **CAP-3**
  - **intent:** Every line item's cited clause is checked against its label.
  - **success:** `clause_match` scores 1 when a line item's cited clause equals `expected_clause`, 0 otherwise.

- **CAP-4**
  - **intent:** Every claim's reimbursable total (sum of approved line items' amounts) is checked against the total implied by the labels.
  - **success:** `reimbursable_total_match` joins `eval/labelled.csv` against `seed/line_items.csv` by `line_id` to get amounts, sums amounts of agent-approved items per claim, and scores 1 when that equals the same sum computed from `expected_decision` labels, 0 otherwise.

- **CAP-5**
  - **intent:** A Groq-hosted model judges each line item's explanation clarity and clause-citation correctness (PRD SM-3).
  - **success:** The judge calls `ChatGroq` with the model from `JUDGE_MODEL` (default `openai/gpt-oss-120b`) and key from `GROQ_API_KEY`, returning `pass`/`fail` plus a one-line reason per line item. It never reads `GEMINI_API_KEY`.

- **CAP-6**
  - **intent:** The run's flag-rate is visible alongside the primary scores, so a trivial always-flag strategy (PRD's counter-metric SM-C1) can't hide behind a high match rate.
  - **success:** The printed output and report file both include the share of decisions that are `flag`, computed from the same run that produced CAP-2/CAP-3's scores.

- **CAP-7**
  - **intent:** After the run, a person can see and reuse the eval's scores without opening the MLflow UI.
  - **success:** The script prints the mean of `decision_match`, `clause_match`, `reimbursable_total_match`, and the judge pass rate, plus the flag-rate from CAP-6, and writes the same numbers to a report file.

- **CAP-8**
  - **intent:** The same judge-scoring pipeline can run against a single claim id that carries no label, independent of the full labelled batch.
  - **success:** Given one of the 10 holdout claim ids, the harness produces a decision, clause, and judge verdict for each of that claim's line items without requiring an `expected_decision`/`expected_clause` row to exist — usable live, one claim at a time, during the demo.

## Constraints

- Built with `mlflow.genai.evaluate`, not a hand-rolled scoring loop.
- Read-only, unchanged: `eval/labelled.csv`, `POLICY.md`, `BRIEF.md`, `seed/`, and Epic 2's agent behavior — this epic calls the existing agent as-is and never edits its decision logic, prompts, or policy handling.
- CAP-5's judge always calls `ChatGroq` via `JUDGE_MODEL`/`GROQ_API_KEY`, regardless of the agent's own `PROVIDER` setting, and never reads `GEMINI_API_KEY` — so it never competes for the agent's Gemini quota.
- No network calls beyond model APIs: CAP-2, CAP-3, CAP-4, and CAP-6 all run locally against labels and seed data; only the agent's own model call and CAP-5's Groq call cross the network.
- Unlike triage's Epic 3, no auto-approve-escalation handling is needed: the expense agent (Epic 2 CAP-7) never pauses mid-run for a human, so this eval never blocks on that axis at all.

## Non-goals

- Dashboards, CI, and hosting.
- Tuning the agent to raise its score.

## Success signal

The entrypoint runs start to finish with no person present for the 30 labelled claims, producing one MLflow run scored by all four scorers, printing their means plus the flag-rate, and writing those numbers to a report file. Separately, pointing the harness at any one of the 10 holdout claim ids produces a decision, clause, and judge verdict for that claim alone, ready for a person to score live at the demo.

## Assumptions

- Entrypoint assumed at `cases/expense/eval/run_eval.py`, report file at `cases/expense/eval/latest_report.json` — mirrors the triage case's `eval/run_eval.py` / `eval/latest_report.json` pattern.
- MLflow experiment reused as `expense-agent` (the same experiment Epic 2 assumed), not a separate eval-only experiment — matches how triage's Epic 3 logs into the agent's own experiment rather than a new one.
- CAP-5's judge reports pass/fail per line item, averaged as a pass rate against the 0.75 target — same treatment triage's judge used, since the PRD specifies the target at the WHAT level without prescribing a scale.

## Open Questions

- PRD's OQ-2 — hand-trace `POLICY.md`'s precedence order against all 30 labelled claims to confirm no genuine tie exists — is still unresolved. This epic's scorers assume `eval/labelled.csv` is internally consistent; that check should run before or during this epic's build, not be assumed clean.
