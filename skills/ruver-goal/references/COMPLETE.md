# Goal completion (falsifiable)

The goal is done only when **all** are true on the **current head SHA**:

1. Draft PR exists (`pr_url` in STATE).
2. `gh pr checks`: no required check pending/fail.
3. `mergeable` / `mergeStateStatus` is MERGEABLE (or CLEAN).
4. The PR has a comment whose body contains:

```text
<!-- ruver-qa: v=1 verdict=PASS|FAIL|BLOCKED sha=<headSha> -->
```

   `sha=` must equal `headRefOid`.
5. That same comment has evidence. UI: a `user-attachments` URL (the
   `--attach` video). API-only: an attached HTTP still of the changed
   endpoints, or FE stills of the callers. Local
   `test-results/*.webm` is not enough.

`FAIL` still completes **this** goal if the comment is on the head SHA
(QA ran). A `PR_BUG` reopens work: new SHA → loop continues until a
new comment matches the new SHA.

Verifier: `gh pr view --json headRefOid,url,mergeable,mergeStateStatus`
plus `gh api repos/$REPO/issues/$PR/comments` and grep the marker.
If that review cannot find the marker plus evidence (video URL or
HTTP still), the goal stays open.
