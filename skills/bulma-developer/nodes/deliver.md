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

When a draft PR exists and CI is not yet green, start **bulma-goal**
wait loop (`../../bulma-goal/references/LOOP.md`). Do not
block this turn on `--watch`.
