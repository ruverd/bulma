# `/bulma-reviewer`

Alias: **`/reviewer`**. Graph engineer for **review**. Runs
[`/bulma-code-review`](bulma-code-review.md), classifies CI /
mergeability, optionally buses a `REVIEW_RESULT`.

Never merges. Not the fd worker `bulma-fd-reviewer`.

Skill: [`../../skills/bulma-reviewer`](../../skills/bulma-reviewer).

## When

- `/reviewer https://github.com/org/repo/pull/99`
- `/reviewer owner/repo#99`
- `/reviewer` on the current branch’s PR
- Envelope: `REVIEW_REQUEST`

`--force` reviews while CI is red. Pending required CI waits 5m
and does **not** post (`wait_ci`).

## Graph

```
args or REVIEW_REQUEST
  → admit           idle → main; busy or 2+ PRs → worker+worktree
  → resolve
  → wait_ci         required CI pending — 5m wake, no PR comment
  → code_review     /bulma-code-review (spec-first, bind, high-risk critic)
  → diagnose        classify failures + mergeable
  → report          REVIEW_RESULT + pop if stacked
```

Draft, conflict, and CI-red **DEFER** are expected. That is a gate,
not a failed run.

## What the main thread does

1. Claim the lane. Second review while main is busy → one worker per PR.
2. Hand the diff to `/bulma-code-review` (one GitHub artifact).
3. Diagnose: CI red vs product vs merge conflict.
4. Report. If stacked, write `REVIEW_RESULT` and pop the bus.

Does **not** spawn developer or QA unless the user asks after the
report. Outbound fix is “tell the user” or LSTM on the same PR.

## vs LSTM vs code-review

| Command | Who | Job |
|---|---|---|
| `/bulma-reviewer` | reviewer | Orchestrate + diagnose CI |
| `/bulma-code-review` | engine | The GitHub review itself |
| `/bulma-lstm` | author | Patch the comments on the same branch |

## Never

- Merge.
- Spawn `bulma_developer` / `bulma_qa`.
- Post a `ci_pending` comment (wait instead).
- Confuse this with `bulma-fd-reviewer` (that is an fd node).

## Related

[`/bulma-code-review`](bulma-code-review.md) · [`/bulma-lstm`](bulma-lstm.md) ·
[`/bulma-bus`](bulma-bus.md)
