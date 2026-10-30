# `/bulma-code-review`

Review **engine**. One GitHub artifact per PR: `APPROVE`,
`REQUEST_CHANGES`, or `DEFER`. Called by [`/bulma-reviewer`](bulma-reviewer.md)
or run alone.

Every verdict body includes `Model` and `Reasoning effort` rows with the
executing reviewer's actual runtime settings. Workers report their own pair,
not the orchestrator's or critic's. Missing fields are `unknown`, never guessed.
PR creation also records code review model and effort separately from
implementation attribution in the description's `Agent run` section.

Skill: [`../../skills/bulma-code-review`](../../skills/bulma-code-review).

## When

- `/bulma-code-review https://github.com/org/repo/pull/99`
- `/bulma-code-review 99 100` (two PRs → one worker each)
- `/bulma-code-review` on the current branch
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
7. Read reviews, unresolved threads and comments, including AI QA, before
   pass selection and publication. Open concerns block approval, except a
   thread whose author approved this head. Never dismiss another review; ask
   its reviewer to re-review.
8. Approve only the exact reviewed head with CI execution proved on that SHA.
   Review new commits before approving. Missing/skipped tests are not green.
9. Inspect callers and neighboring tests one hop outside the diff; compare API
   mocks with provider/client response shapes. Own Critical/High blocks approval.
10. Workflows, Terraform, auth, billing/seats and secrets are listed as
    needing human sign-off. That list does not defer or block approval,
    including on light and promoted passes.

Pending required CI allows code review first, then retains completed analysis
locally during `wait_ci`. No PR artifact is posted while pending. Live gates
run again before publication; changed inputs invalidate the retained analysis.
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

[`/bulma-reviewer`](bulma-reviewer.md) · [`/bulma-lstm`](bulma-lstm.md)
