# Run ledger

`$BULMA_ROOT/.bulma-bus/RUN_LOG.tsv`. Append-only. One row per transition.

This is **observation, not a gate.** Nothing reads it to decide whether to
continue, and no node stops because a number in here got large. It exists so a
bottleneck is a measurement instead of a hunch, and so a loop is visible after
the fact. The loop caps live in the graphs (`qa_fix_loops`, `ci_fix_loops`);
this file only records what happened.

## Columns

```text
ts_iso   epoch   graph   node   event   lap   sha   result   detail
```

| Column | Value |
|---|---|
| `ts_iso` | `date -u +%Y-%m-%dT%H:%M:%SZ`. For a human reading the file |
| `epoch` | `date -u +%s`. For arithmetic, so no reader has to parse a date |
| `graph` | `developer` · `qa` · `triage` · `reviewer` · `lstm` · `fd` · `goal` |
| `node` | node name as the GRAPH.md edge table spells it |
| `event` | `enter` · `exit` · `switch` · `claim` · `release` · `reclaim` |
| `lap` | how many times this `graph/node` has been entered in this run, from 1 |
| `sha` | head sha when known, else empty |
| `result` | the node's result on `exit`, else empty |
| `detail` | one short field, no tabs. Job id, verdict, reason |

Tab-separated, no quoting, no embedded tabs. A value that would need either is
too long for this file — put it in STATE and reference it.

## When to append

| Moment | Row |
|---|---|
| Orchestrator moves `status` into a node | `enter`, with the lap count |
| Node returns | `exit`, with its result |
| Bus switch ([PROTOCOL.md](PROTOCOL.md)) | `switch`, `detail` = `from>to type` |
| QA slot claimed ([JOBS.md](JOBS.md)) | `claim`, `detail` = job id |
| QA slot released | `release`, `detail` = job id |
| Expired or abandoned claim taken over | `reclaim`, `detail` = old id + reason |

Two lines per node is the whole cost. Write them as you go; do not batch them
at the end, because the run that most needs the record is the one that dies
before reaching an end.

## Reading it

```bash
bulma report
```

Wall time and lap count per `graph/node`, widest first, plus the age of the QA
claim. A row with more than one lap is where the run spent money twice.

## Tokens

Wall time and laps are what a graph can record truthfully about itself. Token
counts are not: a node cannot see its own usage, and a number it invents is
worse than no number. Do not estimate tokens into this file.

`bulma report` reads the host transcript when the installer knows the
path, and prints prompt / uncached / cache% by workspace class (`lstm`,
`fd`, `reviewer`, `other`). Uncached is billed input that missed the
prefix cache. Graphs still never write those numbers.
