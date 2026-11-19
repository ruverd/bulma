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
   PASS → done
   FAIL+PR_BUG → fix
```

## What the main thread does

1. Parse args ([ARGS.md](../../skills/bulma-developer/ARGS.md)).
2. Claim the lane ([bulma-bus](bulma-bus.md) JOBS). Busy main → worker + worktree.
3. **deliver** runs [feature-delivery](bulma-feature-delivery.md) until CI green.
4. **fix** stays on the existing PR branch.
5. For one PR, MERGEABLE + CI green → **bot_review** → envelope `QA_REQUEST`.
6. On `QA_RESULT` PASS, record completion on the tested head. Review status stays as set on the PR.

## Stacked tasks

A Linear parent with open subtasks automatically uses
[stacked delivery](../../skills/bulma-developer/STACKED.md). Several task
IDs or an explicit stack also use it. For local feature plans, one PR with
a coder per slice is the default. Distinct review or rollout boundaries
can warrant a stack without creating tracker subtasks.

Each child targets the next branch. After a human merges a child, the next
worker starts with the changes received on its branch. The final umbrella
targets the default branch. Each PR opens ready for review and keeps its
CI, mergeability and applicable review gates. Integrated QA runs on the
umbrella's current combined head with the usual provider and evidence rules.

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
