# Commands

One page per command. Most people only need [`/bulma`](bulma.md). It picks
the right stage for you. Call a stage directly when you want to run one step
by itself, or when you have no TypeSafe API key.

Claude Code and Grok accept every command below as written, including the
short aliases (`/developer`, `/qa`, `/reviewer`, `/lstm`, `/goal`, `/memory`).
Cursor accepts the full `/bulma-*` names. Codex rejects custom `/` commands,
so type `$bulma-developer` or pick the skill from `/skills`.

Unfamiliar term? See the [glossary](../glossary.md).

## Graphs (main thread)

Each stage follows its own graph of steps on the chat thread. None of them
writes product code itself. Workers do.

| Command | Short | When | Page |
|---|---|---|---|
| `/bulma-developer` | `/developer` | Ticket, goal, or PR_BUG fix | [bulma-developer](bulma-developer.md) |
| `/bulma-qa` | `/qa` | Exercise a PR (agent-browser or HTTP) | [bulma-qa](bulma-qa.md) |
| `/bulma-triage` | — | Classify a QA finding | [bulma-triage](bulma-triage.md) |
| `/bulma-reviewer` | `/reviewer` | Review a PR / diagnose CI | [bulma-reviewer](bulma-reviewer.md) |
| `/bulma-lstm` | `/lstm` | Incoming review comments | [bulma-lstm](bulma-lstm.md) |
| `/bulma-goal` | — | Keep going until QA evidence | [bulma-goal](bulma-goal.md) |
| `/bulma` | — | Start here. Picks the stage and asks Jev at its judgment calls (needs `TYPESAFE_API_KEY`) | [bulma](bulma.md) |
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
