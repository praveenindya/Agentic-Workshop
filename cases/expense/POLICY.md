# Expense policy

Every line item on a claim gets exactly one decision (approve, flag or reject) and the clause that decided it. This file is read-only.

## 1. General

- **1.1** Each line item is decided on its own. A claim can mix approved, flagged and rejected items.
- **1.2** Expenses must be claimed within 60 days. An item dated more than 60 days before the claim's submission date is rejected.
- **1.3** Any item over $25 needs a receipt. An item over $25 without a receipt is flagged for follow-up.
- **1.4** All amounts are in Canadian dollars.

## 2. Limits

Limits depend on the employee's level (L1 to L4) and the city where the expense happened. They are in `seed/limits.csv`.

- **2.1** Meals are limited per day. Add up every meal on the same day; each meal that day gets the day's decision.
- **2.2** Hotels are limited per night. Each line is one night.
- **2.3** Flights are limited per trip. Each line is one trip.
- **2.4** Against any limit in section 2 or 6: at or under the limit, approve. Over the limit by 20% or less, flag. More than 20% over, reject.

## 3. Not reimbursable

- **3.1** Alcohol is never reimbursed. Reject it.
- **3.2** Personal expenses (gyms, entertainment, clothing) are never reimbursed. Reject them.
- **3.3** Parking tickets and traffic fines are never reimbursed. Reject them.

## 4. Software and equipment

- **4.1** Software and equipment need IT pre-approval. Approve them only when the description includes an IT approval code (ITA- followed by digits); otherwise reject.

## 5. Duplicates

- **5.1** An item with the same date, merchant and amount as an earlier item from the same employee is a duplicate. Reject the later one.

## 6. Ground transport

- **6.1** Taxis, rideshares and trains are limited per day, like meals (add up the day). The limit comes from `seed/limits.csv` under `ground`.

## 7. Approval

- **7.1** Any approved item over $500 is paid only after a person says yes. The agent records the decision; a person releases the payout.

## When more than one clause applies

Use the first that applies, in this order: section 3, then 5.1, then 1.2, then 4.1, then the limits (sections 2 and 6), then 1.3. If none applies, approve under the category's clause (2.1 meals, 2.2 hotels, 2.3 flights, 6.1 ground transport).
