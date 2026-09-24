# Node: admit

**Verb:** gate  
**Capability:** read/write JOBS queue only

Follow `../../bulma-bus/JOBS.md` “Enqueue or start QA”.
Load `bulma-memory` (read both files). Chat follows that skill.

1. Init `.bulma-bus/JOBS.md` if missing.
2. `job_id` = envelope `job_id` or `qa-pr-<n>`.
3. Decide whether the slot is free — the four conditions in
   `../../bulma-bus/JOBS.md`. Empty and this-id are two of them. Expired and
   abandoned claims are the other two, and they are the common case once a
   session has died mid-QA.
4. Free → claim `qa_active` + `qa_claimed_at`, write `.bulma-qa/STATE.md`
   (`job_id`), then **resolve**. Took over a claim? Log it and say so in chat
   before resolving.
5. Held by **another live** id → append `qa_waiting`,
   park the envelope at `jobs/<id>/qa-request.md`.
   Do **not** change `.bulma-qa/STATE.md`.
   Do **not** start e2e, browser, HTTP QA, or plan.
   Chat (`bulma-memory`): queue + position. **Stop.**

Never two QA `execute` runs.
