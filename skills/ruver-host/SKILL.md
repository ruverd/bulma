---
name: ruver-host
category: lib
description: >
  Host contract: maps the primitives graphs name (load_skill, spawn_worker,
  worktree, schedule_wake, session_model) onto this harness, with fallbacks for
  the optional MCP capabilities. Load when a node names a primitive or a new
  harness needs wiring.
---

# Host contract

Graphs name **primitives**. This file maps them onto the harness in
front of you. If a node mentions a primitive, do that mapping here.
Do not copy harness APIs into GRAPH.md.

In this repo, skills live under `skills/<name>/`.
After install they are siblings (`ruver-qa` next to `ruver-bus`
and `unslop`).
Resolve a skill **by name** via the host skill loader, or by the
relative path in git. Never hardcode `~/.agents/skills`, `~/.grok`,
`~/.claude`, or `~/.codex`.

## Primitives

| Primitive | Meaning | Fallback if the host has no API |
|---|---|---|
| `load_skill name` | Inject that skill's SKILL.md (and GRAPH.md if present) into **this** thread | Read the flattened sibling, or `skills/<name>/SKILL.md` in git |
| `load_graph name` | Same as `load_skill ruver-<name>`. Main thread only | Same |
| `spawn_worker` | One child session, **general-purpose**. Not a graph name | Tell the user the worker prompt; or run the node inline if isolation is impossible |
| `worktree` | Isolated checkout of the same branch | `git worktree add` (JOBS.md) |
| `schedule_wake` | Resume this graph later without blocking the turn | Ask the user to re-run the slash command when CI moves; do not `gh pr checks --watch` |
| `cancel_wake` | Drop that scheduled resume | No-op if none exists |
| `session_model` | Whatever the current session already uses | Do not pin `grok-*` / `sonnet` / `opus` in graph files |

## spawn_worker

Pass, and nothing else:

- job id
- worktree path (or “host worktree”)
- the **node file** as the contract
- the ticket, finding, or PR this node is for (full text, not “read STATE”)
- a file/path whitelist, plus 20–40 line excerpts if a snippet is required
- “do not spawn graph types”, never merge

The child loads the node and any skill **that node names**.

Do not pass GRAPH.md, the parent skill tree, the parent MCP/tool
catalog, `how` / `why`, or the session history. Isolation is a short
prompt, not a copy of this thread.

Prefer host isolation `worktree` when the spawn API has it. Then do
**not** also pass `cwd`.

| Host | Call |
|---|---|
| Grok | `spawn_subagent` `subagent_type: general-purpose` `isolation: "worktree"` |
| Claude Code | `Agent` / `Task` with `general-purpose` (or the fd agent name for implement/test/review) |
| Codex | child agent spawn; isolation if the CLI exposes a worktree |
| Cursor | `Task` general-purpose |

Never `spawn_worker` with types `ruver_developer` / `ruver_qa` /
`ruver_triage` / `ruver_reviewer` / `ruver_lstm`. Those are
`load_graph` on the main thread.

Fd **workers** (`ruver-fd-coder`, `ruver-fd-tester`, …) may be the
child type when the host registered them. If it did not, use
general-purpose and paste the node file into the prompt.

## schedule_wake

Used by `ruver-goal` and `ruver-code-review` wait_ci. Interval 5m.
One wake per PR. Store the host's id in STATE as `loop_id`.

| Host | Call |
|---|---|
| Grok | `scheduler_create` (same as `/loop`). Delete with `scheduler_delete` |
| Claude Code | `/loop` or the scheduler the session already uses. Else ask the user to re-run |
| Codex | host wakeup if present; else ask the user to re-run |
| Cursor | same fallback |

The wake prompt is in the skill's `LOOP.md`. It must `load_skill` by
**name**, not by an absolute home path.

## Optional MCP

Some nodes read better context when an MCP server happens to be installed. None
of them require it. A graph names the **capability**; this table maps it, and
every row degrades to the fallback rather than blocking.

| Capability | Tool when present | Fallback when absent |
|---|---|---|
| `tracker_fetch_issue` | Linear: `mcp__linear-server__get_issue` | The PR body and title alone. Never invent AC |
| `tracker_save_issue` | Linear: `mcp__linear-server__save_issue` | `gh issue create` / `glab issue create` ([BLOCKERS.md](../ruver-feature-delivery/BLOCKERS.md)) |
| `tracker_save_comment` | Linear: `mcp__linear-server__save_comment` | Comment on the PR instead |
| `code_graph_explore` | `mcp__codegraph__codegraph_explore` or TokenSave `tokensave_context` (search the tool list) | `Grep` the symbol name, same result cap |

When the git toplevel has `.codegraph/` or `.tokensave/`, this
capability is **required** for discovery. Query the graph before a
Grep/Read loop. Do not spawn an extra explorer worker. Grep/Read of
whole files is the fallback when the index is missing or the query
misses.

Tools may be **deferred**: absent from the initial function list until a tool
search selects them. Try the search before concluding a capability is missing.

A missing optional capability is never `mcp_gate: failed`. That flag means a
**detected, critical** source is unreachable, such as a ticket URL the goal
depends on. See
[MCP_CONTEXT.md](../ruver-feature-delivery/MCP_CONTEXT.md).

## Starting graphs

| Host | How the user starts a graph |
|---|---|
| Grok | `/developer` (command alias) or `/ruver-developer` (skill name) |
| Claude Code | `/developer` or `/ruver-developer` |
| Codex | `$ruver-developer` or select `ruver-developer` through `/skills` |
| Cursor | `/ruver-developer` |

Codex reserves slash input for built-in commands. Never tell a Codex user to
run `/ruver-*`; the parser rejects it before skill routing.

Short command aliases (Grok / Claude, via `commands/`): `/developer`,
`/reviewer`, `/lstm`, `/qa`, `/memory`. Same skill. Skill folder names
stay `ruver-*`. `/memory` is `ruver-memory` (lib), not a graph.

## Disk

`$RUVER_ROOT` is host-neutral. See [skills/ruver-bus/DISK.md](../ruver-bus/DISK.md).
Claude, Codex, Grok, and Cursor on one machine **share** that tree.

## Quality rubric

`ruver-fd-quality` loads bundled
`thermo-nuclear-code-quality-review` (`skills/thermo-nuclear-code-quality-review/`). Always run
`fix all`. Do not skip.

## Product policy

Reviewers, assignee, sibling repos, test command, tracker, design
system: [PRODUCT.md](../ruver-feature-delivery/PRODUCT.md)
plus the **current repo** (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`)
plus `ruver-memory` (confirmed reviewers, chat language).
Do not bake a company's GitHub handles or repo names into a graph node.
