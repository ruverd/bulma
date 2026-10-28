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

`$BULMA_HOME/bulma.json`, written by `scripts/bulma.py`, never by hand in a
graph, outside git, shared by every repo on the machine:

```json
{
  "power": "balanced",
  "power_by_hook": { "qa.gate": "shadow", "dispatch.tier": "shadow" },
  "act_at": { "fd.triage.path": 0.70 },
  "model": "jev-1.14.0",
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
/bulma model jev-1.14.0       # pin once thresholds are tuned
/bulma report                 # calibration table
```

## Calibration loop

1. Run new hooks or models under `shadow`. Each answer records its model,
   policy fingerprint, question type, source (`live` or `replay`), probability,
   effective threshold and whether it acted. Older ledgers remain readable in
   separate `legacy` cohorts. The fingerprint includes the runner, catalog,
   cache implementation and resolved question criteria.
2. Mark decisions `confirmed` or `reversed` only after independent evidence
   settles the answer: tests, QA, or a human-reviewed label. No outcome means
   unknown, not correct. Graph agreement is a diagnostic, not a label.
3. `bulma.py report` separates model, policy, source and power. It shows
   confirmed, reversed and unlabeled counts, automatic coverage (`acted%`),
   and p95 latency. Cache hits do not contribute to calibration. Replay rows
   never suggest thresholds. Legacy provenance is unknown.
4. `suggest effective` needs at least 20 outcome-labeled decisions above a
   candidate threshold and at least 95% confirmed outcomes. Both Noul tails
   count: `p=0.1` predicts no with certainty `0.9`; `p=0.9` predicts yes with
   certainty `0.9`. Noul graph answers normalize `true/false` to `yes/no`.
   Choice and Score retain API confidence. These numbers are different
   measures and must not be pooled across question types.
5. Validate proposed cuts on a held-out set, including uncertain and wrong
   predictions. Twenty labels are a minimum sample, not proof of 95% accuracy.
   `no supported threshold` means no tested cut met the rule. For `balanced`,
   apply with `bulma.py tune <hook.question> <value>`. For other power levels,
   undo the offset in the table above before tuning, including the reversed
   offset on `policy.ask`.

## Compare model releases

The default is pinned to `jev-1.14.0`. Existing explicit model settings still
win. This release changes the default model; the old thresholds have not been
validated against 1.14. Use shadow comparison before trusting a new model or
lowering thresholds. Do not use `jev-latest` for a calibrated workflow.

Prepare a batch of representative, complete states with `graph_answer` values
from independently reviewed labels. Keep a separate held-out batch. Use the
same batches for each version; no config edit is needed:

```sh
python3 scripts/bulma.py ask-many --batch labeled.json --model jev-1.13.0 --power shadow --json
python3 scripts/bulma.py ask-many --batch labeled.json --model jev-1.14.0 --power shadow --json
python3 scripts/bulma.py report --model jev-1.13.0 --source live
python3 scripts/bulma.py report --model jev-1.14.0 --source live
```

For each returned `decision_id` and question, mark `confirmed` when it matches
its reviewed label and `reversed` otherwise. Preserve the model's original
answer; `graph_answer` alone does not qualify a row for threshold suggestions:

```sh
python3 scripts/bulma.py outcome <decision_id> <question> confirmed
```

Compare labeled errors, coverage, input tokens and p95 latency per question,
including Portuguese requests and option-order variants. Measure coverage in
shadow from the returned certainty versus effective threshold, since `acted%`
is deliberately zero there. Promote only after the held-out comparison, then
pin the chosen version with `bulma.py model set <id>`. Images, Box and long
context remain disabled; they are unrelated to this text-only migration.

## Request and retry budgets

`entry.*` requests default to 3 seconds; other hooks default to 8 seconds.
One monotonic budget covers all attempts and backoff. Each network attempt
uses only the remaining budget; a Retry-After that would exhaust it triggers
fallback immediately. Late responses never authorize a decision. This is a
request/retry budget, not a hard real-time guarantee: OS DNS resolution and
socket reads can finish after their requested timeout.

```sh
python3 scripts/bulma.py timeout 8
python3 scripts/bulma.py timeout 3 --hook entry.route
python3 scripts/bulma.py timeout --hook entry.route
```

These commands write `timeout_seconds` and `timeout_by_hook` in the shared
settings file. Invalid or incomplete API answers fall back per question and
never enter the cache. Missing required state keys fail before any batch item
is sent. Truncated states fall back without sending a request. The runner
filters out top-level fields outside the hook's recipe; keep relevant evidence
within the recipe caps rather than increasing context size.
