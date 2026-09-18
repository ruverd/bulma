# Adapter: Grok

Maps [ruver-host](../../ruver-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Grok |
|---|---|
| `load_skill` / `load_graph` | `/ruver-<name>` or `/skills ruver-<name>` |
| `spawn_worker` | `spawn_subagent` `subagent_type: general-purpose` `isolation: "worktree"` |
| fd workers | plugin agents `ruver-fd-coder` etc. if installed |
| `schedule_wake` | `scheduler_create` (same as `/loop`) |
| `cancel_wake` | `scheduler_delete` |
| `session_catalog` | `spawn_subagent` `model` enum in **this** session. Do not invent ids |
| `session_model` | pass `spawn_subagent` `model` when the run named a catalog id. `inherit` omits it |
| `session_effort` | map `max` → `xhigh`; `low` `medium` `high` keep those names. No agent tool: print `/effort <mapped>` and pass `effort:` on the worker prompt |

Disk: `$HOME/.ruver/<slug>` (install.sh may symlink from `~/.grok/ruver`).
