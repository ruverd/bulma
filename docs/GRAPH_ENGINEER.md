# Graph engineer

A graph engineer writes **how the agent works**. Not the product.

The main thread of `/ruver-developer`, `/ruver-qa`, `/ruver-triage`,
`/ruver-reviewer`, `/ruver-lstm`, and `/ruver-goal`
**is** that role. It walks a GRAPH. It writes STATE. It does not
open `src/` and type the feature. `/memory` is a lib command, not a
graph.

Command pages: [commands/](commands/README.md).

## Three layers

| Layer | Where it lives | What it names |
|---|---|---|
| **Graph** | this repo (`skills/<name>/`, `GRAPH.md`) | nodes, edges, stop conditions, envelopes |
| **Host** | [ruver-host](../skills/ruver-host/SKILL.md) | how *this* harness spawns a child, wakes later, isolates a worktree |
| **Product** | target repo `AGENTS.md` / `CLAUDE.md` + [PRODUCT.md](../skills/ruver-feature-delivery/PRODUCT.md) + `ruver-memory` | test command, reviewers, tracker, design system, sibling repos, chat language |

A graph that says `spawn_subagent` or `model: grok-4.6` or
`reviewers: octocat` is no longer a graph. It is a host or a
product leaking in.

## What you ship

For each graph:

- `SKILL.md` — when to run, invariants, what the orchestrator never does
- `GRAPH.md` — nodes and edges
- `STATE.schema.md` + `templates/STATE.md`
- `nodes/*.md` — one file per node
- bus types, if it talks to another graph ([PROTOCOL.md](../skills/ruver-bus/PROTOCOL.md))

Worker contracts (`agents/ruver-fd-coder.md`, …) are **not** graphs.
They implement one ticket. The graph engineer writes the contract;
the worker runs it.

## Main thread

```
User slash / envelope
        │
        ▼
  Graph engineer (this session)
        │
        ├── load sibling skill by name
        ├── read/write $RUVER_ROOT (never the git root)
        ├── spawn ONE worker when the node says implement / test / review
        └── bus switch (envelope + stack) when the edge leaves this graph
```

Never spawn another **graph** as a child (`ruver_qa`, `ruver_developer`,
…). Load it on this thread after the bus write. See
[ruver-host](../skills/ruver-host/SKILL.md) for `load_graph` vs `spawn_worker`.

## Adding a graph

1. Folder under `skills/<name>/` with `category: graph` (`engine` for an engine, `lib` for a primitive).
2. Relative links only. Every skill is a sibling of every other, whatever the
   categories, so a cross-skill link is always `../<name>/FILE.md`
   (`../ruver-bus/JOBS.md`). No link may leave the skills root, and no
   `~/.claude`, `~/.grok`, `~/.codex`, `~/.agents`.
3. Need a child agent? Call it `spawn_worker` and point at `ruver-host`.
4. Need a later turn (CI)? Call it `schedule_wake` and point at `ruver-host`.
5. Product policy (who reviews, which test binary, which forge)
   comes from [PRODUCT.md](../skills/ruver-feature-delivery/PRODUCT.md),
   the **current repo**, and `ruver-memory`. Not from this plugin.
6. List the path in `plugin.json`.
7. Skill bodies stay in English. Chat follows `ruver-memory` (default
   English). Forge text stays English. Unslop always.

Then `ruver setup` (or `./install.sh setup`) and a commit. Slash names stay the skill folder
name (`/ruver-developer`) because the directory is already flat.

## Jev hooks

Graphs stay Jev-free. When a node has a fork worth a calibrated answer, add
a row to `skills/bulma/HOOKS.md` and an entry to
`skills/bulma/decisions.json` with the node's exact enum;
`tests/lib/check_bulma.py` fails when the two drift. The node file itself
does not change.

A hook that fires in a loop rather than once — per browser observation, per
finding — keeps its own script and reference page under `skills/bulma/`, never
in the target graph: `qa.browse` ships `scripts/browse.py` and `BROWSE.md`,
the two review hooks ship `VERDICT.md`. Build the state with a script when the
recipe is mechanical, and make that script the one thing that turns an answer
back into an action, so an answer can never become a selector or a command on
its own.
