# `/ruver-code-review`

Review **engine**. One GitHub artifact per PR: `APPROVE`,
`REQUEST_CHANGES`, or `DEFER`. Called by [`/ruver-reviewer`](ruver-reviewer.md)
or run alone.

Skill: [`../../skills/ruver-code-review`](../../skills/ruver-code-review).

## When

- `/ruver-code-review https://github.com/org/repo/pull/99`
- `/ruver-code-review 99 100` (two PRs → one worker each)
- `/ruver-code-review` on the current branch
- Flags: `--deep` `--light` `--dry-run` `--force`

## Invariants

1. One PR on the main thread (plus at most one high-risk critic spawn,
   which does not post). Two or more PRs → one fresh worker per PR.
   Orchestrator does **not** read diffs itself.
2. Exactly one artifact per PR. Never a review **and** an issue comment.
3. Never APPROVE while required CI is failed, pending, or unknown.
4. No finding without a concrete trigger. Drop in silence.
5. Spec checklist (`AC.md`) is written before product-file Reads.
   Tests are read before correctness. Findings are bound to the patch
   and carry an `axis`. High-risk PRs get one critic spawn (three
   lenses, no vote) before the verdict; that spawn does not post.
   The GitHub body includes Acceptance coverage.
6. Nits never block. Max 5, collapsed. Most stay silent.
7. Other reviewers’ `CHANGES_REQUESTED` is ignored. Re-find from the
   head SHA.

Pending required CI: `wait_ci` (5m `schedule_wake`, **no** PR comment).
Draft / conflict / CI-red: DEFER with `pass=none` (no code was read).

## Pass

| Last artifact on this SHA | Pass |
|---|---|
| none | deep |
| already reviewed this SHA | skip |
| new commits after a deep/light | light (incremental + carry-forward) |
| prior DEFER `pass=none`, gate gone | deep |

## Verdicts

| Findings | Verdict |
|---|---|
| ≥1 blocker or major | `REQUEST_CHANGES` |
| clean, full coverage, CI green | `APPROVE` |
| gate / incomplete coverage / blocker-level uncertainty | `DEFER` |

## Never

- Merge.
- Invent a finding.
- APPROVE a draft, a conflict, or red CI.
- Two artifacts on the same PR in one run.

## Related

[`/ruver-reviewer`](ruver-reviewer.md) · [`/ruver-lstm`](ruver-lstm.md)
