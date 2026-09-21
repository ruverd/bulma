# Browse

How `qa.browse` drives agent-browser. One observation, one Jev request, one
command. The pattern is
[jev-ultrafast](https://github.com/browser-use/jev-ultrafast) (Browser Use ×
TypeSafe): a dynamic, indexed action space, with the operation and every
target answered in the same request. That project drives Chrome through its
own harness; here the executor is agent-browser, which already hands out
`@eN` refs, so the refs are the action space and no index has to be invented.

## Loop

```text
agent-browser snapshot -i --json      one browser call, atomic
  → scripts/browse.py state           element table + target heads
  → bulma.py ask qa.browse            one request: operation + 3 heads
  → scripts/browse.py resolve         keep the head the operation names
  → agent-browser <argv>              one command
  → snapshot again
```

Refs go stale the moment the page changes, so every cycle re-snapshots. That
is one browser call per cycle, not a call per element.

```bash
S=.ruver-bulma/state
agent-browser --session "$SESSION" snapshot -i --json >"$S/snap.json"
python3 scripts/browse.py state --snapshot "$S/snap.json" \
  --goal "$GOAL" --step "S3 user-break" --pass-if "$PASS_IF" \
  --url "$(agent-browser --session "$SESSION" get url)" \
  --history "$S/history.txt" \
  --out "$S/qa.browse-$TS.json" --criteria "$S/qa.browse-$TS.criteria.json"

python3 scripts/bulma.py ask qa.browse \
  --state "$S/qa.browse-$TS.json" --criteria "$S/qa.browse-$TS.criteria.json" \
  --context repo="$REPO" --context pr="$PR" --context sha="$SHA" --json >"$S/qa.browse-$TS.answer.json"

python3 scripts/browse.py resolve --snapshot "$S/snap.json" \
  --answer "$S/qa.browse-$TS.answer.json" --session "$SESSION" [--text "..."]
```

`resolve` prints `{ operation, ref, argv }`. Run `argv` as it is. Append the
executed line to `history.txt` so the next cycle knows what already happened.

## Speculative heads

`operation` and `click_target`, `type_text_target`, `select_target` are one
request. Only the head the operation names can execute; the other two were
speculation and are discarded. Two decisions, one round trip.

Each head offers only refs that operation can execute on — a `heading` is in
the element table as context but in no head, and a head with nothing
compatible offers `none` alone. `available` in the state says which
operations have a target at all, so the page's real action space reaches Jev
even though the operation criteria are a fixed list.

## Exit codes

| `browse.py` exit | Meaning |
|---|---|
| 0 | `argv` printed; run it |
| 4 | bad input: no refs in the snapshot, a ref that was never observed, an operation the target cannot take, `TYPE_TEXT` with no `--text` |
| 5 | no actionable decision: a question did not clear `act_at`, or the matching head is `none`. Read the snapshot and drive the step by hand |

Exit 5 is the ordinary fallback, not an error. Exit 4 means the answer and
the snapshot disagree; re-snapshot and ask again rather than guessing a
selector.

## Guards

- Jev picks an operation and a ref. It never writes a selector, a coordinate,
  a shell command or JavaScript. `resolve` maps the ref back to a node that
  snapshot observed, or refuses.
- `TYPE_TEXT` carries no string from Jev. The session model writes the value
  and passes it as `--text`.
- `DONE` ends the navigation loop and proves nothing. `pass_if`, the clips
  and `ruver-qa` VERDICTS.md decide the step, exactly as without Jev.
- `BLOCKED` stops the navigation, not the run. The QA `BLOCKED` verdict is
  still the graph's own call.
- `SELECT` targets an observed option and executes on the combobox that owns
  it. An option with no owner in the snapshot is exit 5.
- `WAIT` is one short settle, capped in the script. It is not a sleep loop.
- Caps: 60 elements, 120 characters per line. A page wider than that gets
  scrolled, not uncapped.

## Power

`qa.browse` is `stakes: low` and `act_at` 0.70 on all four questions: a wrong
click costs one re-snapshot, and no evidence gate depends on it. Run it under
`shadow` first if you want the ledger before the speed —
[POWER.md](POWER.md). Under `shadow` nothing executes from Jev and every
cycle is driven by hand, which is the same as running `/qa` without bulma.
