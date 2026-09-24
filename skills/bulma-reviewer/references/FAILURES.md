# Failure classes (reviewer)

Every relevant failure gets exactly one class.

| Class | Evidence | Action |
|---|---|---|
| `PR FAILURE` | Diff introduced or exposed it (logic, types, contract, missing behavior) | Recommend or apply a focused fix if authorized |
| `TEST FAILURE` | Fixture, mock, expectation, or flake — not the product | Fix test only with evidence the product is correct. Never weaken |
| `INFRASTRUCTURE FAILURE` | Runner, registry, network, Actions, external outage | Retry; no app-code workaround |
| `ENVIRONMENT FAILURE` | Missing env, service, credentials, DB | Diagnose; never print secrets |
| `BRANCH FAILURE` | Conflicts, stale head, wrong base, integration with base | Fix branch state, then re-check CI |
| `UNRELATED FAILURE` | Same fail on base / untouched code / predates PR / many PRs | Do not pad this PR. Tracker issue if needed |
| `HUMAN INTERVENTION REQUIRED` | Ambiguous product, security, missing creds, destructive, architecture | Escalate |

## Base-branch compare

Use when class is uncertain:

- Same fail on base?
- Did the PR touch the failing code?
- Is the branch behind base?

That split is **PR regression vs pre-existing**.

## Mergeability

```text
CI = fully green
AND
mergeability = MERGEABLE
```

Not mergeable: `CONFLICTING`, `DIRTY`, `BLOCKED`, `UNKNOWN`, pending.
Never claim MERGEABLE without `gh pr view`.
