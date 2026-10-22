# Node: patch

**Verb:** TDD via coder
**Capability:** spawn `bulma-fd-coder` (or run that contract inline if
this job is already a depth-1 worker)

Orchestrator **does not** write product code. Same PR. Same branch.
No new PR. Draft stays draft. No merge.

## Before the coder

[DECISION_POLICY.md](../../bulma-feature-delivery/DECISION_POLICY.md).
DECIDE by default. Do not ping the user.

**Complicated** (run [grill.md](grill.md) first) if any:

- auth / tenant / PII / money / public API / permission
- new module, type, or endpoint
- more than two behavioral files, or the root cause is still fuzzy
- TDD would need a redesign
- two designs still look equally right after lookup

**Simple** (skip grill): one localized change, the review already names
the trigger and the fix, a neighbor pattern exists.

Grill ASK → `waiting_user`, stop. Resume continues here.

## Coder

Follow [implement.md](../../bulma-feature-delivery/nodes/implement.md) +
[TDD.md](../../bulma-feature-delivery/TDD.md). One verified cause group at a time from `groups.json`. Fresh `bulma-fd-coder`
per group; related comments share discovery and one coherent implementation.
Groups execute sequentially on the same branch. Never parallelize overlapping
writes. Reuse that coder for corrections, except the final retry uses a fresh one.

Inject: all group comments + dispositions + per-comment acceptance, cause evidence,
grill decisions if any, file whitelist,
TDD RED/GREEN, same branch. Spawn payload:
[bulma-host](../../bulma-host/SKILL.md) `spawn_worker`. Forbidden:
GRAPH.md, parent tool catalog, production code before RED,
other tickets, merge, new PR.

Worker lane (cannot spawn): run [coder.md](../../bulma-feature-delivery/nodes/coder.md)
inline. TDD still required. Do not skip because the slice is small.

`NEEDS_CONTEXT` → parent DECIDE from the review + repo. ASK only last
resort.

If the SHA changed, recapture After and `gh pr edit --body` so the
Before → After section matches HEAD.
[evidence.md](../../bulma-feature-delivery/nodes/evidence.md).

Then **prove**. Do not **reply** from this node.

Record the group's resulting tree, commands and evidence paths. A later group
that changes an earlier group's code invalidates its affected proof. Complete
all groups before final prove; proof checks every fix comment on the final tree.
Use [runtime evidence](../../bulma-bus/PERFORMANCE.md) to reuse only identical
local test executions. Grouping never marks a comment processed or replied.
