# Node: tickets

**Verb:** split. `to-issues` process, local file only.

Write `$BULMA_ROOT/.bulma-feature-delivery/TICKETS.md` from [../templates/TICKETS.md](../templates/TICKETS.md). Tracer-bullet **vertical** slices. Each ticket names its blockers.

One ticket = one implement window. Load bundled
`principle-sequence-verifiable-units`.

Seams: apply [../TDD.md](../TDD.md). Default table, DECIDE. Record `seams` in STATE.

Do **not** create tracker issues from this node. [BLOCKERS.md](../BLOCKERS.md) is the only create path (missing contract).

Main thread.

Compact mode: validate the existing single ticket and seams, then continue.
Do not load to-issues, duplicate SPEC.md or synthesize another plan. All consumers
read STATE `spec_path` and `tickets_path`; separate files remain for detailed mode.
