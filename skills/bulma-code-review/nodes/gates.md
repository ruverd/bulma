# 3. Gates — before reading any diff

Nothing below this line reads a diff or a file. Draft, conflict, and CI-red
gates still post one issue comment. Pending required CI does **not** post.
It waits ([LOOP.md](../LOOP.md)).

Compute `ci_overall` from the `statusCheckRollup` already fetched in §2:
`failure` if any required check failed, else `pending` if any required check is
pending/queued/in_progress, else `success`. Empty rollup → `unknown`.
What counts as required is in [LOOP.md](../LOOP.md) (CI workflow + GitHub-required;
ignore review bots).

| Condition | Action |
|---|---|
| `state` is CLOSED or MERGED | print state, post nothing, stop |
| `isDraft` | DEFER, `reason=draft` |
| `mergeStateStatus` in `DIRTY`, `CONFLICTING` | DEFER, `reason=conflict` |
| `ci_overall` = failure | DEFER, `reason=ci_red`, list ≤8 failing checks with log links |
| `ci_overall` = pending | **wait_ci** — [LOOP.md](../LOOP.md). No PR comment. Chat only. Stop. |
| `ci_overall` = unknown | DEFER, `reason=ci_unknown` |

Every gate DEFER carries `pass=none` in its marker — **no code was reviewed**. That
value is what stops §8.1 from later promoting unreviewed code to APPROVE.
`wait_ci` posts nothing, so there is no marker until a later review or DEFER.

`--force` skips the three CI rows only (state, draft and conflict gates never
yield). Use it to review while CI is still running. It also skips `wait_ci`.
