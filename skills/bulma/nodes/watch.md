# Node: watch

**Verb:** observe every workspace
**Capability:** read `$RUVER_HOME/*/.ruver-*/STATE.md`, `gh` read-only, write
`$RUVER_HOME/bulma-watch.json`

The watchdog. Runs finish outside the graph all the time: the PR merges while
the job sits in `ci_watching`, or the worktree is deleted. This node finds what
is actually stalled across every repo and worktree, not only this one.

| Args | Command |
|---|---|
| `watch` | `python3 scripts/watch.py` |
| `watch --stale-hours N` | same, a workspace counts as stalled after N hours without a write (default 24) |
| `watch --no-gh` | skip the GitHub reconcile (offline) |

The script:

1. Drops terminal STATEs (`done`, `done_notes`, `published`, `deferred`, …)
   and an fd status left behind after its developer run closed.
2. Keeps a workspace when something in it needs the user (`waiting_user`,
   `escalated`, `blocked`, `waiting_blocker`), or when nothing in it moved
   for `--stale-hours`.
3. Reconciles each PR with `gh pr view`. A merged or closed PR means the
   work finished upstream. It is counted as `closed` and cached in
   `bulma-watch.json`, so later runs skip the call.
4. Resolves the workspace directory from the STATE `worktree` field, else
   from the slug. A missing directory is `orphaned`: it cannot be resumed.

## Output

Print the script output as-is, then at most three sentences in the chat
language: what needs the user first, which stalled item you would resume,
and whether the orphaned ones are worth restarting.

Report only. Do not resume, `cd`, or load a graph from this node. The user
picks a line and runs its `next` command; that `/bulma` run routes normally.
Never edit another graph's STATE to mark it closed: the cache is the
reconcile.

Scheduled runs use the host scheduler (for example `/loop 6h /bulma watch`
in Claude Code). The node behaves the same way when scheduled. Stop.
