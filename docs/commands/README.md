# Commands

Every slash command the graph engineer runs. Skill ids stay `ruver-*`.
Short aliases (`/developer`, `/reviewer`, `/lstm`, `/qa`) are command
files.

Claude and Grok use commands below exactly as written. Codex reserves direct
`/name` entries for built-ins, so use `$ruver-developer` or `/skills`.

## Graphs (main thread)

These **are** the graph engineer. They walk a GRAPH. They do not
implement product code.

| Command | Short | When | Page |
|---|---|---|---|
| `/ruver-developer` | `/developer` | Ticket, goal, or PR_BUG fix | [ruver-developer](ruver-developer.md) |
| `/ruver-qa` | `/qa` | Exercise a PR (agent-browser or HTTP) | [ruver-qa](ruver-qa.md) |
| `/ruver-triage` | — | Classify a QA finding | [ruver-triage](ruver-triage.md) |
| `/ruver-reviewer` | `/reviewer` | Review a PR / diagnose CI | [ruver-reviewer](ruver-reviewer.md) |
| `/ruver-lstm` | `/lstm` | Incoming review comments | [ruver-lstm](ruver-lstm.md) |
| `/ruver-goal` | — | Keep going until QA evidence | [ruver-goal](ruver-goal.md) |
| `/bulma` | — | Pick the graph, gate its forks with Jev (needs `TYPESAFE_API_KEY`) | [bulma](bulma.md) |
| `/ruver-memory` | `/memory` | Durable prefs outside git | [memory](memory.md) |

## Protocol

Not a graph: no nodes, no edges. The graphs load it by name.

| Command | When | Page |
|---|---|---|
| `/ruver-bus` | Resume or inspect the stack | [ruver-bus](ruver-bus.md) |

## Engines

Called by a graph.

| Command | When | Page |
|---|---|---|
| `/ruver-feature-delivery` (`/ruver-fd`) | Grill → spec → tickets → TDD → draft PR | [ruver-feature-delivery](ruver-feature-delivery.md) |
| `/ruver-code-review` | One review artifact per PR | [ruver-code-review](ruver-code-review.md) |

How they connect: [../ARCHITECTURE.md](../ARCHITECTURE.md).
Role: [../GRAPH_ENGINEER.md](../GRAPH_ENGINEER.md).
Host mapping: [ruver-host](../../skills/ruver-host/SKILL.md).
