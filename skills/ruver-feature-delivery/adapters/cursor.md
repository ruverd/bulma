# Adapter: Cursor

Maps [ruver-host](../../ruver-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Cursor |
|---|---|
| `load_skill` / `load_graph` | `/ruver-<name>` |
| `spawn_worker` | `Task` general-purpose |
| `schedule_wake` | ask the user to re-run unless a loop command exists |
| `session_model` | inherit |

Installer copies this pack into the Cursor skill home.
Disk: `$HOME/.ruver/<slug>`.
