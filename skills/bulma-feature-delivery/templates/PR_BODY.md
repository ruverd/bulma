## What changed

<!-- One or two sentences. Name the mechanism, not the feeling. Evidence: attached PNG, fenced output, or n/a. -->

## Ticket

<!-- Tracker id and URL, or n/a. Evidence: URL or n/a. -->

## How tested

<!-- Commands, recorded exit codes and receipt paths from runtime evidence cited in STATE. Do not infer success from a log-summary command. Evidence: fenced output or n/a. -->

## How to test

<!-- Steps a reviewer follows to see the change work: setup, route or command, input, expected result. Concrete enough to run without reading the diff. Keep the repo template's own how-to-test section if it has one; add this one only when it is missing. Evidence: numbered steps. -->

## Before → After

<!-- Same route and viewport as Before. New screen: `Before: n/a (new screen)`. Evidence: attached PNGs. -->

Before:

After:

## Risks

<!-- What could break, and why it is acceptable. Evidence: attached PNG, fenced output, or n/a. -->

## Rollout

<!-- Paired PRs in other repos and the safe merge and deploy order, flag and default, and how to revert (one command, or why a revert is unsafe after a migration). Evidence: links or n/a. -->

## Agent run

<!-- Required in every PR, including each stacked child. Always the last section. Follow bulma-host PR_ATTRIBUTION.md. Model and reasoning effort: actual executing session values, else `unknown` per field. Multiple contributors: list each distinct model/effort pair and role. Time: wall clock from the first branch commit (or STATE start) to PR open, rounded to minutes. Tokens: the host-reported total from `session_usage`, else `n/a`. Never estimate a number. On update, preserve earlier contributions and refresh this section. -->

- Model:
- Reasoning effort:
- Code review model:
- Code review reasoning effort:
- Time:
- Tokens:

<!-- Model/Reasoning effort identify implementation contributors. Code review fields identify the reviewer responsible for the pre-PR verdict, copied from its result, including role/pair entries when multiple reviewers contributed. Never substitute the shipper's or critic's settings. If review ran but a field is unavailable, use `unknown`. If no review ran, write `not run` and the reason; attribution does not bypass a required review gate. -->
