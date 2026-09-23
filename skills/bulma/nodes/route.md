# Node: route

**Verb:** decide the target
**Capability:** run `scripts/bulma.py ask`

Deterministic first, Jev second. Never guess a graph.

## Steps

1. `../ARGS.md` already classified the args. Tracker id or tracker URL →
   `target: developer`, `target_args: <id or URL>`, no Jev call, write the
   Route block with `why: deterministic: ticket id`, go to **overlay**.
   Args that are only PR or MR refs → one `world.sh --pr` per ref, then read
   `pr.author_is_user`: `true` → `qa`, `false` → `reviewer`, no Jev call,
   `why: deterministic: pr author`. Several refs: one `reviewer` run with
   every non-own URL (ruver-code-review fans out), then one `qa` run with
   every own URL (ruver-qa queues extras). `pr` null (no `gh`) → step 2.
   Words that name the work ("roda QA", "review") override the author
   rule: step 2 decides.
2. PR or MR URL with other words, or free text →
   `python3 scripts/bulma.py ask entry.route --build --args "<args>" --context repo=<owner/repo> --context pr=<n> --json`.
   `--build` writes the `entry.route` state from `world.json` (recipe in
   `../HOOKS.md`) to `.ruver-bulma/state/`. Do not write it by hand.
3. Empty or `resume` →
   `python3 scripts/bulma.py ask entry.next_step --build --args "<args>" --json`
   (add `--resume` for `resume`: the builder keeps only `resume:*`
   candidates). The builder writes the dynamic criteria from
   `candidates.json`; do not pass `--criteria`.
4. Read the answer:
   - `user_blocked` decisive-yes → print each `states[].waiting_user`
     question first, in the chat language.
   - choice `none` → answer the user in chat; `status: done`.
   - power `shadow` or `cautious` → list the top three
     options from `probabilities` with their numbers, ask one question,
     `status: waiting_user`, end the turn.
   - `act: true` → `target` = the choice (for `entry.next_step`, the
     candidate's `target` and `args`). Write the Route block with
     `why: <decision_id> <confidence>`. Go to **overlay**.
   - remaining `act: false` → list the top three
     options from `probabilities` with their numbers, ask one question,
     `status: waiting_user`, end the turn.
5. Append the `decision_id` to STATE `decision_ids`. One `J:` line.

## Output

`target`, `target_args`, `status: overlay | waiting_user | done`.
