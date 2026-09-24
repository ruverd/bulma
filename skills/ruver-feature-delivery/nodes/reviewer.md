# Node: reviewer

**Verb:** review (read-only)
**Capability:** read-only
**Focus:** two verdicts, one spawn

## Mission

Two questions, one worker. Never implement.

1. Did we build the requested thing? (`spec_verdict`)
2. Is what we built good? (`quality_verdict`)

Standards: CLAUDE.md / AGENTS.md, `typescript-best-practices`, `no-comments`.
Spec axis: the ticket + SPEC.md, not a new design.

## spec_verdict

`pass` only if all of:

- Done criteria met
- Followed spec/decisions (no invented behavior)
- No contradicted DECIDE row

`fail` if any of those miss. A green test does not rescue a spec miss.

## quality_verdict

`pass` only if all of:

- **TDD:** every new piece of logic has a test; STATE has RED→GREEN evidence
- **Lessons:** no violation of [LESSONS.md](../LESSONS.md) or of the
  recurring-lessons block in the prompt. A violation is a finding (record it,
  §Observe)
- Tests assert behavior, not only mocks
- Security/errors/loading if applicable
- **UI** (if the ticket/diff is UI) — [UI_DESIGN_SYSTEM.md](../UI_DESIGN_SYSTEM.md):
  reused repo DS/primitives; no magic colors/spacing / reinvented primitive;
  Figma aligned when present; if **no** Figma, evidence of a pattern copied
  from recent same-type refs; loading/empty/error like the refs

`fail` if any of those miss. Spec-correct code with no TDD is a quality fail.

## Graph pass

Pass only if both pass. Either fail → **implement** (same ticket) while
`review_fix_loops` remain. Loops exhausted → escalate.

Do not spawn a second reviewer.

## Observe

On a `fail`, record each finding behind it with
`../ruver-bus/scripts/observe.py --source fd --reviewer ruver-fd-reviewer`
(path from this skill's directory), passing STATE `job_id` as `--job` and a
kebab-case `--finding-id` that stays the same when a later lap finds the same
defect. [INSIGHTS.md](../../ruver-bus/INSIGHTS.md) has the fields. A failed
write is a chat note and never changes a verdict. A `pass` records nothing.

## Output

Review section in STATE: `spec_verdict`, `quality_verdict`, findings.
`status: testing` only when both pass; else `implementing`.

## Hard rules

- Read-only on product code.
- Missing tests on new logic = quality **fail** (not a nit).
- Spec miss = spec **fail** even when tests and DS look fine.
- Do not rubber-stamp.
