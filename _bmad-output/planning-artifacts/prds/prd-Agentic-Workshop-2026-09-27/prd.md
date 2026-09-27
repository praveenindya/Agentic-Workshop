---
title: Expense Claim Reviewer
created: 2026-09-27
updated: 2026-09-27
status: draft
---

# PRD: Expense Claim Reviewer
*Working title — confirm.*

## 0. Document Purpose
One-page MVP PRD, single-agent scope, for the workshop's internal build. Built from `brief-Agentic-Workshop-2026-09-27/brief.md` (adversarially reviewed). Read alongside `cases/expense/BRIEF.md`, `POLICY.md`, and `INTENT.md` — this PRD doesn't restate the policy, it defines what the agent must do with it.

## 1. Vision
Finance currently reviews every expense claim by hand; the core failure isn't speed, it's **fairness** — two reviewers applying the same written policy to the same claim can land on different verdicts. This agent applies `POLICY.md` identically every time: one line item, one decision, one cited clause, no drift between runs or reviewers.

## 2. Target User
### 2.1 Jobs To Be Done
- As a Finance reviewer, I need every line item decided against the same policy, the same way, so I stop being the tiebreaker between my own and a colleague's judgment calls.
- As the person who releases payouts over $500, I need a single decision + clause to say yes/no to, not a full claim to re-review. This is a distinct role from the primary reviewer — need not be the same person.

*Single-operator internal tool — full UJ narratives skipped per template guidance; the JTBD above is the whole story.*

## 3. Glossary
- **Line item** — one claimed expense on a claim; gets exactly one decision.
- **Decision** — `approve`, `flag`, or `reject`.
- **Clause** — the numbered `POLICY.md` rule that determined the decision.
- **Claim** — a set of line items submitted together by one employee.
- **Reimbursable total** — sum of a claim's approved line items.

## 4. Features

### 4.1 Policy-Driven Line-Item Review
**Description:** For each claim, the agent looks up the employee (level, city) and applicable limits, then decides every line item using `POLICY.md`'s fixed precedence (§3 → 5.1 → 1.2 → 4.1 → limits §2/§6 → 1.3), recording the decision and clause via `record_decision`. §5.1 duplicate detection needs a fifth tool — cross-claim employee history — beyond the original four; the duplicate check only fires when that history is available (i.e. build the tool, gate the check on it).

**Functional Requirements:**

#### FR-1: Decide a line item
Agent can decide any line item as `approve`/`flag`/`reject`, citing the deciding clause, via the MCP tools (`get_claim`, `get_employee`, `get_policy_limits`, `record_decision`, and a new `get_employee_history(employee_id)`-shaped tool for cross-claim duplicate detection).
**Consequences (testable):** Every line item in a claim gets exactly one recorded decision + clause; clause matches `POLICY.md`'s precedence order for that item's conditions; a line item matching an earlier item (same date, merchant, amount) from the same employee's history is rejected under §5.1, even when the earlier item is on a different claim.

#### FR-2: Hold high-value approvals for a human
Any `approve` over $500 is recorded but not released; a person must say yes before payout. The agent's responsibility ends at recording the decision and flagging it as held — the approval interaction itself (a person reviewing and saying yes or no) and any payout execution happen entirely outside this system. A "no" requires no state change in `decisions`: the agent's `approve` + clause record stands as its decision either way: whether the money moves is a downstream human process this system never touches.
**Consequences (testable):** No approved line item over $500 is marked paid without an explicit human yes; the agent has no path to bypass this gate; the agent never writes or expects a "declined by approver" state — that state, if it exists at all, lives outside this system.

**Out of Scope:** actually releasing payment (any amount) — a person always does this, per `BRIEF.md`.

## 5. Non-Goals (Explicit)
- Not paying anyone, ever — human-in-the-loop for money movement, full stop.
- Not emailing employees or providing any interface beyond the 3:00pm demo dashboard.
- Not a multi-agent system — one agent, one MCP server, per this PRD's scope.
- Not specifying the approver's yes/no interface or how a `flag`ged line item gets resolved by a human — both are real interaction design work `[NOTE FOR PM: needed before this is buildable end-to-end; scope into a UX pass, not silently assumed]`, explicitly deferred out of this one-page MVP PRD.

## 6. MVP Scope
### 6.1 In Scope
- FR-1, FR-2. MLflow tracing. Code + judge eval against `eval/labelled.csv` (first 30 claims); last 10 score live at the demo.

### 6.2 Out of Scope for MVP
- Appeals/override workflow for a disputed decision — `[NOTE FOR PM]` this is in tension with the PRD's own "fairness" vision; revisit if a v2 happens.
- Any UI beyond the demo dashboard.

## 7. Success Metrics
**Primary**
- **SM-1**: Decision + clause match rate on `eval/labelled.csv`, target **100%** — `POLICY.md` is a deterministic rule set with one objectively correct decision+clause per line item; the 30 labelled claims are the ground truth, not a soft target to approximate. Validates FR-1.
- **SM-2**: Reimbursable-total exact match per claim, target **100%** of the 30 labelled claims — follows from SM-1: if every line item matches, every total matches. A shortfall here with SM-1 passing indicates a totals-computation bug, not a policy-application error.
- **SM-3**: Judge score — explanation clarity + correct clause citation, target 0.75 of 1. Validates FR-1.

**Counter-metrics (do not optimize)**
- **SM-C1**: Do not optimize match rate by defaulting ambiguous items to `flag` — flagging everything trivially raises accuracy on labelled data while producing an agent nobody trusts. Counterbalances SM-1/SM-2.

## 8. Open Questions
1. Exact tool signature for cross-claim employee history — `get_employee_history(employee_id)` shape, or extend an existing tool? Decide at `/bmad-architecture`.
2. **Pre-build check:** hand-trace `POLICY.md`'s precedence order (§3 → 5.1 → 1.2 → 4.1 → limits → 1.3) against all 30 claims in `eval/labelled.csv` to confirm every line item resolves to exactly one clause with no genuine tie. SM-1/SM-2's 100% targets assume this holds; if a tie surfaces, those targets need revisiting before build starts, not after.
3. Who resolves a `flag`ged line item, and how? Undefined — likely a UX-pass question alongside the approver interface (see §5).

## 9. Assumptions Index
*None remaining — all three prior assumptions (approver role, duplicate-history tool, judge target) resolved; SM-1/SM-2 now anchor directly to `eval/labelled.csv` rather than an inferred percentage.*
