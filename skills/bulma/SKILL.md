---
name: bulma
category: graph
description: Jev-gated router and overlay for ruver graphs. Use when /bulma.
argument-hint: "<empty | ticket | PR url | text | power <level> | report | watch | lookback | resume>"
---

# Bulma (graph)

Orchestrator. You do not implement product code. You never merge.

Bulma decides **which** ruver graph runs now, loads it on this thread, and
stays loaded while it runs. At each fork listed in [HOOKS.md](HOOKS.md) it asks
TypeSafe Jev a typed question and acts on the answer when confidence clears a
threshold the user controls ([POWER.md](POWER.md)). Code owns the edges; Jev
only picks among options the node already has.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [ARGS.md](ARGS.md) ·
[STATE.schema.md](STATE.schema.md) · [HOOKS.md](HOOKS.md) ·
[POWER.md](POWER.md) · [DISPATCH.md](DISPATCH.md) ·
[REQUIREMENTS.md](REQUIREMENTS.md) ·
[ruver-host](../ruver-host/SKILL.md) · [DISK.md](../ruver-bus/DISK.md)
(`.ruver-*` is **global**, never the git root) · `ruver-memory`

Chat: `ruver-memory`. Unslop always. Scripts live in `scripts/` next to this
file; the host tells you where the skill directory is. Run them with
`python3` and `bash`.

## Requirement

Every other graph works without Jev. This one does not. `admit` runs
`scripts/bulma.py doctor`; exit 2 or 3 means print the message it returns in
the chat language, write `status: blocked`, and stop. Nothing else runs.
Details: [REQUIREMENTS.md](REQUIREMENTS.md).

## Start

1. Load `ruver-memory`. Resolve `$RUVER_ROOT`. Init `.ruver-bulma/STATE.md`
   from [templates/STATE.md](templates/STATE.md) unless one is live.
2. Parse args with [ARGS.md](ARGS.md) **before** any Jev call. Local verbs
   (`power`, `tune`, `model`, `report`, `status`, `doctor`, `watch`,
   `lookback`) run and stop.
3. Walk [GRAPH.md](GRAPH.md): **admit → inventory → route → overlay → done**.

## Routing

Deterministic first: a tracker id or tracker URL goes to `developer` with no
Jev call. Bare PR or MR refs go by author with no Jev call: the user's own PR
goes to `qa`, anyone else's to `reviewer`. A PR ref with other words, or free
text, goes through `entry.route`. Empty args or `resume` go through `entry.next_step` over the
candidates `scripts/world.sh` found. Below threshold, or under `shadow` and
`cautious`, bulma suggests and waits; it never guesses a graph.

## Overlay

After `load_graph <target>` follow that graph exactly. When it (or an engine
it loads) reaches a node in HOOKS.md, ask first, then write the field:
`act: true` means Jev's value, `act: false` means the graph's own rule.
Bus switches inside the target keep the overlay. Bulma never appears on
`STACK.md`. Jev down mid-run means fallback and continue; only `admit`
stops. Contract: [nodes/overlay.md](nodes/overlay.md).

Workers: the overlay also picks the tier each coder worker runs on
(`dispatch.tier`), escalates it on a fail, and never lowers a gate.
[DISPATCH.md](DISPATCH.md).

## Watch

`/bulma watch` checks every workspace under `$RUVER_HOME`, not just this repo,
and lists stalled work, work that needs the user, and orphaned work, each with
its next command. It reconciles against GitHub first, so a PR that already
merged is not reported as stuck. Report only, no key.
[nodes/watch.md](nodes/watch.md).

## Lookback

`/bulma lookback` counts what human reviewers caught and the graphs missed, by
cluster, per reviewed PR, against the previous window of the same length. Each
cluster names the skill section meant to stop it, so a cluster that does not
shrink after that section changed shows the change failed. It proposes skill
edits and opens a draft PR only after the user says yes. No key.
[nodes/lookback.md](nodes/lookback.md).

## Power

`shadow | cautious | balanced | bold`, global or per hook, plus a per-question
`act_at` override, all in `$RUVER_HOME/bulma.json`. `/bulma power <level>`,
`/bulma tune <hook.question> <act_at>`, `/bulma report`. Math and the
calibration loop: [POWER.md](POWER.md).

## Chat shape

```text
S: bulma route -> developer (DEV-4772)
J: target=developer (deterministic: ticket id)
P: developer admit
```

One `J:` line per hook while the overlay runs, for example
`J: path=debug_fix .88 ok · risk=elevated .61 -> ROUTING`.

## Never

- Enter the bus stack, spawn a graph, merge, or write product code.
- Skip a gate or invent an edge because Jev said so.
- ASK the user because Jev was undecided. Undecided means the graph rule.
  The only hook that can produce ASK is `policy.ask`, inside
  `../ruver-feature-delivery/DECISION_POLICY.md`.
- Send full files to Jev. Caps are in HOOKS.md.
- Run any hook before `doctor` passed in this run.
- Write outside `$RUVER_ROOT/.ruver-bulma/`, `$RUVER_HOME/bulma.json`, and
  `$RUVER_HOME/bulma-watch.json`.
- Print `TYPESAFE_API_KEY`.
