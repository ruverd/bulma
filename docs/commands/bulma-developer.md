# `/bulma-developer`

Alias: **`/developer`**. Graph engineer for **delivery**. Ticket,
free-text goal, or a `QA_RESULT` FAIL + `PR_BUG`. Never implements
product code. Never merges.

Skill: [`../../skills/bulma-developer`](../../skills/bulma-developer).
Engine: [`/bulma-feature-delivery`](bulma-feature-delivery.md).

## When

- `/developer ABC-123`
- `/developer the notification inbox on the dashboard`
- `/developer resume`
- `/developer ABC-10` where ABC-10 has sub-issues, `/developer ABC-11 ABC-12`, or "stacked: …" (stack mode)
- Envelope: `QA_RESULT` FAIL + `PR_BUG` (from [QA](bulma-qa.md))

## Graph

```
goal | ticket | resume | FAIL+PR_BUG
        │
     admit
        │
   ┌────┴─────┐
   ▼          ▼
deliver      fix
 (fd)     (same PR)
   │          │
   └────┬─────┘
        ▼
    mergeable          CI green AND mergeable
        │
    bot_review         skip if no bot; else wait / lstm
        │
   request_qa  ──bus──►  /bulma-qa
        │
   apply_qa
        │
   PASS → ready
   FAIL+PR_BUG → fix
```

## What the main thread does

1. Parse args ([ARGS.md](../../skills/bulma-developer/ARGS.md)).
2. Claim the lane ([bulma-bus](bulma-bus.md) JOBS). Busy main → worker + worktree.
3. **deliver** runs [feature-delivery](bulma-feature-delivery.md) until CI green.
4. **fix** stays on the existing PR branch.
5. MERGEABLE + CI green → **bot_review** → envelope `QA_REQUEST`.
6. On `QA_RESULT` PASS → mark the PR ready. Ready is not merge.

## Stacked tasks

A parent with sub-issues, several ids, or an explicit stacked request runs
**stack** ([STACKED.md](../../skills/bulma-developer/STACKED.md)). The main
thread only orchestrates:

- one worker per child, each in its own worktree, running
  `bulma-feature-delivery` end-to-end itself
- every child PR targets `main`, never another child's branch
- the orchestrator polls `gh pr checks` for every child and sends a fresh fix
  worker for any red CI, up to `ci_fix_loops` per child
- each green child goes through mergeable, bot review, and QA as its own job
- the parent is done only when every child is

Workers (`bulma-fd-coder`, tester, shipper, …) write the code. The
graph engineer only walks edges.

## Never

- Merge.
- Spawn `/bulma-qa` as a child. Bus switch.
- Abort an in-flight QA because a new ticket arrived.
- Re-grill settled decisions on `resume` unless an AC line contradicts them.
- Skip a node on `resume` only because the file still exists. Replay invariants.

## Related

[`/bulma-qa`](bulma-qa.md) · [`/bulma-goal`](bulma-goal.md) ·
[`/bulma-bus`](bulma-bus.md) · [`/bulma-lstm`](bulma-lstm.md)
