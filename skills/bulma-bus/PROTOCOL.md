# Inter-graph protocol

**One home.** Developer / QA / triage / reviewer / lstm point here.
Do not restate the schema in those skills.

## Disk

Under `$BULMA_ROOT` ([DISK.md](DISK.md)). **Never** the git root.
Do not `git add` this tree.

```
.bulma-bus/
  STACK.md       # one graph name per line; last line = active
  ENVELOPE.md    # current message (overwrite per hop)
  log.md         # append-only one-liners
  RUN_LOG.tsv    # transitions, timing, laps — see LEDGER.md
  JOBS.md        # workers + single QA slot — see JOBS.md
  jobs/<id>/     # parked envelopes, worker STATE/RESULT
```

Concurrent tickets and the QA FIFO: [JOBS.md](JOBS.md).

## STACK

```text
developer
qa
triage
```

Last line is the running graph. Push on switch-to-callee. Pop when the
callee writes a `*_RESULT` and returns.

Allowed names: `developer` · `qa` · `triage` · `reviewer` · `lstm`

**Depth is capped at 3.** The deepest legitimate chain is
`developer → qa → triage`; nothing in the graphs needs a fourth frame. A push
that would make it four means an edge is pointing back into a graph already on
the stack, so the push is a cycle, not a call. Refuse it: leave the stack
alone, write a `*_RESULT` for the caller with the reason, and escalate. Do not
pop your way down to make room — that abandons a graph mid-run.

Before pushing, check `to` is not already on the stack. Same answer if it is:
that is the cycle, one frame earlier.

## Envelope types

| type | from → to | Meaning |
|---|---|---|
| `QA_REQUEST` | developer → qa | CI green + MERGEABLE; validate behavior |
| `TRIAGE_REQUEST` | qa → triage | Potential product error; PR link required |
| `PR_BUG_FIX` | (legacy) | Unused. PR_BUG fix enters via `QA_RESULT` FAIL |
| `REVIEW_REQUEST` | any → reviewer | Diagnose PR / CI / branch |
| `LSTM_REQUEST` | any → lstm | Incoming review / conflict on an existing PR |
| `LSTM_RESULT` | lstm → caller | Dispositions + patched + ack ids |
| `QA_RESULT` | qa → caller | `PASS` / `FAIL` / `BLOCKED` / `PENDING_TRIAGE` |
| `TRIAGE_RESULT` | triage → qa | `PR_BUG` / `EXISTING_BUG` / `NEW_BUG` / `NOT_A_BUG` / `BLOCKED` |
| `REVIEW_RESULT` | reviewer → caller | Review status + findings |

## Envelope fields (required marked)

```yaml
schema: 1
id: <iso-ish unique>
from: developer | qa | triage | reviewer | lstm   # required
to: developer | qa | triage | reviewer | lstm     # required
type: <above>                              # required
pr_url: https://github.com/.../pull/N      # required except REVIEW on a branch
pr_number:
repo:
branch:
sha:
tracker_id:
feature:
payload_path:   # extra file if the body would be huge
job_id:         # bus JOBS.md id when concurrent
created_at:
```

Body (markdown after frontmatter) carries repro / expected / actual /
evidence / ACs as the callee's skill already specifies
(`bulma-qa/references/HANDOFF.md`, `bulma-developer/references/QA_HANDOFF.md`).

**PR link is never omitted** on QA / triage / PR_BUG envelopes.

## Switch (main thread only)

```
0. Refuse if `to` is already on STACK.md, or the stack is already 3 deep
1. Write .bulma-bus/ENVELOPE.md
2. Append one line to log.md: ISO from→to type pr, and one `switch` row
   to RUN_LOG.tsv ([LEDGER.md](LEDGER.md))
3. Push `to` onto STACK.md
4. Stop acting as `from`
5. load_graph `<to>` (skill `bulma-<to>` SKILL.md + GRAPH.md). See
   [bulma-host](../bulma-host/SKILL.md).
6. That graph reads the envelope as input
```

On `*_RESULT`:

```
1. Write ENVELOPE.md (result)
2. Pop STACK
3. Load the new top graph
4. That graph applies the result (do not re-run finished nodes)
```

## Anti-patterns

- Spawn a graph as a subagent (`bulma_qa` / `_triage` / `_developer` /
  `_reviewer` / `_lstm`). Overflow work uses `general-purpose` workers (JOBS.md).
- Two QA `execute` runs (agent-browser) at once
- Two graphs “active” without a stack
- A fourth stack frame, or pushing a graph already on the stack
- Popping a live graph to make room for a push
- Copying this schema into five SKILL.md files
- Switching without `pr_url` on QA/triage
- Developer implementing product code on the main thread
  (fd / worker does that)
- Aborting QA because a new ticket arrived
