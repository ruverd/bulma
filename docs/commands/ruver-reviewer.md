# `/ruver-reviewer`

Alias: **`/reviewer`**. Graph engineer for **review**. Runs
[`/ruver-code-review`](ruver-code-review.md), classifies CI /
mergeability, optionally buses a `REVIEW_RESULT`.

Never merges. Not the fd worker `ruver-fd-reviewer`.

Skill: [`../../skills/ruver-reviewer`](../../skills/ruver-reviewer).

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
  → code_review     /ruver-code-review (spec-first, bind, high-risk critic)
  → diagnose        classify failures + mergeable
  → report          REVIEW_RESULT + pop if stacked
```

Draft, conflict, and CI-red **DEFER** are expected. That is a gate,
not a failed run.

## What the main thread does

1. Claim the lane. Second review while main is busy → one worker per PR.
2. Hand the diff to `/ruver-code-review` (one GitHub artifact).
3. Diagnose: CI red vs product vs merge conflict.
4. Report. If stacked, write `REVIEW_RESULT` and pop the bus.

Does **not** spawn developer or QA unless the user asks after the
report. Outbound fix is “tell the user” or LSTM on the same PR.

## vs LSTM vs code-review

| Command | Who | Job |
|---|---|---|
| `/ruver-reviewer` | reviewer | Orchestrate + diagnose CI |
| `/ruver-code-review` | engine | The GitHub review itself |
| `/ruver-lstm` | author | Patch the comments on the same branch |

## Never

- Merge.
- Spawn `ruver_developer` / `ruver_qa`.
- Post a `ci_pending` comment (wait instead).
- Confuse this with `ruver-fd-reviewer` (that is an fd node).

## Related

[`/ruver-code-review`](ruver-code-review.md) · [`/ruver-lstm`](ruver-lstm.md) ·
[`/ruver-bus`](ruver-bus.md)
