# `/bulma-bus`

Shared stack and envelopes. Five graphs, one session. They **do not nest**.

Skill: [`../../skills/bulma-bus`](../../skills/bulma-bus).

## When

- `/bulma-bus resume` — pick up the last STACK line
- `/bulma-bus status` — print stack, envelope, QA slot
- Any graph about to leave for another graph (write envelope, then this protocol)

## Topology

```
developer ⇄ qa ⇄ triage
     ⇄ reviewer
     ⇄ lstm
```

Communication is files under `$BULMA_ROOT/.bulma-bus/` — never the git
root. See [DISK.md](../../skills/bulma-bus/DISK.md).

```
.bulma-bus/
  STACK.md       last line = active graph
  ENVELOPE.md    current message
  log.md         append-only
  JOBS.md        workers + single QA slot
  jobs/<id>/     parked envelopes
```

## Switch (main thread only)

1. Write `ENVELOPE.md`
2. Push `to` onto `STACK.md`
3. Stop acting as `from`
4. `load_graph` `bulma-<to>` on **this** thread

On `*_RESULT`: write envelope, pop, load the new top. Do not re-run
finished nodes.

## Envelope types

| type | from → to |
|---|---|
| `QA_REQUEST` | developer → qa |
| `TRIAGE_REQUEST` | qa → triage |
| `QA_RESULT` | qa → caller |
| `TRIAGE_RESULT` | triage → qa |
| `REVIEW_REQUEST` | any → reviewer |
| `REVIEW_RESULT` | reviewer → caller |
| `LSTM_REQUEST` | any → lstm |
| `LSTM_RESULT` | lstm → caller |

PR link is required on QA / triage envelopes.

## Jobs

One QA execute at a time. Overflow developer / reviewer / lstm →
general-purpose worker + worktree. Never spawn a graph as a child.

## Never

- `spawn_worker` with types `bulma_qa` / `bulma_developer` / …
- Two QA execute runs
- Two graphs “active” without a stack

## Related

All graphs. Protocol:
[PROTOCOL.md](../../skills/bulma-bus/PROTOCOL.md).
