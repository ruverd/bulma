# Node: route

**Verb:** decide the target
**Capability:** run `scripts/bulma.py ask`

Deterministic first, Jev second. Never guess a graph.

## Steps

1. `../ARGS.md` already classified the args. Tracker id or tracker URL →
   `target: developer`, `target_args: <id or URL>`, no Jev call, write the
   Route block with `why: deterministic: ticket id`, go to **overlay**.
2. PR or MR URL, `owner/repo#N`, or free text → state JSON
   `{args, world, pr, user_login}` per the `entry.route` recipe in
   `../HOOKS.md` (trim `world` to `stack_top`, `jobs`, `states[]` with graph,
   status, waiting_user). Write it to
   `.ruver-bulma/state/entry.route-<UTC ts>.json`. Run
   `python3 scripts/bulma.py ask entry.route --state <file> --context repo=<owner/repo> pr=<n> --json`.
3. Empty or `resume` → state `{args, candidates, world}` and
   `python3 scripts/bulma.py ask entry.next_step --state <file> --criteria .ruver-bulma/candidates.json --json`.
   For `resume`, first drop every non-`resume:*` id from a copy of
   `candidates.json` and pass that copy.
4. Read the answer:
   - `user_blocked` decisive-yes → print each `states[].waiting_user`
     question first, in the chat language.
   - `act: true` → `target` = the choice (for `entry.next_step`, the
     candidate's `target` and `args`). Write the Route block with
     `why: <decision_id> <confidence>`. Go to **overlay**.
   - choice `none` → answer the user in chat; `status: done`.
   - `act: false`, or power `shadow` or `cautious` → list the top three
     options from `probabilities` with their numbers, ask one question,
     `status: waiting_user`, end the turn.
5. Append the `decision_id` to STATE `decision_ids`. One `J:` line.

## Output

`target`, `target_args`, `status: overlay | waiting_user | done`.
