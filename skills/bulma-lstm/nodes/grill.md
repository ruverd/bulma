# Node: grill (complicated fixes only)

**Verb:** lock the design of the fix. Main thread (or worker inline).

Only when [patch.md](patch.md) marked the slice **complicated**.
Simple fixes never enter this node.

Follow [GRILL.md](../../bulma-feature-delivery/GRILL.md) +
[DECISION_POLICY.md](../../bulma-feature-delivery/DECISION_POLICY.md).

Resolve only gaps that change the fix. **DECIDE** from requirements and existing
patterns. Log consequential rationale in STATE `## Decisions`. ASK under the
shared decision policy for missing intent, even with a confident recommendation.
Batch independent questions, sequence dependent ones; `waiting_user` blocks
dependent work. Chat follows `bulma-memory`. Do not interview through the tree.

This is not a feature delivery. Implementation decisions resolved → **patch**, never spec,
never tickets, never a new PR.

Load `how` only for a named subsystem gap, not the monorepo.
