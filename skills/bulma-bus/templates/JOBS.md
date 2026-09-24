---
schema: 2
qa_active: ""
qa_claimed_at: ""
qa_waiting: ""
updated_at: ""
---

# Jobs

| id | kind | lane | status | linear | pr | worktree | worker_id |
|---|---|---|---|---|---|---|---|

`qa_waiting` = comma-separated job ids, FIFO.
`qa_active` = job id holding the single QA slot, or empty.
`qa_claimed_at` = ISO 8601 UTC instant that id claimed it. Empty when
`qa_active` is empty. Together they are a lease, not a lock — see
[../JOBS.md](../JOBS.md).
