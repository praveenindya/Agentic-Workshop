# Ideal customer profile and lead rules

Every inbound lead gets a tier (hot, warm or cold), an owner, and a draft first reply. This file is read-only.

## 1. Who we sell to

- **1.1 Fit.** A lead fits when its company is in SaaS, Fintech, Healthcare or Logistics **and** has 200 to 5,000 employees. Company details come from `seed/companies.csv`. A company that isn't listed there does not fit.
- **1.2 Buying intent.** A lead shows intent when the message mentions pricing, a demo, a trial, a budget, this quarter, replacing a tool, a contract or a rollout.

## 2. Tiers

- **2.1 Always cold:** a personal email address (gmail.com, outlook.com, yahoo.com, hotmail.com), a competitor's domain (rivalflow.io, pipelinepro.com), or a message from a student, a job seeker or a vendor selling to us.
- **2.2 Hot:** fit and buying intent.
- **2.3 Warm:** fit or buying intent, but not both.
- **2.4 Cold:** neither.

## 3. Owners

- **3.1** An existing customer (status `customer` in `seed/crm_accounts.csv`) goes to their account owner, whatever the region.
- **3.2** Everyone else goes to the territory owner for the company's region, from `seed/territories.csv`. Churned customers and prospects count as everyone else.
- **3.3** No region (an unlisted company or a personal email) goes to Sales Ops.

## 4. The first reply

- **4.1** Write to the person by first name and answer what their message actually asked.
- **4.2** Keep it under 120 words and sign it with the owner's name.
- **4.3** Never quote prices, discounts or dates, and never claim anything that isn't in this file.
- **4.4** Cold leads get a short, polite reply that points them to the website.
- **4.5** No reply is sent until a person approves it. The agent saves it as a draft.
