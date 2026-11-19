# Node: deliver

**Verb:** run fd  
**Capability:** orchestrate only — load `bulma-feature-delivery` GRAPH

## Mission

Run **bulma-feature-delivery** on the goal until `status=done` (CI green)
or a terminal fd state (`waiting_blocker`, `escalated`, `done_local`).

Do not re-implement fd. Do not write product code.
If `lane=worker`, work only in `worktree` (or host isolation).

## Output

`fd_status` + `pr_url` + `sha` into developer STATE.

When fd discovers a tracker stack or chooses a stack from the settled plan,
transfer that plan on the same foreground to [stack](stack.md). Persist
`mode=stack` and resume from that plan. If discovery runs in a busy-lane
worker, return the plan in its RESULT for foreground dispatch.

When an open PR exists and CI is not yet green, start **bulma-goal**
wait loop (`../../bulma-goal/references/LOOP.md`). Do not
block this turn on `--watch`.
