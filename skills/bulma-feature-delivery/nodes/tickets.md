# Node: tickets

**Verb:** split. `to-issues` process, local file only.

Write `$BULMA_ROOT/.bulma-feature-delivery/TICKETS.md` from [../templates/TICKETS.md](../templates/TICKETS.md). Tracer-bullet **vertical** slices. Each ticket names its blockers.

One ticket = one implement window. Load bundled
`principle-sequence-verifiable-units`.

Seams: apply [../TDD.md](../TDD.md). Default table, DECIDE. Record `seams` in STATE.

For each behavior change, use the ticket's existing RED step to name the
consequential scenario, its observable result and the test seam. Consider
where the happy path could pass while a changed or preserved contract breaks.
Choose cases from the affected callers, states and dependency outcomes. Cite
existing tests that already prove preserved behavior.

For a full feature without tracker children, choose `delivery_mode` from
the plan. Default to `delivery`: implement each slice in its own coder
session and ship the validated combined tree as one PR. Choose `stack`
when each proposed PR has a distinct, testable review, rollout, or delivery
purpose. Record the decision with the acceptance boundaries and dependencies.
Example: a disabled path can be reviewed before a separate activation
change. Only ask for a product or rollout decision if it blocks either
shape. Use [the stack planner](../../bulma-developer/STACKED.md#plan-and-state)
with the existing local slices, using `source: planned` or
`source: integrated`. Finish the applicable plan critic first. A stack
member, a no-PR run, and a cross-repo fullstack run retain their own path.

Do **not** create tracker issues from this node. [BLOCKERS.md](../BLOCKERS.md) is the only create path (missing contract).

Main thread.

Carry the selected playbook's obligations into each applicable ticket. Complete
baseline capture before implementation. Refactoring records its fixed probe,
fixtures and original receipt; performance records its frozen method. Do not
create another checklist: update the owning rows in STATE.

Compact mode: validate the existing single ticket and seams, then continue.
Do not load to-issues, duplicate SPEC.md or synthesize another plan. All consumers
read STATE `spec_path` and `tickets_path`; separate files remain for detailed mode.
