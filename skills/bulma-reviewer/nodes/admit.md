# Node: admit

**Verb:** route  
**Capability:** write JOBS, maybe spawn worker

Follow `../../bulma-bus/JOBS.md`.
Load `bulma-memory` (read both files). Chat follows that skill.

1. Init `.bulma-bus/JOBS.md` if missing.
2. `job_id` = `rev-pr-<n>` (or `rev-<branch>`).
3. Idle main + **one** PR → `lane=foreground`, write
   `.bulma-reviewer/STATE.md`, then **resolve**.
4. Busy main, **or** 2+ PRs in this call → one worker +
   worktree **per PR**. Orchestrator does not review diffs.
   Each worker runs `bulma-code-review` for that PR only.
   No `bulma_reviewer` spawn. No browser QA.

Worker writes `jobs/<id>/RESULT.md`. Aggregate in chat.
