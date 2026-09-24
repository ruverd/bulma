# QA STATE

**Path:** `.bulma-qa/STATE.md`

```
init | resolving | planning | executing | triage_requested | verdict | done | blocked
```

| Field | Use |
|---|---|
| `pr_url` | required |
| `repo` | `owner/repo` |
| `branch` | head |
| `sha` | tested oid |
| `linear` | ticket id or empty |
| `surface` | routes / endpoints / specs from the plan |
| `plan_path` | `.bulma-qa/PLAN.md` |
| `findings_path` | `.bulma-qa/FINDINGS.md` when any finding exists |
| `qa` | `PASS` / `FAIL` / `BLOCKED` / `PENDING_TRIAGE` |
| `triage_class` | after `TRIAGE_RESULT` |
| `video_url` | comment attachment (or empty if upload failed) |
| `comment_url` | PR comment after verdict |
| `job_id` | bus JOBS id (`qa-pr-N` / `dev-<ticket>`) |
