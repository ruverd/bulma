# Node: grill (complicated fixes only)

**Verb:** lock the design of the fix. Main thread (or worker inline).

Only when [patch.md](patch.md) marked the slice **complicated**.
Simple fixes never enter this node.

Follow [GRILL.md](../../bulma-feature-delivery/GRILL.md) +
[DECISION_POLICY.md](../../bulma-feature-delivery/DECISION_POLICY.md).

Walk the tree internally. Look it up. **DECIDE**. Log in STATE
`## Decisions`. ASK only if very important **and** high uncertainty
after lookup. One question, English, `waiting_user`. Do not interview
through the tree.

This is not a feature delivery. Frontier empty → **patch**, never spec,
never tickets, never a new PR.

Load `how` for the subsystem you will touch, not the monorepo. `why`
only per [PSTACK.md](../../bulma-feature-delivery/PSTACK.md).
