# Reviewer graph

```
start (args or REVIEW_REQUEST)
  → admit           # idle → main; busy or 2+ PRs → worker+worktree
  → resolve
  → wait_ci         # required CI pending — 5m loop, no PR comment
  → code_review     # /ruver-code-review (spec-first, bind, high-risk critic)
  → diagnose        # classify failures + mergeable
  → report          # REVIEW_RESULT + pop if stacked
```

## Edges

| From | Condition | To |
|---|---|---|
| start | always | **admit** |
| admit | idle + one PR | **resolve** |
| admit | busy or 2+ PRs | one worker+worktree per PR; **stop** on main |
| start | unresolvable | **stop** |
| resolve | required CI pending | **wait_ci** |
| resolve | otherwise | **code_review** |
| wait_ci | still pending | **stop** (loop wakes in 5m) |
| wait_ci | green | **code_review** |
| wait_ci | red / unknown | **code_review** (skill DEFERS) |
| code_review | always | **diagnose** |
| diagnose | always | **report** |
| report | stacked | `REVIEW_RESULT` + pop |
| report | invoked alone | chat report only |

Pending wait lives in `ruver-code-review` [LOOP.md](../ruver-code-review/LOOP.md).
Do not post a `ci_pending` comment.

## Nodes

`nodes/admit.md` · `nodes/resolve.md` · `nodes/wait_ci.md` ·
`nodes/code_review.md` · `nodes/diagnose.md` · `nodes/report.md`

Concurrency: `../ruver-bus/JOBS.md`.

Failures: [references/FAILURES.md](references/FAILURES.md)  
Report: [references/REPORT.md](references/REPORT.md)
