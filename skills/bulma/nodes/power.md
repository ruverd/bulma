# Node: power

**Verb:** configure

| Args | Command |
|---|---|
| `power` | `python3 scripts/bulma.py power` |
| `power <level>` | `python3 scripts/bulma.py power set <level>` |
| `power <level> <hook>` | `python3 scripts/bulma.py power set <level> --hook <hook>` |
| `tune <hook.question> <act_at>` | `python3 scripts/bulma.py tune <hook.question> <act_at>` |
| `model` / `model <id>` | `python3 scripts/bulma.py model [set <id>]` |

Print the script output as-is, then one sentence in the chat language on
what changes (which hooks, which direction). No doctor, no key needed.
Stop.
