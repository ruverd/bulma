# Goal graph

The loop exists because CI outlives a tool timeout. Each wake takes exactly one
step and ends the turn.

```
/goal <ticket | PR url | status | cancel>
  │
  ├ cancel ──► cancel_wake, leave graphs as-is ──► stop
  ├ status ──► read STATE + gh, report ──► stop
  │
  ▼
admit  (STATE, completion bar, host goal if the host has one)
  │
  ▼
inspect  (gh pr view · gh pr checks · issue comments)
  │
  ▼
step  (exactly one, from the table below)
  │
  ├ nothing to do yet ──► schedule_wake ──► stop until the next fire
  └ bar satisfied ──────► complete ──► cancel_wake ──► done
```

## Edges

| From | Condition | To |
|---|---|---|
| start | `cancel` | **cancel_wake**, stop |
| start | `status` | report from STATE + `gh`, stop |
| start | ticket id or feature text, no STATE | **admit** |
| start | PR url and a live PR | **admit** (skip implement) |
| start | empty args with live STATE | **inspect** |
| admit | no PR yet | **step** → developer `deliver` |
| admit | draft PR exists, CI not green | **schedule_wake**, stop |
| inspect | no PR | **step** → developer `deliver` |
| inspect | CI pending or in progress | **stop** (wait for the next fire) |
| inspect | CI red | **step** → developer `fix` / fd ci loop |
| inspect | green, not MERGEABLE | **step** → developer `mergeable` |
| inspect | green + MERGEABLE, no QA comment on **this** SHA | **step** → enqueue-or-start QA ([JOBS.md](../bulma-bus/JOBS.md)) |
| inspect | QA comment on this SHA, `FAIL` + `PR_BUG` | **step** → developer `fix` |
| inspect | QA comment on this SHA, `PASS` / `FAIL`-unrelated / `BLOCKED` documented | **complete** |
| step | action dispatched, work still open | **schedule_wake**, stop |
| complete | [COMPLETE.md](references/COMPLETE.md) all true | `cancel_wake`, **done** |
| any | `cancel_wake` fails | report the `loop_id`, never leave a silent loop |

One wake per PR. `loop_id` in STATE is the guard against a second loop.

Nodes: `nodes/admit.md` · `nodes/inspect.md` · `nodes/step.md` ·
`nodes/complete.md`.

Loop mechanics: [references/LOOP.md](references/LOOP.md). Completion bar:
[references/COMPLETE.md](references/COMPLETE.md).
