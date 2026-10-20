# `/bulma-reviewer`

Alias: **`/reviewer`**. Graph engineer for **review**. Runs
[`/bulma-code-review`](bulma-code-review.md), classifies CI /
mergeability, optionally buses a `REVIEW_RESULT`.

Never merges. Not the fd worker `bulma-fd-reviewer`.

Engine preflight reads review discussions and AI QA, rechecks the live head
before publication, proves CI ran on that commit, and checks caller contracts
outside the diff. Open concerns or our own Critical/High block approval.
Sensitive paths require human sign-off. Another review is never dismissed.
On Codex, invoke `$bulma-reviewer` or select it through `/skills`.

Review preserves existing worktrees and staged changes. Local checks run in an
isolated checkout after inspecting changed scripts. Regression evidence names
the assertion and distinguishes source inspection from an executed failing
and passing comparison. Tests that mock away the failing behavior do not prove
the fix. Changes tied to another deployment also check counterpart revisions,
intermediate version compatibility, merge/deploy order, flags and rollback.
These checks share the engine's existing caps and single verdict.

Approval and changes-requested bodies include a `Model` row with the executing
reviewer's runtime model name or id. If unavailable, the value is `unknown`.

Skill: [`../../skills/bulma-reviewer`](../../skills/bulma-reviewer).

## When

- `/reviewer https://github.com/org/repo/pull/99`
- `/reviewer owner/repo#99`
- `/reviewer` on the current branch’s PR
- Envelope: `REVIEW_REQUEST`

`--force` reviews while CI is red. Pending required CI permits pinned code review, then retains analysis and waits
without posting. A CI completion event resumes when supported; otherwise a 5m wake.

## Graph

```
args or REVIEW_REQUEST
  → admit           idle → main; busy or 2+ PRs → worker+worktree
  → resolve
  → code_review     /bulma-code-review (spec-first, bind, high-risk critic)
  → wait_ci?        retain analysis while CI runs, refresh gates before publishing
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
