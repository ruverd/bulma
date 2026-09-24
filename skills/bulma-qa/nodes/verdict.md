# Node: verdict

**Verb:** close

1. Map TRIAGE_RESULT via [../references/HANDOFF.md](../references/HANDOFF.md).
2. **Post the PR comment** with evidence attached (UI video
   and/or HTTP stills) —
   [../references/COMMENT.md](../references/COMMENT.md)
   (`../scripts/publish-evidence.sh`, never `gh gist create` on
   binaries). No comment → this node has not finished.
   Write `video_url` and `comment_url` into STATE.
3. Write `QA_RESULT` envelope. Pop stack.
4. Run caller `apply_qa` (if developer is on the stack) **before**
   starting another QA.
5. Clear `qa_active` and `qa_claimed_at`. Dequeue next
   (`bulma-bus/JOBS.md`).
6. If `.bulma-goal/STATE.md` has `loop_id` and COMPLETE.md is satisfied
   (or a head-SHA comment now exists), `scheduler_delete` that loop.

Never FAIL a suspected product bug without triage unless unambiguous.

This node is not the only exit. `blocked`, `handed_off` and `escalated`
release the lease too — `../../bulma-bus/JOBS.md`.
