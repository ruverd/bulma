# Reviewer STATE

**Path:** `.bulma-reviewer/STATE.md`

```
init | resolving | waiting_ci | reviewing | diagnosing | reporting | done
```

`review_verdict` · `failure_class` · `mergeable` · `ci` ·
`job_id` · `lane` · `worktree` · `worker_id` · `loop_id` · `worktree_cleanup`

`worktree_cleanup`: `removed` or a retention reason.

`loop_id` is copied from `.bulma-code-review/STATE.md` (one home).

`feedback_status`: pending / no_action / recorded.
`feedback_paths`: assessment or pending paths.
`feedback_tasks`: issue draft paths or confirmed issue URLs.
See [FEEDBACK.md](../bulma-bus/FEEDBACK.md).
