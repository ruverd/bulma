# `/bulma`

One entry point. Looks at the world, picks the graph, and while that graph
runs asks TypeSafe Jev at its forks. Skill: [`../../skills/bulma`](../../skills/bulma).

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
| ticket id or tracker URL | [developer](ruver-developer.md), no Jev call for routing |
| PR or MR URL, free text | Jev picks developer / qa / reviewer / lstm / triage / memory, or `none` |

While the chosen graph runs, ten hooks fire
([HOOKS.md](../../skills/bulma/HOOKS.md)): fd triage path and risk, ASK vs
DECIDE at grill forks, the QA unambiguous-FAIL gate, triage class per
finding, lstm claim and fix checks per comment, reviewer failure class, the
code-review high-risk critic, and the worker tier per coder spawn
([DISPATCH.md](../../skills/bulma/DISPATCH.md)). Jev picks among the node's own options;
edges, loop caps and verdicts stay in the graphs. The review verdict is
never a Jev call.

## Power

`shadow | cautious | balanced | bold`, global or per hook, per-question
thresholds, all in `~/.ruver/bulma.json`
([POWER.md](../../skills/bulma/POWER.md)). Every answer lands in
`DECISIONS.tsv`; `/bulma report` turns it into a calibration table.

## Never

- Merge, spawn a graph, enter the bus stack, write product code
- Skip a gate or invent an edge on a Jev answer
- Ask you because Jev was unsure (that means the graph's own rule)

## Related

[`/ruver-developer`](ruver-developer.md) · [`/ruver-qa`](ruver-qa.md) ·
[`/ruver-reviewer`](ruver-reviewer.md) · [`/ruver-lstm`](ruver-lstm.md) ·
[`/ruver-triage`](ruver-triage.md)
