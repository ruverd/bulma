# Adapter: Codex

Maps [ruver-host](../../ruver-host/SKILL.md) primitives. Graphs stay generic.

| Primitive | Codex |
|---|---|
| `load_skill` / `load_graph` | `$ruver-<name>` or the skills menu |
| `spawn_worker` | child agent, general-purpose; worktree if the CLI exposes it |
| `schedule_wake` | host wakeup if present; else ask the user to re-run |
| `cancel_wake` | drop that wakeup |
| `session_catalog` | empty unless this session lists a model enum |
| `session_model` | inherit unless the spawn API takes a catalog id the run named |
| `session_effort` | inherit; pass `effort:` on the worker prompt |

Installer copies this pack into the Codex and agents skill homes.
Disk: `$HOME/.ruver/<slug>`.
