# Node: plan

**Verb:** write  
**Capability:** read PR/diff, write `.ruver-qa/PLAN.md` + STATE

Follow [../references/PLAN.md](../references/PLAN.md).

1. Copy [../templates/PLAN.md](../templates/PLAN.md) → `.ruver-qa/PLAN.md`.
2. Fill inventory, blast radius, and happy and user-break steps
   from the diff and ACs.
3. STATE: `status=planning`, `plan_path=.ruver-qa/PLAN.md`, `surface`
   = routes/endpoints/specs listed.
4. Chat the step list (English). Then **execute**.

No e2e, no browser, no HTTP execute, no verdict in this node.
