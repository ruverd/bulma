# CI / QA wake loop

`schedule_wake` ([bulma-host](../../bulma-host/SKILL.md)). Do not block the turn
on `gh pr checks --watch`.

## Create (once per PR)

If STATE already has `loop_id`, do not create a second loop.

```
schedule_wake
  interval: "5m"
  fire_immediately: false
  prompt: <exact text below>
```

Store the host's wake id in `.bulma-goal/STATE.md` as `loop_id`.

## Prompt (paste verbatim, fill PR/repo)

```text
Continue bulma-goal. load_skill bulma-goal.

PR: <url>
Repo: <owner/repo>
Goal state: .bulma-goal/STATE.md

Inspect gh (pr view, pr checks, issue comments) for this PR.
Take exactly one next step from the bulma-goal table (wait / fix /
mergeable / enqueue-or-start QA via bulma-bus/JOBS.md / complete).
Never start a second QA while qa_active holds another live PR. A claim past
qa_lease_minutes is dead, and taking it over is correct (bulma-bus/JOBS.md).
If CI is still pending, do nothing else and end the turn.
If a bulma-qa marker comment exists for the current head SHA and
includes a video URL, cancel_wake and stop.
Do not merge. Chat: `bulma-memory`. Unslop always, one short S/D/P block.
```

Interval **5m**. Min 60s. CI that takes longer than a tool timeout
is why this loop exists.

## Delete

`cancel_wake` with `loop_id` when:

- COMPLETE.md is satisfied, or
- user runs `/bulma-goal cancel`, or
- PR is closed/merged (still never merge ourselves).

If delete fails, report the id; do not leave a silent loop.
