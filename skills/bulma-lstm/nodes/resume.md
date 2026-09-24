# Node: resume

**Verb:** continue

Load `.bulma-lstm/STATE.md`. Reconcile `pr_url` / `sha` with `gh pr view`.
If `waiting_user`, the current message is the answer. Then jump to
`status` (verifying / patching / replying / rebasing). Do not re-ack
comment ids already in `processed_comment_ids`. Missing acks →
**reply**, even if the parent review id is listed.
