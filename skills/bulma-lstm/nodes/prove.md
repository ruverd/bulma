# Node: prove

**Verb:** prove the patch. Read-only on product code except through
the fd reviewer/tester contracts.
**When:** after **patch** pushed, before **reply**. GRAPH owns the edge.

Skip-only runs never enter this node.

## Mission

The comment we marked **fix** is gone at HEAD, and the patch is good.
Same two questions as fd [reviewer.md](../../bulma-feature-delivery/nodes/reviewer.md),
scoped to the should-fix slices, not a new design.

1. Did we address **this comment**? (`spec_verdict`)
2. Is the patch good? (`quality_verdict`)

Then the fd [tester.md](../../bulma-feature-delivery/nodes/tester.md)
hard gate on the touched area.

Do not implement in this node. Fail → **patch**.

## Spec axis

The bound comment text + the verify row, not the reviewer's preferred
refactor. A green test does not rescue a comment that still reproduces.

`spec_verdict=fail` if the claim still holds at HEAD, or the change
does something else.

`quality_verdict=fail` if TDD evidence is missing on a behavior
change, tests do not assert behavior, or a UI slice violates
[UI_DESIGN_SYSTEM.md](../../bulma-feature-delivery/UI_DESIGN_SYSTEM.md).

## Loops

`prove_fix_loops: 2`. Either verdict fail, or tester fail → **patch**
the same slice while loops remain. Last remaining slot: **fresh**
`bulma-fd-coder` (the previous one missed it). Exhaust → **escalate**.
Do not **reply**. Do not dismiss `CHANGES_REQUESTED`.

## Evidence

If HEAD ≠ STATE `sha`, recapture After
([evidence.md](../../bulma-feature-delivery/nodes/evidence.md))
before pass. UI + `risk=elevated` on a fix row: After of that route.

## Output

```text
spec_verdict: pending | pass | fail
quality_verdict: pending | pass | fail
tester: pending | pass | fail
sha: <head>
```

Pass only when every fix slice has both verdicts pass and tester pass.
Then **request_qa** when `signoff_required=yes`; otherwise **reply**.

## Final group proof

Run one independent fd reviewer over the final combined patch with all fix
comments and their acceptance criteria. Produce a spec result per comment and a
quality result for the patch. Execute tester on the union of affected areas;
reuse only evidence accepted by `runtime.py check` with a complete environment
fingerprint. Every comment must pass at the final tree, including comments whose
group ran earlier. Failed comments return their group to patch. A new final tree
invalidates affected proof and evidence before reply. Keep existing retry limits.
