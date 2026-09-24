# Commands

Every slash command the graph engineer runs. Skill ids stay `bulma-*`.
Short aliases (`/developer`, `/reviewer`, `/lstm`, `/qa`) are command
files.

Claude and Grok use commands below exactly as written. Codex reserves direct
`/name` entries for built-ins, so use `$bulma-developer` or `/skills`.

## Graphs (main thread)

These **are** the graph engineer. They walk a GRAPH. They do not
implement product code.

| Command | Short | When | Page |
|---|---|---|---|
| `/bulma-developer` | `/developer` | Ticket, goal, or PR_BUG fix | [bulma-developer](bulma-developer.md) |
| `/bulma-qa` | `/qa` | Exercise a PR (agent-browser or HTTP) | [bulma-qa](bulma-qa.md) |
| `/bulma-triage` | — | Classify a QA finding | [bulma-triage](bulma-triage.md) |
| `/bulma-reviewer` | `/reviewer` | Review a PR / diagnose CI | [bulma-reviewer](bulma-reviewer.md) |
| `/bulma-lstm` | `/lstm` | Incoming review comments | [bulma-lstm](bulma-lstm.md) |
| `/bulma-goal` | — | Keep going until QA evidence | [bulma-goal](bulma-goal.md) |
| `/bulma` | — | Pick the graph, gate its forks with Jev (needs `TYPESAFE_API_KEY`) | [bulma](bulma.md) |
| `/bulma-memory` | `/memory` | Durable prefs outside git | [memory](memory.md) |

## Protocol

Not a graph: no nodes, no edges. The graphs load it by name.

| Command | When | Page |
|---|---|---|
| `/bulma-bus` | Resume or inspect the stack | [bulma-bus](bulma-bus.md) |

## Engines

Called by a graph.

| Command | When | Page |
|---|---|---|
| `/bulma-feature-delivery` (`/bulma-fd`) | Grill → spec → tickets → TDD → draft PR | [bulma-feature-delivery](bulma-feature-delivery.md) |
| `/bulma-code-review` | One review artifact per PR | [bulma-code-review](bulma-code-review.md) |

How they connect: [../ARCHITECTURE.md](../ARCHITECTURE.md).
Role: [../GRAPH_ENGINEER.md](../GRAPH_ENGINEER.md).
Host mapping: [bulma-host](../../skills/bulma-host/SKILL.md).
