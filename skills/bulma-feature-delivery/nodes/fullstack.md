# Node: fullstack_setup (+ coordinate)

**Verb:** coordinate
**Capability:** git worktree (Orca optional); host `spawn_worker`; write STATE
**When:** `scope: fullstack` after triage, sibling resolved ([PRODUCT.md](../PRODUCT.md))

## Mission

1. Create/reuse **worktrees** on frontend and backend with the **same branch**.
2. Run a worker in each worktree.
3. Wait; aggregate.

Follow [FULLSTACK.md](../FULLSTACK.md).

## Steps

1. Resolve sibling names ([PRODUCT.md](../PRODUCT.md)). Empty → do not run this node.
2. Resolve `tracker_branch` (STATE) = `feature/<id-lowercase>`
   ([JOBS.md](../../bulma-bus/JOBS.md)).
3. Worktree on **backend** and **frontend** (`git worktree add`, or Orca if it is up).
4. `spawn_worker` on each ([bulma-host](../../bulma-host/SKILL.md)). BE first when the contract is new.
5. Wait until both done/escalation.
6. Update STATE: worktree paths, task/worker ids, status per repo.

## Output

```text
result: ok | blocked | partial
branch: <same on both>
backend_worktree: ...
frontend_worktree: ...
```

## Hard rules

- Same branch on both repos.
- Orca is optional. Host workers on git worktrees always work.
- Tracker MCP for the ticket, never a vendor CLI.
- No automatic merge.
