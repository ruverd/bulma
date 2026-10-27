# Stacked task

A stacked task is one parent with several children. Each child is its own
branch, its own worktree, and its own draft PR. The main thread is the
**orchestrator** only. It never implements a child and never runs a child's
fd nodes itself. Every child runs Bulma end-to-end inside its own worker.

## Detect

Admit sets `mode: stack` when any of these hold:

| Signal | Children |
|---|---|
| Tracker issue has child / sub-issues | one child per open sub-issue |
| Several tracker ids in the args (`ABC-1 ABC-2`) | one child per id |
| The user says "stacked", "stack of PRs", "one PR per task", or lists 2+ separately shippable tasks | one child per listed task |

Not stacked: fd `tickets` splitting one goal into slices. Slices still ship
as one PR. A single child is not a stack; run plain **deliver**.

## Registry

`$BULMA_ROOT/.bulma-developer/STACK.md`, written by the orchestrator only:

```markdown
| child | job_id | depends_on | branch | worktree | worker | pr | sha | ci | ci_fix_loops_used | status |
|---|---|---|---|---|---|---|---|---|---|---|
```

- `job_id`: `dev-<child-id>` (tracker) or `dev-<parent-slug>-<n>` (free text).
- `branch`: [JOBS.md](../bulma-bus/JOBS.md#worktree) rules per child.
  Tracker child `ABC-2` → `feature/abc-2`. Free text → `feature/<parent-slug>-<n>`.
- `ci`: `pending | green | red | fixing | escalated`.
- `status`: `queued | running | ci | fixing | mergeable | qa | done | done_notes | waiting_user | escalated`.

## Base branch

Every child PR uses `--base main` (the repo default). **Never** base a child
PR on the parent's or another child's branch. A PR based on a feature branch
merges into that branch, not into main.

`depends_on` only changes where the child **starts**:

- No dependency, or the dependency is merged → worktree from `origin/main`.
- Dependency not merged yet → worktree from the dependency's pushed branch
  head. The PR still targets main. The body says `Depends on #N. Merge #N first.`
- When the dependency merges or its head moves, a fix worker rebases the child
  onto `origin/main` (or the new head) and the orchestrator re-checks CI.

## Spawn

Spawn children whose dependencies have a pushed branch. Independent children
start together, one host `spawn_worker` each
([bulma-host](../bulma-host/SKILL.md#spawn_worker)), each with worktree
isolation. Dependent children start when their dependency's branch exists.

Child worker prompt, in this order:

1. "Run `bulma-feature-delivery` end-to-end yourself, in this worktree:
   mcp_context → triage → … → shipper → ci_watch. Load its SKILL.md and
   GRAPH.md. Execute the nodes inline. Do not spawn `bulma_*` or
   `bulma-fd-*` children. Never merge. Draft PR with --base main."
2. job id, worktree path, branch, start ref.
3. the child task: tracker id or full task text, plus the parent goal in one line.
4. `depends_on` PRs and the base rule above.
5. "Write `<abs parent $BULMA_ROOT>/.bulma-bus/jobs/<job_id>/RESULT.md` with
   `status`, `pr_url`, `sha`, `ci`, and the path to your fd STATE.md."

The child keeps its own fd STATE under its worktree's `$BULMA_ROOT`
([DISK.md](../bulma-bus/DISK.md)). The orchestrator reads it; it does not edit it.

## Watch and fix CI

The orchestrator owns CI for **every** child, including children whose worker
reported green. A worker's green is a claim. `gh pr checks` is the fact.

For each child with a PR, on every wake:

1. `gh pr checks <pr> --json name,bucket,state,link`.
2. All required green → `ci: green`, then this child walks
   **mergeable → bot_review → request_qa → apply_qa** as its own job
   (`job_id`, JOBS.md). The single QA lease still queues children.
   Under `/bulma-fd` alone there is no QA: green on head is that child's done.
3. Pending → leave it. One `schedule_wake` covers all children; never `--watch`.
4. Red → spawn a **fresh** fix worker in that child's worktree. Prompt: the
   child's fd STATE path, "resume `bulma-feature-delivery` at **ci_watch**",
   the first failing check, and `gh run view <id> --log-failed` excerpt
   (20–40 lines). Root cause first, TDD on behavior, push the same branch,
   never `--force`. Then re-check from step 1.
5. Cap: fd `ci_fix_loops` (default 5) per child. Exhausted → that child
   `escalated`. The other children keep going.

A fix that changes a child's head re-checks every child that `depends_on` it.

## Terminal

- Child `waiting_user` → collect its question. Ask the user once for all open
  questions. Parent `waiting_user`. Running children continue.
- Parent `done` only when **every** child is `done` or `done_notes`: PR open,
  CI green on head, QA verdict applied.
- Any child `escalated` with the rest terminal → parent `escalated`, listing
  each red child with PR, failing checks, and loops used.

Summary to the user: one row per child with PR URL, CI, QA, and status.

## Never

- Implement, fix, or rebase product code on the main thread.
- Run a child's fd graph inline on the main thread.
- Base a child PR on anything but main.
- Call the parent done while any child's CI is red or pending.
- Merge, or mark a child ready before its QA PASS.
