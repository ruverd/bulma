# 3. Gates — before reading any diff

Nothing below this line reads a diff or a product file. Workflow configuration
is read only to establish CI execution evidence. Draft, conflict, and CI-red
gates still post one issue comment. Pending required CI does **not** post.
Review the pinned diff while CI runs; retain analysis before waiting ([LOOP.md](../LOOP.md)).

Compute `ci_overall` from the head-bound execution evidence in
[PREFLIGHT.md](../references/PREFLIGHT.md), not rollup conclusions alone:
`failure` if any required check failed, else `pending` if any required check is
pending/queued/in_progress. `success` requires actual build/test execution on
the reviewed SHA and all required checks passing. Empty, skipped, neutral,
stale or unverified build/test evidence → `unknown`; say "CI did not run"
when execution is absent.
What counts as required is in [LOOP.md](../LOOP.md) (CI workflow + GitHub-required;
ignore review bots).

| Condition | Action |
|---|---|
| `state` is CLOSED or MERGED | print state, post nothing, stop |
| `isDraft` | DEFER, `reason=draft` |
| `mergeStateStatus` in `DIRTY`, `CONFLICTING` | DEFER, `reason=conflict` |
| `review_context` = blocked or unknown | DEFER, `reason=review_context` or `review_context_unknown`, link concerns |
| `ci_overall` = failure | DEFER, `reason=ci_red`, list ≤8 failing checks with log links |
| `ci_overall` = pending | **review** pinned head now; after critic retain analysis and **wait_ci**. No PR artifact while pending. |
| `ci_overall` = unknown | DEFER, `reason=ci_unknown` |

Every gate DEFER carries `pass=none` in its marker — **no code was reviewed**. That
value is what stops §8.1 from later promoting unreviewed code to APPROVE.
`wait_ci` posts nothing, so there is no marker until a later review or DEFER.

`--force` skips the three CI rows only (state, draft and conflict gates never
yield). Pending CI already permits inspection by default. `--force` does not bypass the pending publication wait.
