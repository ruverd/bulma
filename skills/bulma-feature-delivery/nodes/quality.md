# Node: quality

**Verb:** harden the current ticket before independent review.
**Capability:** coder or quality worker may edit; orchestrator never edits product code.

Run after implement and blast when applicable, before review and tester. Scope
is the current ticket's diff from its recorded starting tree plus affected
contracts. Do not rescan unrelated completed tickets. A cross-ticket change
invalidates their affected acceptance and requires final combined review.

## Depth

Run `scripts/plan-shape.py` on current diff facts, not just the original estimate.
`risk=elevated`, changed cross-service/public contracts, structural boundary
changes, or more than six touched behavioral files require `quality_mode=deep`.
Missing classification evidence defaults to deep. Never downgrade risk from
file count. Record mode and reason in STATE.

- `focused`: reuse the coder to check changed code against repository conventions,
  remove duplication introduced by this ticket, and fix concrete defects. No
  separate thermo worker or full-file structural audit. Independent review still
  checks correctness, requirements, tests and applicable security/contracts.
- `deep`: load bundled `thermo-nuclear-code-quality-review`, apply `fix all` to
  actionable findings introduced or worsened by this change. One quality worker.
  Keep unrelated refactors out of the task. Preserve behavior and TDD.

Do not rerun the full tester here. Use targeted feedback while editing, then let
review and tester validate the final result once. If a structural fix changes the
implementation design, return NEEDS_CONTEXT to the orchestrator. A structural
blocker with no safe correction returns blocked; never silently waive it.

Record each fixed finding with
`../bulma-bus/scripts/observe.py --source fd --reviewer bulma-fd-quality`
(path from this skill's directory; fields in
[INSIGHTS.md](../../bulma-bus/INSIGHTS.md)). Observation failure never changes gates.

## Output

`result: ok | blocked`, `quality_mode: focused | deep`, reason,
`findings_fixed`, remaining findings, and resulting tree identity.
No commit, push, PR or merge here. Next node is independent **review**, then
**tester**, then final **evidence**. Any subsequent product edit invalidates
review, affected tests and visual evidence before shipping.
