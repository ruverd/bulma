# `/ruver-developer`

Alias: **`/developer`**. Graph engineer for **delivery**. Ticket,
free-text goal, or a `QA_RESULT` FAIL + `PR_BUG`. Never implements
product code. Never merges.

Skill: [`../../skills/ruver-developer`](../../skills/ruver-developer).
Engine: [`/ruver-feature-delivery`](ruver-feature-delivery.md).

## When

- `/developer ABC-123`
- `/developer the notification inbox on the dashboard`
- `/developer resume`
- Envelope: `QA_RESULT` FAIL + `PR_BUG` (from [QA](ruver-qa.md))

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
   request_qa  ──bus──►  /ruver-qa
        │
   apply_qa
        │
   PASS → ready
   FAIL+PR_BUG → fix
```

## What the main thread does

1. Parse args ([ARGS.md](../../skills/ruver-developer/ARGS.md)).
2. Claim the lane ([ruver-bus](ruver-bus.md) JOBS). Busy main → worker + worktree.
3. **deliver** runs [feature-delivery](ruver-feature-delivery.md) until CI green.
4. **fix** stays on the existing PR branch.
5. MERGEABLE + CI green → **bot_review** → envelope `QA_REQUEST`.
6. On `QA_RESULT` PASS → mark the PR ready. Ready is not merge.

Workers (`ruver-fd-coder`, tester, shipper, …) write the code. The
graph engineer only walks edges.

## Never

- Merge.
- Spawn `/ruver-qa` as a child. Bus switch.
- Abort an in-flight QA because a new ticket arrived.
- Re-grill settled decisions on `resume` unless an AC line contradicts them.
- Skip a node on `resume` only because the file still exists. Replay invariants.

## Related

[`/ruver-qa`](ruver-qa.md) · [`/ruver-goal`](ruver-goal.md) ·
[`/ruver-bus`](ruver-bus.md) · [`/ruver-lstm`](ruver-lstm.md)
