# Power

How much Jev gets to decide. One knob, four levels, per hook if you want.

```yaml
power: shadow | cautious | balanced | bold
```

| Level | Offset on `act_at` | Meaning |
|---|---|---|
| `shadow` | never acts | Asks and logs every answer; the graph decides alone. Use it to collect data before trusting a hook |
| `cautious` | +0.10 | Acts only on very confident answers. On `entry.*` it always suggests, never routes alone |
| `balanced` | 0 | Catalog defaults |
| `bold` | −0.10 | Acts on moderately confident answers |

Clamp to `[0.50, 0.99]`. The 0.50 floor is fixed: below it the model is
saying it does not know.

## Decision rule

- Choice: act when `confidence >= act_at'`.
- Noul: decisive-yes when `noul >= act_at'`; decisive-no when
  `noul <= 1 - act_at'`; otherwise undecided, which means the graph rule.
- `direction: ask` (only `policy.ask`): the offset sign flips, so `cautious`
  asks the user more and `bold` asks less.

## Where it lives

`$RUVER_HOME/bulma.json`, written by `scripts/bulma.py`, never by hand in a
graph, outside git, shared by every repo on the machine:

```json
{
  "power": "balanced",
  "power_by_hook": { "qa.gate": "shadow", "dispatch.tier": "shadow" },
  "act_at": { "fd.triage.path": 0.70 },
  "model": "jev-1.13.0",
  "tiers": { "claude": { "light": { "model": "haiku" } } }
}
```

`tiers` maps worker tiers to host spawn args (`bulma.py dispatch map`);
`model` is only the Jev model. Start `dispatch.tier` under `shadow`:
[DISPATCH.md](DISPATCH.md).

Precedence, highest first: `--power` flag > env `BULMA_POWER` >
`power_by_hook[hook]` > `power` > `balanced`. `act_at[hook.question]`
replaces the catalog value before the offset is applied.

Commands (all offline, no key needed):

```text
/bulma power                  # print level and where it came from
/bulma power cautious         # set the global level
/bulma power cautious dispatch.tier   # set one hook only
/bulma tune fd.triage.path 0.70
/bulma model jev-1.13.0       # pin once thresholds are tuned
/bulma report                 # calibration table
```

## Calibration loop

1. Run under `balanced` (or `shadow` for a hook you do not trust yet). Every
   `ask` logs the answer, the confidence, whether it acted, and the graph's
   own answer when the orchestrator passed `--graph-answer`.
2. After 20 or more decisions on a question, `/bulma report` prints
   `agree%` (Jev vs graph rule), `reversed` (outcomes marked wrong later),
   a `calls` line with input tokens and p50 latency per call,
   and `suggest`: the lowest threshold where at least 20 rows agree 95% or
   more. `need >=20` means keep collecting. `keep` means the current value
   already holds.
3. Apply with `/bulma tune <hook.question> <value>`. Raise when `reversed`
   grows; lower when `suggest` is below the current value and `reversed` is
   zero.
4. The default is pinned (`jev-1.13.0`), not `jev-latest`: an alias moving
   under you changes answers. When a new version ships, run it under
   `shadow` with `/bulma model <id>`, compare with `/bulma report` (it notes
   more than one model id), then keep it or go back.
5. Mark wrong calls when a later node proves them wrong
   (`bulma.py outcome <decision_id> <question> reversed`); the outcome hooks
   in [HOOKS.md](HOOKS.md) name the moments.
