# Adapter: Claude Code

Maps [ruver-host](../../ruver-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Claude Code |
|---|---|
| `load_skill` / `load_graph` | `/ruver-<name>` |
| `spawn_worker` | `Agent` / `Task` `general-purpose` (or `ruver-fd-*` when registered) |
| `worktree` | isolation if the Agent tool has it; else `git worktree add` |
| `schedule_wake` | `/loop` or the session scheduler; else ask the user to re-run |
| `cancel_wake` | stop that loop |
| `session_catalog` | Agent / Task `model` enum in **this** session. Do not invent ids |
| `session_model` | set Agent / Task `model` when the run named a catalog id. `inherit` omits it (`model:` in agent files stays inherit) |
| `session_effort` | set the Agent / Task effort or thinking field when the host exposes one (`low` `medium` `high` `max` as the host spells them). Else inherit and pass `effort:` on the worker prompt |

MCP on the **main thread** when a subagent cannot see MCP
([ruver-host](../../ruver-host/SKILL.md)).
Disk: `$HOME/.ruver/<slug>`.
