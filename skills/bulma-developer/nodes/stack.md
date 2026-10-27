# Node: stack

**Verb:** orchestrate children  
**Capability:** `spawn_worker` per child, `gh pr checks`, write `STACK.md` and JOBS. No product code.

Follow [../STACKED.md](../STACKED.md).

1. Resolve children (tracker sub-issues, several ids, or the listed tasks).
   Record `depends_on` from tracker blocks/blockedBy or the user's order.
2. Write `.bulma-developer/STACK.md`. One JOBS row per child (`lane=worker`).
3. Spawn every child whose start ref exists. Each runs `bulma-feature-delivery`
   inline in its own worktree and writes `RESULT.md`.
4. On each RESULT or wake: `gh pr checks` per child PR. Green → that child
   walks mergeable → bot_review → request_qa. Red → fresh fix worker resuming
   that child's fd at `ci_watch`. Pending → `schedule_wake`.
5. Spawn dependents as their start ref appears. Re-check dependents when a
   dependency's head moves.
6. Stop when every child is terminal. Report one row per child.

## Output

`STACK.md` rows, parent `status`, and the per-child summary.
