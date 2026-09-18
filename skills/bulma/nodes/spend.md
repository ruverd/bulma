# Node: spend

**Verb:** pick implementer model and effort
**Capability:** `session_catalog`, `session_model`, `session_effort`
([ruver-host](../../ruver-host/SKILL.md)); `scripts/bulma.py spend`;
`scripts/bulma.py ask`; optional `tracker_fetch_issue`

## Contract

1. Target is already on STATE. If args are a tracker id or tracker URL
   and `ticket_body` is empty, fetch via `tracker_fetch_issue` (fallback:
   title = args). Cap body 6000. A PR URL uses `world.json.pr` when
   present. Free text is `args`.
2. `session_catalog` → ids this session may switch to. Never invent
   one. Build `--criteria` `{session_model: {inherit: "…", <id>: "catalog id"}}`.
3. Flags from ARGS.md: `--effort` and `--session-model` win for that
   field. Both set → write STATE, apply, go to **overlay**. No Jev.
4. Else `python3 scripts/bulma.py spend --target <target>` → graph-answer
   for `effort`. `session_model` graph-answer is `inherit`.
5. State JSON per `entry.spend` in `../HOOKS.md`. Ask
   `python3 scripts/bulma.py ask entry.spend --state <file> --criteria <catalog> --graph-answer effort=<heuristic> --graph-answer session_model=inherit --json`.
6. Per field: flag → that value. `act: true` → Jev. Else graph-answer.
   `shadow` / `cautious`: list top options, one question, `waiting_user`,
   stop. Answer is an effort level, `ok` (take the suggestion),
   `inherit`, or a catalog id.
7. Write `effort`, `effort_source` (`flag` / `jev` / `heuristic` /
   `user`), `session_model` (`inherit` or a catalog id). Host
   `session_effort <effort>` then `session_model <id or inherit>`.
8. Chat: `Spend: effort=low .91 ok · session=cheap .88 ok` (VOICE).
   Under shadow: `Spend(shadow): effort=low (graph: high)`.

## Never

- Pin a host model id in this file or in GRAPH.md.
- Send the Jev id as `session_model`.
- Skip this node because the session is already "the good model".
- ASK because Jev was undecided (that is the heuristic).

## Output

`status: overlay | waiting_user`. Then **overlay**.
