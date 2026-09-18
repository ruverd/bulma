# Spend

Which **implementer** model and reasoning effort this run should use.
Not the Jev id (`model` in `bulma.json`). Jev reads the ticket and
picks among the **current host catalog**.

Levels (host-neutral): `low | medium | high | max`. Mapping onto a
harness lives in [ruver-host](../ruver-host/SKILL.md).

## When

After **route** has a `target`, before **overlay**. Local verbs skip
it. `--effort` and `--session-model` skip the matching question; both
together skip the hook.

## Heuristic (graph-answer)

`python3 scripts/bulma.py spend --target <target>`:

| target | effort |
|---|---|
| memory, none | low |
| qa, reviewer, triage, lstm | medium |
| developer or unknown | high |

`session_model` graph-answer is always `inherit`.

## Jev

`entry.spend` sees `ticket_title`, `ticket_body` (cap 6000),
`acceptance_criteria`, `args`, `target`. `session_model` criteria are
**this session's catalog** plus `inherit`. Never invent an id. Empty
catalog → only `inherit`.

Cheapest catalog id that can still do the ticket. `low` for copy,
rename, docs. `max` only when the ticket needs long reasoning (auth,
money, tenant, public contract, unclear design, wide fullstack).

Flags beat Jev. Undecided Jev → heuristic / `inherit`. `entry.*` under
`shadow` or `cautious` never acts: suggest, `waiting_user`.

## Apply

Write STATE `effort`, `effort_source`, `session_model`. Then host
`session_effort` and `session_model`. `spawn_worker` gets the same
pair: omit `model` when `inherit`.
