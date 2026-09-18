# Bulma STATE

**Path:** `.ruver-bulma/STATE.md`

## status

```
init | inventory | routing | waiting_user | overlay | done | blocked
```

## Fields

| Field | Use |
|---|---|
| `power` | resolved level, from `bulma.py power` |
| `power_source` | flag \| env \| hook \| config \| default |
| `model` | Jev model id sent on this run |
| `effort` | implementer effort: `low` \| `medium` \| `high` \| `max` |
| `effort_source` | flag \| jev \| heuristic \| user |
| `session_model` | implementer catalog id, or `inherit` |
| `args` | raw args |
| `target` | developer \| qa \| reviewer \| lstm \| triage \| memory \| none |
| `target_args` | what the target graph receives |
| `world_path` | `.ruver-bulma/world.json` |
| `decision_ids` | comma list of decision ids this run |
| `hooks_fired` / `hooks_fallback` | counts, updated per hook |
| `waiting_user` | question text when stopped |
| `updated_at` | ISO |

Template: [templates/STATE.md](templates/STATE.md). Ledger of every Jev
answer: `.ruver-bulma/DECISIONS.tsv` (columns in `scripts/bulma.py`).
