# Node: diagnose

**Verb:** root cause. No product fix in this node.

For `playbook: investigation`, follow its cited-answer contract and finish with
the playbook check and `done_report`. Do not produce a fix ticket or dispatch an
implementer. For performance, read the selected measurement contract first.

Bundled `diagnose`: reproduce → minimise → hypothesise → instrument → (stop).

Hard / no playbook: bundled `figure-it-out` Phase A–C, then hand a single fix slice to implement.

`how` on the broken subsystem.
Load bundled `principle-fix-root-causes`.

Output: root cause + one ticket (RED test that fails on the bug + GREEN plan). If it is a feature, re-route to grill.

On a UI route, capture Before here while the bug still shows. Same route and viewport as After. See [evidence.md](evidence.md).

Write the slice that restores stated behavior (DECIDE). Last-resort ASK only if the fix would create a new product rule the ticket does not cover **and** you cannot defend a rec.

Spawn `bulma-fd-debugger` (legacy name; this file is the contract).

For runtime failures, query captured logs before repeating a reproduction.
Use [runtime evidence](../../bulma-bus/PERFORMANCE.md); missing Trail falls back
to file capture. Logs support diagnosis, but do not replace behavioral tests.

After two failed fixes based on the same premise, record that premise and a
discriminating observation before another fix. Keep the existing loop counters;
changing a hypothesis never replenishes them.
