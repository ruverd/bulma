# Adapter: Cursor

Maps [ruver-host](../../ruver-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Cursor |
|---|---|
| `load_skill` / `load_graph` | `/ruver-<name>` |
| `spawn_worker` | `Task` general-purpose |
| `schedule_wake` | ask the user to re-run unless a loop command exists |
| `session_catalog` | Task `model` enum in **this** session when present |
| `session_model` | set Task `model` when the run named a catalog id. `inherit` omits it |
| `session_effort` | inherit; pass `effort:` on the worker prompt |

Installer copies this pack into the Cursor skill home.
Disk: `$HOME/.ruver/<slug>`.
