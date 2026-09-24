# Bulma STATE

**Path:** `.bulma-core/STATE.md`

## status

```
init | inventory | routing | waiting_user | overlay | done | blocked
```

## Fields

| Field | Use |
|---|---|
| `power` | resolved level, from `bulma.py power` |
| `power_source` | flag \| env \| hook \| config \| default |
| `model` | model id sent on this run |
| `args` | raw args |
| `target` | developer \| qa \| reviewer \| lstm \| triage \| memory \| none |
| `target_args` | what the target graph receives |
| `world_path` | `.bulma-core/world.json` |
| `decision_ids` | comma list of decision ids this run |
| `hooks_fired` / `hooks_fallback` | counts, updated per hook |
| `waiting_user` | question text when stopped |
| `updated_at` | ISO |

Template: [templates/STATE.md](templates/STATE.md). Ledger of every Jev
answer: `.bulma-core/DECISIONS.tsv` (columns in `scripts/bulma.py`).
