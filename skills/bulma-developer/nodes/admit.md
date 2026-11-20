# Node: admit

**Verb:** route  
**Capability:** write JOBS, maybe spawn worker

Follow `../../bulma-bus/JOBS.md`.
Load `bulma-memory` (read both files). Chat follows that skill.

1. Init `.bulma-bus/JOBS.md` if missing.
2. `job_id` = `dev-<ticket>` or `dev-pr-<n>`.
3. A single issue ID or URL goes through **deliver** for tracker discovery.
   An explicit stack request goes through the same discovery to resolve its
   tasks. A verified stack plan enters **stack** after discovery
   ([../STACKED.md](../STACKED.md)). If another
   graph owns main, retain the plan and resume it when the orchestrator can
   own the foreground and dispatch its children.
4. Idle main → `lane=foreground`, write
   `.bulma-developer/STATE.md` (`job_id`, `lane`), then
   **deliver** or **fix**.
5. Busy main → worktree + one `general-purpose` worker.
   Do not steal QA/triage/the other job. Stop this call.

Worker prompt: job id, worktree, ticket/PR, load
`bulma-developer` + `bulma-feature-delivery`, execute nodes
**inline** (no `bulma_*` / `bulma-fd-*` spawns), never merge,
write `jobs/<id>/RESULT.md`.
