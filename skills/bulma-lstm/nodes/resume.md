# Node: resume

**Verb:** continue

Load `.bulma-lstm/STATE.md`. Reconcile `pr_url` / `sha` with `gh pr view`.
If `waiting_user`, the current message is the answer. Then jump to
`status` (verifying / patching / replying / rebasing). Do not re-ack
comment ids already in `processed_comment_ids`. Missing acks →
**reply**, even if the parent review id is listed.

For `status=qa_requested`, load [request_qa.md](request_qa.md). Reconcile the
parked request/queue or apply the matching `QA_RESULT`; never enqueue a duplicate
or re-run completed QA. A stale head needs fresh proof. `evidence_ready` is not
human approval, including after resume.

For `status=learning`, resume [learn.md](learn.md). Reconcile source keys and
issue markers before writing. New comments or a moved head return to verify;
old learning does not prove the new head. A completed run with new feedback
needs a fresh assessment even if earlier feedback was already recorded.
