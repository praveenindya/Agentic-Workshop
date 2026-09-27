---
title: Expense Claim Reviewer
status: draft
created: 2026-09-27
updated: 2026-09-27
---

# Product Brief: Expense Claim Reviewer

## Executive Summary

Finance reviews every expense claim by hand today, and the real cost isn't the week-long turnaround — it's that two reviewers looking at the same claim often land on different decisions. That inconsistency reads as arbitrary to the employees on the receiving end. This brief covers an agent that reviews each line item against `POLICY.md`, decides approve/flag/reject, and cites the exact clause behind every call — the same policy, applied the same way, every time. Anything over $500 stays in a person's hands to actually pay; the agent decides, it never releases money.

## The Problem

Finance manually reviews 40 claims / 159 line items per cycle against a policy (`POLICY.md`) that is genuinely detailed — precedence rules, per-category limits by level and city, duplicate detection, IT pre-approval codes. The rules are not the problem. The problem is that two humans applying the same written rules to the same claim can reach different verdicts. [ASSUMPTION: this shows up as employees complaining a colleague's near-identical claim was treated differently, and reviewers spending time re-litigating each other's calls rather than reviewing new claims.] The week-long cycle is real but secondary — it's a symptom of reviewer time being spent on friction, not proof the process itself is broken.

## The Solution

For each claim: look up the employee (level, city), pull the limits that apply, and decide every line item — approve, flag, or reject — citing the `POLICY.md` clause that decided it, applying clauses in the fixed precedence order the policy sets (section 3 → 5.1 → 1.2 → 4.1 → limits → 1.3). Built as a LangChain agent over four MCP tools (`get_claim`, `get_employee`, `get_policy_limits`, `record_decision`) on a local SQLite database, same architecture pattern as the workshop's Saturday triage build, traced in MLflow. Any approved line item over $500 is recorded but held for a person's explicit yes before it pays out — the agent never releases money on its own.

## Who This Serves

**Primary user: Finance reviewers.** They stop manually cross-referencing every line item against the policy and instead review the agent's decisions plus their cited clauses — same rules, applied identically every time, freeing their time for genuine edge cases and reviewer judgment calls the agent should never make on its own.

**Secondary user:** [ASSUMPTION: the person who approves >$500 payouts — a distinct, lighter-weight touchpoint than the full reviewer role. They see one decision and one clause, not a whole claim, and their only job is the yes/no on releasing money. If this is actually the same person as the primary reviewer, or if the employee submitting the claim should count as a secondary user too, that changes this section — flag for correction.]

## Success Criteria

Because the driving problem is **fairness** (consistency across similar claims), not raw throughput, success is measured as: does the agent produce the *same* decision and clause for equivalent line items, every time, matching the policy's own intended outcome — not just "did it get most of them right."

Checked against `eval/labelled.csv` (first 30 claims):
- **Code checks:** decision matches on **[ASSUMPTION: 90%]** of line items, cited clause matches on **[ASSUMPTION: 90%]** of line items, and each claim's reimbursable total matches exactly for **[ASSUMPTION: 90%]** of the 30 claims.
- **Judge:** mean score of **[ASSUMPTION: 0.8 out of 1]** across explanation clarity and correct-clause citation.

The last 10 claims (unlabelled, held out) score live at the 3:00pm demo the same way.

## Scope

**In:** the four MCP tools, policy-driven line-item decisions with clause citations, the $500 human-approval gate, MLflow tracing, and the code + judge eval above.

**Out:** actually paying anyone, emailing employees, any interface beyond the 3:00pm demo dashboard. [ASSUMPTION: cross-item math — same-day meal/ground-transport aggregation, duplicate detection across an employee's history, per-night/per-trip logic — is in scope for correctness but its *implementation location* (agent reasoning loop vs. a dedicated tool) is still an open architecture decision, not yet resolved.]
