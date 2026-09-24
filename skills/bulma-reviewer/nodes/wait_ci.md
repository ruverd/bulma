# Node: wait_ci

**Verb:** wait
**Capability:** scheduler, chat. No GitHub artifact.

Required CI is pending. Same process as
`../../bulma-code-review/LOOP.md`.

1. Write `status: waiting_ci` and `caller: bulma-reviewer` in
   `.bulma-code-review/STATE.md` (and copy `loop_id` into this graph's STATE).
2. Create or reuse the 5m loop. Do not post.
3. Chat WAITING. Stop the turn.

Loop wake with green → **code_review**.
Loop wake with red → **code_review** (the skill DEFERS).
