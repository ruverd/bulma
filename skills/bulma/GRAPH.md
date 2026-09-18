# Bulma graph

```
/bulma [args]
  → admit        doctor (hard gate) · power · catalog · init STATE
  → inventory    scripts/world.sh → .ruver-bulma/world.json + candidates.json
  → route        ARGS.md first; else ask entry.route | entry.next_step
        ├ local verb (power · tune · model · report · status · doctor) → run, stop
        ├ act      → spend (implementer model + effort)
        └ suggest  → one question, waiting_user, stop
  → spend        entry.spend; then overlay
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
| admit | ok | **inventory** |
| inventory | always | **route** |
| route | deterministic target (tracker id or tracker URL) | **spend** |
| route | `entry.route` = `none` | **stop** (answer in chat, no graph) |
| route | power is `shadow` or `cautious` on `entry.*` | **stop** (`waiting_user`, ranked candidates, one question) |
| route | Jev acted (`act: true`) | **spend** |
| route | Jev did not act (`act: false`) | **stop** (`waiting_user`, ranked candidates, one question) |
| spend | `--effort` and `--session-model` both set | **overlay** (no Jev) |
| spend | power is `shadow` or `cautious` on `entry.*` | **stop** (`waiting_user`, suggested effort and catalog id) |
| spend | otherwise | **overlay** (flag, Jev, or heuristic; host `session_effort` / `session_model`) |
| overlay | target graph terminal, `waiting_user`, `escalated`, `blocked`, or the turn ends | **done** |
| done | always | stop |
| any | user answers a `waiting_user` question via `/bulma <answer>` | **route** or **spend** (whichever asked) |

## Nodes

`nodes/admit.md` · `nodes/inventory.md` · `nodes/route.md` ·
`nodes/spend.md` · `nodes/overlay.md` · `nodes/done.md` ·
`nodes/power.md` · `nodes/report.md`

## Defaults

```yaml
power: balanced          # $RUVER_HOME/bulma.json overrides
model: jev-latest        # pin with `bulma.py model set <id>` once tuned
never_merge: true
enter_bus_stack: false
product_code_on_main: false
```
