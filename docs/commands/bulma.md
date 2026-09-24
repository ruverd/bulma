# `/bulma`

The one command most people need. It looks at your open work, picks the
stage to run, and asks TypeSafe Jev at the judgment calls while that stage
runs. New to Bulma? Start with [Getting started](../getting-started.md). Skill: [`../../skills/bulma`](../../skills/bulma).

```text
/bulma
/bulma DEV-4772
/bulma https://github.com/org/repo/pull/805
/bulma review the pagination PR
/bulma power cautious
/bulma report
```

## Needs

`python3` and `TYPESAFE_API_KEY` ([REQUIREMENTS.md](../../skills/bulma/REQUIREMENTS.md)).
Without the key `/bulma` prints the requirement and stops. Every other
command keeps working without Jev.

## What happens

| Args | Then |
|---|---|
| empty | `world.sh` lists open items (waiting graphs, PRs with review comments, red CI, PRs ready for QA). Jev ranks them. Above threshold it runs the pick; below, or on `cautious`, it asks you |
| ticket id or tracker URL | [developer](bulma-developer.md), no Jev call for routing |
| PR or MR URL, free text | Jev picks developer / qa / reviewer / lstm / triage / memory, or `none` |

Two hooks pick the target (`entry.route` and `entry.next_step`). Eight more
fire while the chosen graph runs ([HOOKS.md](../../skills/bulma/HOOKS.md)):
fd triage path and risk, ASK vs DECIDE at grill forks, the QA
unambiguous-FAIL gate, triage class per finding, lstm claim and fix checks
per comment, reviewer failure class, the code-review high-risk critic, and
the worker tier per coder spawn ([DISPATCH.md](../../skills/bulma/DISPATCH.md)).
`/bulma lookback --classify` uses one more, `insight.classify`, to group
review misses. Jev picks among the node's own options;
edges, loop caps and verdicts stay in the graphs. The review verdict is
never a Jev call.

## Power

`shadow | cautious | balanced | bold`, global or per hook, per-question
thresholds, all in `~/.bulma/bulma.json`
([POWER.md](../../skills/bulma/POWER.md)). Every answer lands in
`DECISIONS.tsv`; `/bulma report` turns it into a calibration table.

## Never

- Merge, spawn a graph, enter the bus stack, write product code
- Skip a gate or invent an edge on a Jev answer
- Ask you because Jev was unsure (that means the graph's own rule)

## Related

[`/bulma-developer`](bulma-developer.md) · [`/bulma-qa`](bulma-qa.md) ·
[`/bulma-reviewer`](bulma-reviewer.md) · [`/bulma-lstm`](bulma-lstm.md) ·
[`/bulma-triage`](bulma-triage.md)
