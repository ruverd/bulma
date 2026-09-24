# Node: step

**Verb:** dispatch **one** action, then end the turn.

## Rules

- Exactly one action per wake. Never chain two.
- Dispatch by loading the graph on this thread or by writing a bus envelope
  ([PROTOCOL.md](../../bulma-bus/PROTOCOL.md)). Never spawn `bulma_developer`,
  `bulma_qa` or any other graph type as a child.
- QA goes through enqueue-or-start ([JOBS.md](../../bulma-bus/JOBS.md)). If
  `qa_active` is another **live** PR, enqueue and say the queue position. An
   expired or abandoned claim is free — `../../bulma-bus/JOBS.md`. Do not start a
  second QA.
- After dispatching, if work is still open, `schedule_wake`
  ([LOOP.md](../references/LOOP.md)) and stop.

## Actions

| Inspect said | Action |
|---|---|
| No PR | developer `deliver` |
| CI pending | none. Stop and wait for the next fire |
| CI red | developer `fix` / fd ci loop |
| Green, not MERGEABLE | developer `mergeable` |
| Green + MERGEABLE, no QA comment on head SHA | enqueue-or-start QA |
| QA `FAIL` + `PR_BUG` | developer `fix` |
| QA `PASS` / `FAIL`-unrelated / `BLOCKED` documented | **complete** |

## Never

- Merge, or mark ready before QA `PASS`.
- Sit in `gh pr checks --watch`.
