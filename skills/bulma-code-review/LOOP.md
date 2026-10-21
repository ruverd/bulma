# wait_ci — pending CI loop

Pending required checks never produce a GitHub artifact. Review code first, then wait.
`schedule_wake` ([bulma-host](../bulma-host/SKILL.md)). Do not block the turn on
`gh pr checks --watch`.

## Required checks

`ci_overall` uses **required** checks only:

- Build, test, lint and typecheck jobs from the repo's CI workflows, including
  workflows named `Build`, `Playwright` or similar, not just a literal `CI`
- Plus any check GitHub marks required on the branch

An empty branch-protection required-check list does not waive build/tests.
Inspect workflow branch/path filters and skipped job/step conditions; only
executed checks supply evidence. Optional unrelated jobs do not gate approval.

Ignore review-bot check statuses for this CI loop. Their review comments and
AI QA `FAIL` findings still gate approval through [PREFLIGHT.md](references/PREFLIGHT.md);
QA `BLOCKED` does not.
Required-check success must include actual build/test execution on the reviewed
head. Empty, skipped, neutral, stale or unverifiable jobs are `unknown`, never
green. Check workflow filters against `baseRefName`, especially `feature/*`:
when no build/test workflow runs on PRs into the base at all, `ci-scope.py`
returns `out_of_scope` and there is nothing to wait for
([PREFLIGHT.md](references/PREFLIGHT.md) §CI out of scope).

## State

Path: `$BULMA_ROOT/.bulma-code-review/STATE.md`
(see [DISK.md](../bulma-bus/DISK.md)). One file per git toplevel.

Copy [templates/STATE.md](templates/STATE.md). Fields that matter here:
`pr_url`, `repo`, `pr`, `sha`, `loop_id`, `ci`, `caller`.

## Retain analysis before waiting

In `review_dir`, keep `AC.md`, `bound.json`, `coverage.json` (per-file checks,
caller/contract paths and uncovered areas), and `analysis.json` (`pass`, `risk`,
`critic`, findings and remaining uncertainties). Keep full findings; do not store
only a clean/dirty boolean. Generate current `CONTEXT.json` as described in
[nodes/pass_decision.md](nodes/pass_decision.md).

```bash
python3 scripts/snapshot.py seal --dir "$REVIEW_DIR" --context "$REVIEW_DIR/CONTEXT.json"
```

Cache failure never authorizes publication. Record failure and resume with normal
review rules. `--dry-run` may retain local analysis, but creates no wake or POST.
Prefer host completion events with one wake per PR; otherwise use the 5m timer.
The wake must still verify current HEAD and all gates. No in-session polling.

## Create (once per PR)

If STATE already has a `loop_id` for this `repo#pr`, do not create a second loop.

`--dry-run`: print WAITING, create nothing.
`--force` permits inspection with red/unknown CI, but does not bypass pending wait.

```
schedule_wake
  interval: "5m"
  fire_immediately: false
  prompt: <exact text below>
```

Store the host's wake id in STATE as `loop_id`. Set `status: waiting_ci`.
If a prior issue comment on this SHA has `reason=ci_pending`, delete it.
That comment is the old gate.

## Prompt (paste verbatim, fill PR/repo/caller)

```text
Continue bulma-code-review wait_ci. load_skill bulma-code-review
(SKILL.md + LOOP.md).

PR: <url>
Repo: <owner/repo>
State: $BULMA_ROOT/.bulma-code-review/STATE.md
Caller: <bulma-code-review | bulma-reviewer>

Refresh the snapshot, context and gates on the live head SHA. If retained
analysis matches, do not reread code. If it does not, run the normal deep/light
pass and critic, then retain the replacement analysis even if CI is pending.
If CI is still pending, keep the wake and end the turn without posting.
If green, cancel_wake, then resume verdict and publication with fresh preflight
and gate.py. If Caller is bulma-reviewer, continue at diagnose → report.
If required CI failed or is unknown, cancel_wake and DEFER
(reason=ci_red or ci_unknown) with the issue comment in SKILL §9.
If the PR is CLOSED or MERGED, cancel_wake and stop.
Do not post while pending. Do not merge. Chat: `bulma-memory`. Unslop always.
```

Interval **5m**. Min 60s.

## Each fire

Recompute `ci_overall` on the **current** head SHA (a push while waiting
is a new SHA; wait or review that SHA, never the stale one).

| World | Next |
|---|---|
| pending, analysis valid | stop (keep the loop) |
| pending, analysis invalid | review current inputs, retain analysis, keep loop |
| success | delete loop, reuse valid analysis or **review**, then publish gates |
| failure / unknown | delete loop, **defer** |
| CLOSED / MERGED | delete loop, stop |

## Delete

`cancel_wake` with `loop_id` when:

- review or DEFER is posted, or
- PR is closed/merged, or
- user cancels the wait

If delete fails, report the id; do not leave a silent loop.

## Chat (no GitHub body)

```
# Review: <repo>#<pr>, wait_ci

| | |
|---|---|
| Head | <sha7> |
| Prior | none \| ... |
| CI | pending |
| Axes | skipped — wait_ci |
| Read | 0 files |
| Posted | WAITING — loop <id> every 5m |
```
