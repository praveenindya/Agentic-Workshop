# Case B: inbound lead qualifier

## The problem

Sales reps lose hours every week on web leads that were never going to buy, while the good ones wait a day for an answer. They want an agent that reads each new lead, decides how hot it is, routes it to the right rep, and drafts a first reply that the rep approves with one click.

## What the agent does

For each lead: read the message, look up the company, check whether they're already a customer, and find the right owner. Then give the lead a tier (**hot**, **warm** or **cold**), pick the owner, and write a first reply following `ICP.md`. Every reply waits for a person's yes before it's sent.

## What's in this folder

- `ICP.md`: who we sell to, the tier rules, the routing rules and the reply rules. It covers every edge case in the data.
- `seed/leads.csv`, `seed/companies.csv`, `seed/crm_accounts.csv`, `seed/territories.csv`: 40 leads and the data behind them.
- `eval/labelled.csv`: the right tier and owner for the first 30 leads, and whether each is an existing customer. Build and test against these.

The last 10 leads have no labels here. They're the holdout set, scored live during the demos.

## Tools the agent needs

Build these in an MCP server over a SQLite database you load from `seed/`:

| Tool | Returns |
|---|---|
| `get_lead(lead_id)` | the message and the email domain |
| `lookup_company(domain)` | size, industry and region |
| `find_crm_account(domain)` | whether they're a customer, and the account owner |
| `get_territory_owner(region)` | the rep for a new lead |
| `record_decision(lead_id, tier, owner, reply)` | saves the decision and the draft reply |

## How it's checked

- Code checks: the tier matches the label, the owner matches the label, and existing customers are caught.
- One judge: is the draft reply personal to the lead's message, with no made-up claims?

## Out of scope

Actually sending email, booking meetings, and any interface beyond the dashboard at 3:00.
