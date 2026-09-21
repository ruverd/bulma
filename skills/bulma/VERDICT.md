# Verdict

How `review.severity` and `review.verdict` gate an APPROVE. Both fire in
`ruver-code-review` at the `verdict` node. The arithmetic stays in that
graph's tables; Jev answers the two judgment calls those tables read.

## What actually decides an approve

The verdict table is already deterministic: count surviving blockers and
majors, check the coverage rows, check CI. Nothing in that counting is
uncertain. Two inputs to it are:

1. **Which tier a finding belongs to.** A `nit` never blocks and a `major`
   always does, so the tier *is* the approve lever. `review.severity` asks it
   per surviving finding, new and carried.
2. **Whether the review actually covered the diff, and whether anything
   blocker-level stayed open.** `review.verdict` asks both once, after every
   finding has a tier.

## Severity, asymmetric on purpose

| Jev vs the reviewer | What happens |
|---|---|
| Jev raises the tier, acted | raise it |
| Jev lowers the tier, acted, `introduced_by_pr` decisive-no | lower it — this is the pre-existing clause, the only downgrade Jev can make |
| Jev lowers the tier, acted, `introduced_by_pr` anything else | the reviewer's tier stands |
| undecided, or below `act_at` | the reviewer's tier stands |

The asymmetry mirrors `qa.gate`, where Jev can hand a finding to triage but
can never turn it into a PASS. Here Jev can make a review stricter freely,
and can only relax it through a rule the graph already has in writing:
problems a PR merely touches are nits.

`act_at` is 0.80 on the tier and 0.85 on `introduced_by_pr`, so a downgrade
needs both a confident tier and a confident pre-existing call.

## Verdict

| Answer | Effect |
|---|---|
| `coverage_complete` decisive-no | **DEFER** `reason=coverage` |
| `blocking_uncertainty` decisive-yes | **DEFER** `reason=uncertainty` |
| both the other way | the verdict table's own row for the counts it already has |
| either undecided | the verdict table as written |

Jev never produces an APPROVE on its own. Every gate in front of the verdict
still holds: CI green (or an explicit force run), full coverage rows, and a
marker that proves a pass actually read code. Jev can only turn an APPROVE
the table would have posted into a DEFER, or leave it alone.

## State

Send the finding and its hunk, not the file. Send the coverage table as the
reviewer wrote it, not the diff it summarizes. Caps are in
[HOOKS.md](HOOKS.md); the review of a large PR is many small requests, one
per finding, plus one for the verdict.

## Power

Both hooks are `stakes: high`. Under `shadow` they log and change nothing,
which is the honest way to start: run 20 or more reviews, then read
`/bulma report` for `agree%` against the reviewer's own tiers before letting
either one act ([POWER.md](POWER.md)). A `reversed` outcome on
`severity` — a later review or `ruver-lstm` reproducing something Jev called
a nit — is the signal to raise the threshold back up.
