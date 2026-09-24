# Adapter: Codex

Maps [bulma-host](../../bulma-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Codex |
|---|---|
| `load_skill` / `load_graph` | `$bulma-<name>` or the skills menu |
| `spawn_worker` | child agent, general-purpose; worktree if the CLI exposes it |
| `schedule_wake` | host wakeup if present; else ask the user to re-run |
| `cancel_wake` | drop that wakeup |
| `session_model` | inherit |

Installer copies this pack into the Codex and agents skill homes.
Disk: `$HOME/.bulma/<slug>`.
