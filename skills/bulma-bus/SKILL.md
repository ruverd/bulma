---
name: bulma-bus
category: lib
description: >
  Shared bus for the bulma agent graphs (developer, qa, triage, reviewer, lstm).
  Use when switching graphs, writing or reading a .bulma-bus envelope, or
  resuming a stacked handoff between those agents.
argument-hint: "<resume | status>"
user-invocable: true
---

# Bulma bus

Five graphs, one session. They **do not nest**.

```
developer ⇄ qa ⇄ triage
     ⇄ reviewer
     ⇄ lstm
```

Communication = files under **`.bulma-bus/`** in the **global** home
([DISK.md](DISK.md)) — never the git root.
Protocol: [PROTOCOL.md](PROTOCOL.md). Jobs / QA queue: [JOBS.md](JOBS.md).

## Who orchestrates

The **main thread** is the only graph runner.

| Situation | Action |
|---|---|
| Main, outbound edge | Write envelope → push stack → **load** the target graph SKILL/GRAPH and continue |
| Already a subagent | Write envelope, return. Do **not** spawn a graph |
| Resume / `/bulma-bus` | Read `STACK.md` + latest envelope → load that graph |

**Never** `spawn_worker` with type `bulma_qa` / `bulma_triage` /
`bulma_developer` / `bulma_reviewer` / `bulma_lstm`. Those names are
graphs (main-thread roles). Overflow developer/reviewer/lstm work =
one general-purpose worker + worktree ([JOBS.md](JOBS.md),
[bulma-host](../bulma-host/SKILL.md)). Never a second QA worker.

## Resume

```text
/bulma-bus resume
```

1. Read `.bulma-bus/STACK.md` (**last line** = active graph).
2. Read `.bulma-bus/ENVELOPE.md`.
3. `load_graph` the last STACK line (`bulma-<name>` SKILL.md + GRAPH.md).
4. Continue from that graph's STATE. Do not restart.
5. Also print `JOBS.md`: `qa_active` with its `qa_claimed_at` age,
   `qa_waiting`, worker rows. Flag a claim past `qa_lease_minutes` — that
   is a crashed QA, not a busy one.

## Chat

Short, chat language (`bulma-memory`): `S: bus <from>→<to> <type>` ·
`P: active graph` · `qa_active` / queue.

Timing, laps, and host token totals: [LEDGER.md](LEDGER.md).
`bulma report` reads them. Human-review observations for lookbacks:
[INSIGHTS.md](INSIGHTS.md).
