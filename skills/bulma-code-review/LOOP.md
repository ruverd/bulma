# wait_ci — pending CI loop

Pending required checks never produce a GitHub artifact. Chat only.
`schedule_wake` ([bulma-host](../bulma-host/SKILL.md)). Do not block the turn on
`gh pr checks --watch`.

## Required checks

`ci_overall` uses **required** checks only:

- Jobs from the workflow named `CI`
- Plus any check GitHub marks required on the branch

Ignore review bots. A pending bot check does not start this loop and does not
block APPROVE. Bot reviews wait in developer `bot_review`, not here.

## State

Path: `$BULMA_ROOT/.bulma-code-review/STATE.md`
(see [DISK.md](../bulma-bus/DISK.md)). One file per git toplevel.

Copy [templates/STATE.md](templates/STATE.md). Fields that matter here:
`pr_url`, `repo`, `pr`, `sha`, `loop_id`, `ci`, `caller`.

## Create (once per PR)

If STATE already has a `loop_id` for this `repo#pr`, do not create a second loop.

`--dry-run`: print WAITING, create nothing.
`--force`: skip this file, continue the skill at §4.

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

Re-run §1–§3 on the live head SHA. Do not read the diff until CI is green.
If required CI is still pending, do nothing else and end the turn.
If green, cancel_wake, then run §4–§9 including critic then publish
(deep if nothing was reviewed yet). If Caller is bulma-reviewer, after the review
load_skill bulma-reviewer and continue at diagnose → report.
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
| still pending | stop (keep the loop) |
| success | delete loop, **review** |
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
