# Adapter: Claude Code

Maps [bulma-host](../../bulma-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Claude Code |
|---|---|
| `load_skill` / `load_graph` | `/bulma-<name>` |
| `spawn_worker` | `Agent` / `Task` `general-purpose` (or `bulma-fd-*` when registered) |
| `worktree` | isolation if the Agent tool has it; else `git worktree add` |
| `schedule_wake` | `/loop` or the session scheduler; else ask the user to re-run |
| `cancel_wake` | stop that loop |
| `session_model` | inherit (`model:` in agent files is inherit) |

MCP on the **main thread** when a subagent cannot see MCP
([bulma-host](../../bulma-host/SKILL.md)).
Disk: `$HOME/.bulma/<slug>`.
