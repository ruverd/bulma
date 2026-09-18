# Node: done

**Verb:** close

1. When the target graph reaches a terminal state, `waiting_user`,
   `escalated`, `blocked`, or the turn ends, write `status: done` (or copy
   `waiting_user` from the target) and `updated_at`.
2. Final chat block: `S:` target and its status, `J:` counts
   (`hooks_fired`, `hooks_fallback`, decisions logged), `P:` what the user
   does next (answer, wait for CI, nothing).
3. Do not run `report` here unless the user asked; point at `/bulma report`.
