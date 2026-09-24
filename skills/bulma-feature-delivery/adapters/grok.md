# Adapter: Grok

Maps [bulma-host](../../bulma-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Grok |
|---|---|
| `load_skill` / `load_graph` | `/bulma-<name>` or `/skills bulma-<name>` |
| `spawn_worker` | `spawn_subagent` `subagent_type: general-purpose` `isolation: "worktree"` |
| fd workers | plugin agents `bulma-fd-coder` etc. if installed |
| `schedule_wake` | `scheduler_create` (same as `/loop`) |
| `cancel_wake` | `scheduler_delete` |
| `session_model` | inherit |

Disk: `$HOME/.bulma/<slug>`.
