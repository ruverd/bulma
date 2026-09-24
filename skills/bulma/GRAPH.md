# Bulma graph

```
/bulma [args]
  → admit        doctor (hard gate) · power · catalog · init STATE
  → inventory    scripts/world.sh → .ruver-bulma/world.json + candidates.json
  → route        ARGS.md first; else ask entry.route | entry.next_step
        ├ local verb (power · tune · model · report · status · doctor · watch · lookback) → run, stop
        ├ act      → overlay (load_graph target on the main thread)
        └ suggest  → one question, waiting_user, stop
  → overlay      target graph runs; at each HOOKS.md row: ask → apply → J:
  → done         target terminal or stopped → decisions rollup
```

## Edges

| From | Condition | To |
|---|---|---|
| start | always | **admit** |
| admit | doctor exit 2 or 3 | **stop** (requirement message, `status: blocked`) |
| admit | args are `power`, `tune`, `model` | **power** (no doctor needed), then stop |
| admit | args are `report`, `status`, `doctor` | **report** (no doctor needed), then stop |
| admit | args are `watch` | **watch** (no doctor needed), then stop |
| admit | args are `lookback` | **lookback** (no doctor needed), then stop |
| admit | ok | **inventory** |
| inventory | always | **route** |
| route | deterministic target (tracker id or tracker URL; bare PR refs by author) | **overlay** |
| route | `entry.route` = `none` | **stop** (answer in chat, no graph) |
| route | power is `shadow` or `cautious` on `entry.*` | **stop** (`waiting_user`, ranked candidates, one question) |
| route | Jev acted (`act: true`) | **overlay** |
| route | Jev did not act (`act: false`) | **stop** (`waiting_user`, ranked candidates, one question) |
| overlay | target graph terminal, `waiting_user`, `escalated`, `blocked`, or the turn ends | **done** |
| done | always | stop |
| any | user answers a `waiting_user` question via `/bulma <answer>` | **route** (the answer is the pick) |

## Nodes

`nodes/admit.md` · `nodes/inventory.md` · `nodes/route.md` ·
`nodes/overlay.md` · `nodes/done.md` · `nodes/power.md` · `nodes/report.md` · `nodes/watch.md` ·
`nodes/lookback.md`

## Defaults

```yaml
power: balanced          # $RUVER_HOME/bulma.json overrides
model: jev-1.13.0        # pinned; migrate with `bulma.py model set <id>`
never_merge: true
enter_bus_stack: false
product_code_on_main: false
```
